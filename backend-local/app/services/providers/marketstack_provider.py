from typing import Dict, List, Optional
import requests
import os
import json
import time
from datetime import datetime, timedelta
from ...services.base_provider import ExchangeDataProvider
import logging

logger = logging.getLogger(__name__)

class MarketstackProvider(ExchangeDataProvider):
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('MARKETSTACK_API_KEY')
        if not self.api_key:
            raise ValueError("MARKETSTACK_API_KEY environment variable is not set")
        self.base_url = "http://api.marketstack.com/v2"
        
        # Create cache directory if it doesn't exist
        self.cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def _get_cache_path(self, cache_key: str) -> str:
        """Get the full path for a cache file"""
        # Add provider-specific prefix to prevent cache poisoning
        provider_prefix = "marketstack_"
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
            
    def _make_api_request(self, endpoint: str, params: Dict = None, cache_key: str = None, max_age_hours: int = 24) -> Dict:
        """Make an API request with proper error handling, rate limiting and caching"""
        try:
            # Try to get from cache first if cache_key provided
            if cache_key:
                cached_data = self._read_cache(cache_key, max_age_hours)
                if cached_data:
                    logger.debug(f"Using cached data for {endpoint}")
                    return cached_data
            
            # Add access_key to params
            if params is None:
                params = {}
            params['access_key'] = self.api_key
            
            logging.debug(f"Making API request to {self.base_url}/{endpoint} with params: {params}")
            # Make request
            response = requests.get(
                f"{self.base_url}/{endpoint}",
                params=params
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
        """Get list of available exchanges from Marketstack"""
        try:
            all_exchanges = []
            offset = 0
            limit = 3000  # Maximum per page
            
            # Try to get from cache first
            cached_data = self._read_cache('exchanges', max_age_hours=24)
            if cached_data:
                logger.info("Using cached exchange list")
                return cached_data
            
            while True:
                data = self._make_api_request(
                    "exchanges",
                    params={
                        "limit": limit,
                        "offset": offset
                    }
                )
                
                if not data.get('data'):
                    break
                    
                for exchange in data['data']:
                    logger.debug(f"Processing exchange: {exchange}")
                    # Map Marketstack exchange codes to our standard format
                    exchange_code = self._map_exchange_code(exchange.get('mic', ''))
                    if exchange_code:
                        all_exchanges.append({
                            'code': exchange_code,
                            'name': exchange.get('name', ''),
                            'country': exchange.get('country', ''),
                            'timezone': exchange.get('timezone', {}).get('timezone', '')
                        })
                    else:
                        logger.debug(f"No mapping found for exchange MIC: {exchange.get('mic', '')}")
                
                # Check if we've received all exchanges
                pagination = data.get('pagination', {})
                total_count = pagination.get('total', 0)
                current_count = pagination.get('offset', 0) + pagination.get('count', 0)
                
                if current_count >= total_count:
                    break
                    
                offset += limit
            
            # Cache the results
            if all_exchanges:
                self._write_cache('exchanges', all_exchanges)
            
            logger.info(f"Found {len(all_exchanges)} mapped exchanges")
            return all_exchanges
            
        except Exception as e:
            logger.error(f"Error fetching exchanges from Marketstack: {str(e)}")
            if isinstance(e, requests.exceptions.RequestException) and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            return []
            
    def search_symbols(self, query: str, exchange: str = None, search_type: str = 'symbol') -> List[Dict]:
        """Search for symbols using Marketstack's tickers endpoint"""
        try:
            results = []
            seen_symbols = set()
            
            # Generate cache key based on query and exchange
            cache_key = f"symbol_search_{query}_{exchange or 'all'}"
            
            # Try to get from cache first (shorter cache time for symbol searches)
            cached_results = self._read_cache(cache_key, max_age_hours=1)
            if cached_results:
                logger.debug(f"Using cached results for {query}")
                return cached_results
            
            # Use the tickerslist endpoint for searching
            params = {
                "search": query,
                "limit": 50
            }
            
            if exchange:
                mic_code = self._map_exchange_to_mic(exchange)
                if mic_code:
                    params["exchanges"] = mic_code
            
            data = self._make_api_request("tickerslist", params)
            
            for ticker in data.get('data', []):
                try:
                    symbol = ticker['ticker']  # Using 'ticker' instead of 'symbol'
                    exchange_info = ticker.get('stock_exchange', {})
                    exchange_code = self._map_exchange_code(exchange_info.get('mic', ''))
                    
                    # Skip if doesn't match requested exchange
                    if exchange and exchange_code != exchange:
                        continue
                        
                    # Use combination of symbol and exchange as unique key
                    symbol_key = f"{symbol}_{exchange_code}"
                    if symbol_key in seen_symbols:
                        continue
                        
                    suffix = self._get_symbol_suffix(exchange_code)
                    
                    results.append({
                        'symbol': symbol,
                        'description': ticker.get('name', ''),
                        'displaySymbol': symbol,
                        'exchange': exchange_info.get('name', ''),
                        'type': 'EQUITY',
                        'result': f"{symbol}{suffix}",
                        'country': exchange_info.get('country', ''),
                        'currency': exchange_info.get('currency', 'USD')
                    })
                    seen_symbols.add(symbol_key)
                    
                except Exception as e:
                    logger.error(f"Error processing ticker {ticker.get('ticker')}: {str(e)}")
                    continue
            
            # Cache the results
            if results:
                self._write_cache(cache_key, results)
            
            return results
            
        except Exception as e:
            return self._handle_api_error(e, "searching symbols")
            
    def _get_symbol_suffix(self, exchange_code: str) -> str:
        """Get the appropriate suffix for a symbol based on its exchange"""
        suffix_map = {
            'ASX': '.AX',
            'LSE': '.L',
            'TSX': '.TO',
            'HKEX': '.HK',
            'NYSE': '.NYS',
            'NASDAQ': '.NAS'
        }
        return suffix_map.get(exchange_code, '')
        
    def _map_exchange_code(self, mic_code: str) -> Optional[str]:
        """Map Marketstack's MIC codes to our standard exchange codes"""
        exchange_map = {
            'XNAS': 'NASDAQ',  # NASDAQ
            'XNYS': 'NYSE',    # New York Stock Exchange
            'XASX': 'ASX',     # Australian Securities Exchange
            'XASX.AX': 'ASX',  # ASX with suffix
            'XSFE': 'ASX',     # Sydney Futures Exchange (part of ASX)
            'XSYD': 'ASX',     # Sydney Stock Exchange
            'NSXA': 'NSX',     # National Stock Exchange of Australia
            'XLON': 'LSE',     # London Stock Exchange
            'XTSE': 'TSX',     # Toronto Stock Exchange
            'XHKG': 'HKEX',    # Hong Kong Stock Exchange
            'XETR': 'FRA',     # Frankfurt Stock Exchange
            'XAMS': 'AMS',     # Amsterdam Stock Exchange
            'XPAR': 'PAR',     # Paris Stock Exchange
            'XSWX': 'SWX',     # Swiss Exchange
            'XJPX': 'TSE',     # Tokyo Stock Exchange
            'XSES': 'SGX',     # Singapore Exchange
        }
        return exchange_map.get(mic_code)
        
    def _map_exchange_to_mic(self, exchange_code: str) -> Optional[str]:
        """Map our standard exchange codes to Marketstack's MIC codes"""
        mic_map = {
            'NASDAQ': 'XNAS',
            'NYSE': 'XNYS',
            'ASX': 'XASX',
            'NSX': 'NSXA',     # National Stock Exchange of Australia
            'LSE': 'XLON',
            'TSX': 'XTSE',
            'HKEX': 'XHKG',
            'FRA': 'XETR',
            'AMS': 'XAMS',
            'PAR': 'XPAR',
            'SWX': 'XSWX',
            'TSE': 'XJPX',
            'SGX': 'XSES'
        }
        return mic_map.get(exchange_code)

    def get_exchange(self, code: str) -> Dict:
        """Get a specific exchange by its code"""
        try:
            # First try to get from our exchange map
            mic_code = self._map_exchange_to_mic(code)
            if mic_code:
                response = requests.get(
                    f"{self.base_url}/exchanges/{mic_code}",
                    params={"access_key": self.api_key}
                )
                response.raise_for_status()
                
                data = response.json()
                if data.get('name'):
                    return {
                        'code': code,
                        'name': data['name'],
                        'country': data.get('country', ''),
                        'timezone': data.get('timezone', '')
                    }
            
            # If not found, return empty dict
            return {}
            
        except Exception as e:
            logger.error(f"Error getting exchange {code} from Marketstack: {e}")
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
            logger.error(f"Error searching exchanges on Marketstack: {e}")
            return []

    def _handle_api_error(self, e: Exception, context: str) -> List[Dict]:
        """Handle API errors with proper logging and user-friendly messages"""
        if isinstance(e, requests.exceptions.RequestException):
            if e.response is not None:
                status_code = e.response.status_code
                error_msg = ""
                
                try:
                    error_data = e.response.json().get('error', {})
                    error_msg = error_data.get('message', '')
                except:
                    error_msg = e.response.text
                
                if status_code == 401:
                    logger.error(f"Unauthorized: Check your API key or account status")
                elif status_code == 403:
                    if "https_access_restricted" in error_msg:
                        logger.error("HTTPS access not supported on current plan")
                    else:
                        logger.error("This API endpoint not supported on current plan")
                elif status_code == 404:
                    if "invalid_api_function" in error_msg:
                        logger.error("Invalid API endpoint")
                    else:
                        logger.error("Resource not found")
                elif status_code == 429:
                    if "too_many_requests" in error_msg:
                        logger.error("Monthly API request limit reached")
                    else:
                        logger.error("Rate limit reached (max 5 requests per second)")
                else:
                    logger.error(f"API error in {context}: {status_code} - {error_msg}")
            else:
                logger.error(f"Connection error in {context}: {str(e)}")
        else:
            logger.error(f"Error in {context}: {str(e)}")
        return [] 