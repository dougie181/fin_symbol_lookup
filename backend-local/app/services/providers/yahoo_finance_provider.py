from typing import List, Dict, Optional
import yfinance as yf
import requests
from datetime import datetime, timedelta
from ...services.base_provider import ExchangeDataProvider
from ...services.exchange_data_service import ExchangeDataService
import logging
import json
import os

logger = logging.getLogger(__name__)

class YahooFinanceProvider(ExchangeDataProvider):
    """Yahoo Finance implementation of exchange data provider"""
    
    def __init__(self):
        self._exchange_cache = {}
        self._cache_timestamp = None
        self._cache_duration = timedelta(hours=24)
        self._cache_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'yahoo_exchanges_cache.json')
        self.exchange_service = ExchangeDataService()
        self._load_cache()
        
    def _load_cache(self):
        """Load cached exchanges from file"""
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'r') as f:
                    cache_data = json.load(f)
                    self._exchange_cache = cache_data.get('exchanges', {})
                    cache_time = cache_data.get('timestamp')
                    if cache_time:
                        self._cache_timestamp = datetime.fromisoformat(cache_time)
        except Exception as e:
            logger.error(f"Error loading cache: {str(e)}")
            
    def _save_cache(self):
        """Save exchanges to cache file"""
        try:
            os.makedirs(os.path.dirname(self._cache_file), exist_ok=True)
            with open(self._cache_file, 'w') as f:
                json.dump({
                    'exchanges': self._exchange_cache,
                    'timestamp': self._cache_timestamp.isoformat() if self._cache_timestamp else None
                }, f)
        except Exception as e:
            logger.error(f"Error saving cache: {str(e)}")
        
    def get_all_exchanges(self) -> List[Dict]:
        """Get all available exchanges from our local data"""
        now = datetime.now()
        
        # Return cached results if valid
        if (self._cache_timestamp and self._exchange_cache and 
            now - self._cache_timestamp < self._cache_duration):
            logger.debug("Returning cached exchange data")
            return list(self._exchange_cache.values())

        try:
            logger.debug("Fetching exchanges from local data")
            
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
            
            # Update cache
            self._exchange_cache = {ex['code']: ex for ex in exchange_list}
            self._cache_timestamp = now
            self._save_cache()
            
            logger.debug(f"Successfully loaded {len(exchange_list)} exchanges from local data")
            return exchange_list
            
        except Exception as e:
            logger.error(f"Error loading exchanges from local data: {str(e)}")
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
        try:
            # Use Yahoo Finance's lookup API
            url = "https://query2.finance.yahoo.com/v1/finance/lookup"
            params = {
                'query': query,
                'type': 'equity,etf',
                'count': 50,
                'formatted': 'true'
            }
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            logger.debug(f"Looking up {search_type} with query: {query}")
            response = requests.get(url, params=params, headers=headers)
            
            if not response.ok:
                logger.error(f"Yahoo Finance API error: {response.status_code} - {response.text}")
                return []
                
            try:
                data = response.json()
                logger.debug(f"Yahoo Finance API response: {data}")
            except ValueError as e:
                logger.error(f"Failed to parse Yahoo Finance API response: {response.text}")
                return []
            
            results = []
            seen_symbols = set()
            
            # Get the documents from the correct path in the JSON structure
            documents = data.get('finance', {}).get('result', [{}])[0].get('documents', [])
            
            # Process each quote from the lookup results
            for quote in documents:
                try:
                    # Skip non-equity/ETF results
                    if quote.get('quoteType', '').lower() not in ['equity', 'etf']:
                        continue
                    
                    symbol = quote.get('symbol')
                    company_name = quote.get('shortName', '')
                    
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
                    exchange_code = quote.get('exchange', '')
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
                            elif "OTC PINK" in exchange_info['name'].upper() or exchange_info['code'] == "PNK":
                                suffix = ".PK"
                            elif "OTC EXPERT" in exchange_info['name'].upper() or exchange_info['code'] == "OEM":
                                suffix = ".EX"
                            elif "OTCQX" in exchange_info['name'].upper() or exchange_info['code'] == "QX":
                                suffix = ".QX"
                            elif "OTCQB" in exchange_info['name'].upper() or exchange_info['code'] == "QB":
                                suffix = ".QB"
                            elif "BULLETIN BOARD" in exchange_info['name'].upper() or exchange_info['code'] == "OBB":
                                suffix = ".OB"
                    
                    # Format the result to match the frontend's expected format
                    result = {
                        'symbol': symbol,
                        'description': company_name,
                        'displaySymbol': symbol,
                        'exchange': exchange_info['name'] if exchange_info else exchange_code,
                        'type': quote.get('quoteType', ''),
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
                    logger.error(f"Error processing symbol {quote.get('symbol')}: {str(e)}")
                    continue
            
            logger.debug(f"Found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            raise Exception(f"Failed to search symbols: {str(e)}") 