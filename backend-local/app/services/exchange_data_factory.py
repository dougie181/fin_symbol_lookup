from typing import Dict, Type, List
import logging
from .base_provider import ExchangeDataProvider
from .providers.yahoo_finance_provider import YahooFinanceProvider
from .providers.alpha_vantage_provider import AlphaVantageProvider
from .providers.marketstack_provider import MarketstackProvider

logger = logging.getLogger(__name__)

class ExchangeDataFactory:
    """Factory for creating exchange data providers"""
    
    _providers: Dict[str, Type[ExchangeDataProvider]] = {
        'yahoo': YahooFinanceProvider,
        'alphavantage': AlphaVantageProvider,
        'marketstack': MarketstackProvider
    }
    
    @classmethod
    def create_provider(cls, provider_name: str) -> ExchangeDataProvider:
        """Create a provider instance by name"""
        if provider_name not in cls._providers:
            raise ValueError(f"Unknown provider: {provider_name}")
            
        logger.debug(f"Creating {provider_name} provider")
        return cls._providers[provider_name]()
    
    @classmethod
    def register_provider(cls, name: str, provider_class: Type[ExchangeDataProvider]):
        """Register a new provider"""
        cls._providers[name.lower()] = provider_class
        logger.debug(f"Registered new provider: {name}")
    
    @classmethod
    def get_available_providers(cls) -> List[Dict]:
        """Get list of available providers"""
        return [
            {
                'code': 'yahoo',
                'name': 'Yahoo Finance'
            },
            {
                'code': 'alphavantage',
                'name': 'Alpha Vantage'
            },
            {
                'code': 'marketstack',
                'name': 'Marketstack'
            }
        ]

    @classmethod
    def get_exchange_data(cls, provider_code: str = 'yahoo'):
        """Get exchange data using the specified provider"""
        return cls.create_provider(provider_code) 