from typing import Dict, List, Optional
import requests
import os
import json
import time
from datetime import datetime, timedelta
from ...services.base_provider import ExchangeDataProvider
from ...services.exchange_data_service import ExchangeDataService
import logging

logger = logging.getLogger(__name__)

class OpenFIGIProvider(ExchangeDataProvider):
    """OpenFIGI implementation of exchange data provider"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('OPENFIGI_API_KEY')
        self.base_url = "https://api.openfigi.com/v3"
        
        # Create cache directory if it doesn't exist
        self.cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize exchange service for local exchange data
        self.exchange_service = ExchangeDataService()
        
    def _get_cache_path(self, cache_key: str) -> str:
        """Get the full path for a cache file"""
        # Add provider-specific prefix to prevent cache poisoning
        provider_prefix = "openfigi_"
        return os.path.join(self.cache_dir, f"{provider_prefix}{cache_key}.json")
        
    def _read_cache(self, cache_key: str, max_age_hours: int = 24) -> Optional[Dict]:
        """Read data from cache if it exists and is not too old"""
        try:
            cache_path = self._get_cache_path(cache_key)
            if not os.path.exists(cache_path):
                return None
                
            # Check if cache is too old
            if time.time() - os.path.getmtime(cache_path) > max_age_hours * 3600:
                return None
                
            with open(cache_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error reading cache {cache_key}: {e}")
            return None
            
    def _write_cache(self, cache_key: str, data: Dict) -> None:
        """Write data to cache"""
        try:
            cache_path = self._get_cache_path(cache_key)
            with open(cache_path, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            logger.warning(f"Error writing cache {cache_key}: {e}")
            
    def _make_api_request(self, endpoint: str, data: Dict = None, cache_key: str = None, max_age_hours: int = 24) -> Dict:
        """Make an API request with proper error handling and caching"""
        try:
            # Try to get from cache first if cache_key provided
            if cache_key:
                cached_data = self._read_cache(cache_key, max_age_hours)
                if cached_data:
                    logger.debug(f"Using cached data for {endpoint}")
                    return cached_data
            
            # Prepare headers
            headers = {
                'Content-Type': 'application/json'
            }
            if self.api_key:
                headers['X-OPENFIGI-APIKEY'] = self.api_key
            
            # Make request
            response = requests.post(
                f"{self.base_url}/{endpoint}",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            data = response.json()
            
            # Cache the response if cache_key provided
            if cache_key and data:
                self._write_cache(cache_key, data)
            
            return data
        except Exception as e:
            self._handle_api_error(e, f"API request to {endpoint}")
            return {}
            
    def get_all_exchanges(self) -> List[Dict]:
        """Get all available exchanges from our local data"""
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
        try:
            # Get all exchanges first
            exchanges = self.get_all_exchanges()
            
            # Filter by query
            query = query.lower()
            return [
                ex for ex in exchanges
                if query in ex['code'].lower() or
                   query in ex['name'].lower() or
                   query in ex.get('country', '').lower()
            ]
            
        except Exception as e:
            logger.error(f"Error searching exchanges: {str(e)}")
            return []
            
    def _map_openfigi_to_exchange(self, openfigi_code: str, market_sector: str = None, security_type: str = None, composite_figi: str = None) -> Optional[str]:
        """Map OpenFIGI's exchange codes back to our exchange codes"""
        # Direct mapping of OpenFIGI exchange codes to our system
        exchange_map = {
            'AU': 'ASX',     # Australian Securities Exchange
            'GB': 'LSE',     # London Stock Exchange
            'CA': 'TSX',     # Toronto Stock Exchange
            'HK': 'HKEX',    # Hong Kong Stock Exchange
            'DE': 'FRA',     # Frankfurt Stock Exchange
            'NL': 'AMS',     # Amsterdam Stock Exchange
            'FR': 'PAR',     # Paris Stock Exchange
            'CH': 'SWX',     # Swiss Exchange
            'JP': 'TSE',     # Tokyo Stock Exchange
            'SG': 'SGX',     # Singapore Exchange
            'UA': 'NAS',     # NASDAQ
            'US': 'NYSE',    # NYSE
        }
        
        # First try direct mapping
        if openfigi_code in exchange_map:
            return exchange_map[openfigi_code]
            
        # For US markets, try to determine based on the composite FIGI
        if composite_figi and len(composite_figi) >= 2:
            prefix = composite_figi[:2].upper()
            if prefix == 'UA':
                return 'NAS'  # NASDAQ
            elif prefix == 'BB':
                return 'NYSE'
                
        return None

    def _is_valid_listing(self, item: Dict) -> bool:
        """Determine if this is a valid listing we want to show"""
        # Skip if it's not a stock or ETF
        if not any(x in item.get('securityType', '') for x in ['Common Stock', 'ETF', 'ETP']):
            return False
            
        # Skip depositary receipts and other secondary instruments
        if any(x in item.get('securityType2', '') for x in ['Depositary Receipt', 'DR', 'CEDEAR']):
            return False
            
        # Skip warrants and options
        if any(x in item.get('securityType', '') for x in ['WRT', 'Option', 'Future']):
            return False
            
        return True

    def search_symbols(self, query: str, exchange: str = None, search_type: str = 'symbol') -> List[Dict]:
        """Search for symbols using OpenFIGI's search endpoint"""
        try:
            results = []
            seen_symbol_exchanges = set()  # Track symbol+exchange combinations
            
            # Generate cache key based on query and exchange
            cache_key = f"symbol_search_{query}_{exchange or 'all'}"
            
            # Try to get from cache first (shorter cache time for symbol searches)
            cached_results = self._read_cache(cache_key, max_age_hours=1)
            if cached_results:
                logger.debug(f"Using cached results for {query}")
                return cached_results
            
            # First try the search endpoint
            search_request = {
                "query": query
            }
            
            # Only add exchCode if an exchange is specified
            if exchange:
                # Map our exchange code to OpenFIGI format
                exch_code = self._map_exchange_to_openfigi(exchange)
                if exch_code:
                    search_request["exchCode"] = exch_code
            
            logger.debug(f"Making OpenFIGI search request: {search_request}")
            
            # Make the search API request
            search_data = self._make_api_request("search", data=search_request)
            logger.debug(f"OpenFIGI search response: {search_data}")
            
            # Process all valid listings
            if 'data' in search_data:
                for item in search_data['data']:
                    try:
                        # Skip invalid listings
                        if not self._is_valid_listing(item):
                            continue
                            
                        symbol = item.get('ticker')
                        if not symbol:
                            continue
                            
                        # Get exchange info
                        openfigi_exchange = item.get('exchCode', '')
                        logger.debug(f"Processing item with OpenFIGI exchange code: {openfigi_exchange}")
                        
                        # Skip if doesn't match requested exchange
                        if exchange:
                            mapped_exchange = self._map_exchange_to_openfigi(exchange)
                            logger.debug(f"Comparing exchange codes: {openfigi_exchange} vs {mapped_exchange}")
                            if openfigi_exchange != mapped_exchange:
                                continue
                        
                        # Map OpenFIGI exchange code back to our system's exchange code
                        our_exchange_code = self._map_openfigi_to_exchange(
                            openfigi_exchange,
                            market_sector=item.get('marketSector'),
                            security_type=item.get('securityType'),
                            composite_figi=item.get('compositeFIGI')
                        )
                        if not our_exchange_code:
                            logger.debug(f"Could not map OpenFIGI exchange code {openfigi_exchange} to our system")
                            continue
                            
                        # Skip if we've seen this symbol+exchange combination
                        symbol_exchange = f"{symbol}:{our_exchange_code}"
                        if symbol_exchange in seen_symbol_exchanges:
                            continue
                            
                        exchange_info = self.get_exchange(our_exchange_code)
                        
                        # Get appropriate suffix
                        suffix = self.exchange_service.get_exchange_suffix(our_exchange_code) or ''
                        
                        # Map security type to our standard format
                        security_type = item.get('securityType', '')
                        if 'Common Stock' in security_type:
                            security_type = 'EQUITY'
                        elif 'Option' in security_type:
                            security_type = 'OPTION'
                        elif 'ETF' in security_type:
                            security_type = 'ETF'
                        else:
                            security_type = security_type.upper()
                        
                        result_item = {
                            'symbol': symbol,
                            'description': item.get('name', ''),
                            'displaySymbol': symbol,
                            'exchange': our_exchange_code,
                            'type': security_type,
                            'result': f"{symbol}{suffix}",
                            'country': exchange_info.get('country', '') if exchange_info else '',
                            'currency': item.get('currency', 'USD')
                        }
                        
                        logger.debug(f"Adding search result: {result_item}")
                        results.append(result_item)
                        seen_symbol_exchanges.add(symbol_exchange)
                        
                    except Exception as e:
                        logger.error(f"Error processing search result {item.get('ticker')}: {str(e)}")
                        continue
            
            # Cache the results
            if results:
                self._write_cache(cache_key, results)
            
            logger.debug(f"Found {len(results)} results for query: {query}")
            return results
            
        except Exception as e:
            logger.error(f"Error searching symbols: {str(e)}")
            return []
            
    def _map_exchange_to_openfigi(self, exchange_code: str) -> Optional[str]:
        """Map our exchange codes to OpenFIGI's country codes"""
        # OpenFIGI uses country codes (e.g., "AU" for Australia) rather than exchange codes
        country_map = {
            'ASX': 'AU',     # Australian Securities Exchange
            'NYSE': 'US',    # New York Stock Exchange
            'NASDAQ': 'US',  # NASDAQ
            'LSE': 'GB',     # London Stock Exchange
            'TSX': 'CA',     # Toronto Stock Exchange
            'HKEX': 'HK',    # Hong Kong Stock Exchange
            'FRA': 'DE',     # Frankfurt Stock Exchange
            'AMS': 'NL',     # Amsterdam Stock Exchange
            'PAR': 'FR',     # Paris Stock Exchange
            'SWX': 'CH',     # Swiss Exchange
            'TSE': 'JP',     # Tokyo Stock Exchange
            'SGX': 'SG'      # Singapore Exchange
        }
        return country_map.get(exchange_code)
            
    def _handle_api_error(self, e: Exception, context: str) -> List[Dict]:
        """Handle API errors with proper logging and user-friendly messages"""
        if isinstance(e, requests.exceptions.RequestException):
            if e.response is not None:
                status_code = e.response.status_code
                error_msg = ""
                
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('error', '')
                except:
                    error_msg = e.response.text
                
                if status_code == 401:
                    logger.error("Unauthorized: Check your API key or account status")
                elif status_code == 403:
                    logger.error("This API endpoint not supported on current plan")
                elif status_code == 404:
                    logger.error("Resource not found")
                elif status_code == 429:
                    logger.error("Rate limit reached")
                else:
                    logger.error(f"API error in {context}: {status_code} - {error_msg}")
            else:
                logger.error(f"Connection error in {context}: {str(e)}")
        else:
            logger.error(f"Error in {context}: {str(e)}")
        return [] 