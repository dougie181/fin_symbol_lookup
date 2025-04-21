from typing import Dict, Type
import logging
from .base_provider import ExchangeDataProvider
from .providers.yahoo_finance_provider import YahooFinanceProvider

logger = logging.getLogger(__name__)

class ExchangeDataFactory:
    """Factory for creating exchange data providers"""
    
    _providers: Dict[str, Type[ExchangeDataProvider]] = {
        'yahoo': YahooFinanceProvider
    }
    
    @classmethod
    def create_provider(cls, provider_type: str = 'yahoo') -> ExchangeDataProvider:
        """Create a new exchange data provider instance"""
        try:
            provider_class = cls._providers.get(provider_type.lower())
            if not provider_class:
                raise ValueError(f"Unknown provider type: {provider_type}")
            
            logger.debug(f"Creating {provider_type} provider")
            return provider_class()
            
        except Exception as e:
            logger.error(f"Error creating provider: {str(e)}")
            raise

    @classmethod
    def register_provider(cls, name: str, provider_class: Type[ExchangeDataProvider]):
        """Register a new provider"""
        cls._providers[name.lower()] = provider_class
        logger.debug(f"Registered new provider: {name}")
    
    @classmethod
    def get_available_providers(cls) -> list:
        """Get list of available provider names"""
        return list(cls._providers.keys()) 