from abc import ABC, abstractmethod
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class ExchangeDataProvider(ABC):
    """Abstract base class for exchange data providers"""
    
    @abstractmethod
    def get_all_exchanges(self) -> List[Dict]:
        """Get all available exchanges from the provider"""
        pass
    
    @abstractmethod
    def get_exchange(self, code: str) -> Dict:
        """Get a specific exchange by its code"""
        pass
    
    @abstractmethod
    def search_exchanges(self, query: str) -> List[Dict]:
        """Search exchanges by name or code"""
        pass
    
    @abstractmethod
    def search_symbols(self, query: str, exchange: str = None) -> List[Dict]:
        """Search for symbols that match the query, optionally filtering by exchange"""
        pass 