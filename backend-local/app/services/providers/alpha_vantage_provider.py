from typing import List, Dict
import requests
from datetime import datetime, timedelta
from ...services.base_provider import ExchangeDataProvider
from ...services.exchange_data_service import ExchangeDataService
import logging
import os

logger = logging.getLogger(__name__)

class AlphaVantageProvider(ExchangeDataProvider):
    """Alpha Vantage implementation of exchange data provider"""
    
    def __init__(self):
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY', '')
        self._exchange_cache = {}
        self._cache_timestamp = None
        self._cache_duration = timedelta(hours=24)
        self.exchange_service = ExchangeDataService()
        
    def get_all_exchanges(self) -> List[Dict]:
        """Get all available exchanges"""
        try:
            # Get exchanges from our local data
            exchanges = self.exchange_service.get_all_exchanges()
            
            # Convert to list and sort
            exchange_list = [
                {
                    'code': ex.code,
                    'name': ex.name,
                    'country': ex.country
                }
                for ex in exchanges
            ]
            exchange_list.sort(key=lambda x: (x['country'], x['name']))
            
            return exchange_list
            
        except Exception as e:
            logger.error(f"Error getting exchanges: {str(e)}")
            return []

    def get_exchange(self, code: str) -> Dict:
        """Get a specific exchange by its code"""
        exchange = self.exchange_service.get_exchange(code)
        if exchange:
            return {
                'code': exchange.code,
                'name': exchange.name,
                'country': exchange.country
            }
        return {}

    def search_exchanges(self, query: str) -> List[Dict]:
        """Search exchanges by name or code"""
        query = query.upper()
        exchanges = self.exchange_service.get_all_exchanges()
        return [
            {
                'code': ex.code,
                'name': ex.name,
                'country': ex.country
            }
            for ex in exchanges
            if query in ex.code.upper() or 
               query in ex.name.upper() or
               query in ex.country.upper()
        ]

    def search_symbols(self, query: str, exchange: str = None, search_type: str = 'symbol') -> List[Dict]:
        """Search for symbols that match the query, optionally filtering by exchange"""
        if not self.api_key:
            logger.error("Alpha Vantage API key not configured")
            raise ValueError("Alpha Vantage API key not configured. Please set the ALPHA_VANTAGE_API_KEY environment variable.")

        try:
            # Use Alpha Vantage's symbol search endpoint
            url = "https://www.alphavantage.co/query"
            params = {
                'function': 'SYMBOL_SEARCH',
                'keywords': query,
                'apikey': self.api_key
            }
            
            logger.debug(f"Looking up {search_type} with query: {query}")
            response = requests.get(url, params=params)
            
            if not response.ok:
                logger.error(f"Alpha Vantage API error: {response.status_code} - {response.text}")
                return []
                
            try:
                data = response.json()
                logger.debug(f"Alpha Vantage API response: {data}")
            except ValueError as e:
                logger.error(f"Failed to parse Alpha Vantage API response: {response.text}")
                return []
            
            results = []
            seen_symbols = set()
            
            # Process each match from the search results
            for match in data.get('bestMatches', []):
                try:
                    symbol = match.get('1. symbol')
                    company_name = match.get('2. name', '')
                    
                    # Skip if we don't have the required data
                    if not symbol or not company_name:
                        continue
                    
                    # Skip if we've seen this symbol already
                    if symbol in seen_symbols:
                        continue
                    
                    # Apply search type filter
                    search_query = query.upper()
                    if search_type == 'symbol' and search_query not in symbol.upper():
                        continue
                    elif search_type == 'company' and search_query not in company_name.upper():
                        continue
                        
                    logger.debug(f"Processing symbol: {symbol}")
                    
                    # Get exchange info from our local data
                    exchange_code = match.get('4. region', '')  # Alpha Vantage uses 'region' for exchange
                    exchange_info = self.get_exchange(exchange_code)
                        
                    # Add appropriate suffix based on exchange
                    suffix = ""
                    if exchange_info:
                        # Check if symbol already has a suffix
                        has_suffix = any(x in symbol for x in ['.AX', '.XA', '.NAS', '.NYS', '.PK', '.EX', '.QX', '.QB', '.OB'])
                        
                        if not has_suffix:
                            if exchange_info['code'] in ['ASX', 'CXA']:
                                # Both ASX and CHESS Depositary Interests use .AX suffix
                                suffix = ".AX"
                            elif "NASDAQ" in exchange_info['name'].upper():
                                suffix = ".NAS"
                            elif "NYSE" in exchange_info['name'].upper():
                                suffix = ".NYS"
                            elif "OTC PINK" in exchange_info['name'].upper():
                                suffix = ".PK"
                            elif "OTC EXPERT" in exchange_info['name'].upper():
                                suffix = ".EX"
                            elif "OTCQX" in exchange_info['name'].upper():
                                suffix = ".QX"
                            elif "OTCQB" in exchange_info['name'].upper():
                                suffix = ".QB"
                            elif "BULLETIN BOARD" in exchange_info['name'].upper():
                                suffix = ".OB"
                    
                    # Format the result
                    result = {
                        'symbol': symbol,
                        'description': company_name,
                        'displaySymbol': symbol,
                        'exchange': exchange_info['name'] if exchange_info else exchange_code,
                        'type': match.get('3. type', ''),
                        'result': f"{symbol}{suffix}"
                    }
                    
                    # If a specific exchange was requested, only include matches for that exchange
                    if exchange and exchange.strip():
                        if exchange_info and exchange_info['code'] == exchange:
                            results.append(result)
                            seen_symbols.add(symbol)
                    else:
                        results.append(result)
                        seen_symbols.add(symbol)
                        
                except Exception as e:
                    logger.error(f"Error processing symbol {match.get('1. symbol')}: {str(e)}")
                    continue
            
            logger.debug(f"Found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return [] 