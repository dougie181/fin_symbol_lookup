from flask import Blueprint, request, jsonify
from ..services.exchange_data_factory import ExchangeDataFactory
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Initialize blueprint FIRST
exchange_bp = Blueprint('exchange', __name__, url_prefix='/api')

# Then define routes
@exchange_bp.route('/exchanges', methods=['GET'])
def get_exchanges():
    """Get all available exchanges"""
    try:
        # Get provider from query parameter or use default
        provider_name = request.args.get('provider', 'yahoo')
        logger.debug(f"Using exchange data provider: {provider_name}")
        
        # Get the provider
        provider = ExchangeDataFactory.create_provider(provider_name)
        
        # Get exchanges
        exchanges = provider.get_all_exchanges()
        logger.debug(f"Found {len(exchanges)} exchanges")
        
        return jsonify(exchanges)
    except Exception as e:
        logger.error(f"Error getting exchanges: {str(e)}")
        return jsonify({'error': str(e)}), 500

@exchange_bp.route('/exchanges/selected', methods=['GET', 'POST'])
def manage_selected_exchanges():
    """Manage selected exchanges"""
    try:
        if request.method == 'POST':
            selected = request.json.get('exchanges', [])
            # TODO: Implement saving selected exchanges
            return jsonify({"status": "success", "selected": selected})
        else:
            # TODO: Implement loading selected exchanges
            return jsonify([])
    except Exception as e:
        logger.error(f"Error managing selected exchanges: {str(e)}")
        return jsonify({'error': str(e)}), 500

@exchange_bp.route('/search', methods=['GET'])
def search_symbols():
    """Search for symbols across exchanges"""
    try:
        # Get provider from query parameter or use default
        provider_name = request.args.get('provider', 'yahoo')
        logger.debug(f"Using exchange data provider: {provider_name}")
        
        # Get search parameters
        query = request.args.get('query', '')
        exchange = request.args.get('exchange', '')
        search_type = request.args.get('type', 'symbol')
        
        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400
            
        # Validate search type
        if search_type not in ['symbol', 'company']:
            return jsonify({'error': 'Invalid search type. Must be either "symbol" or "company"'}), 400
            
        # Get the provider
        provider = ExchangeDataFactory.create_provider(provider_name)
        
        # Search symbols
        results = provider.search_symbols(query, exchange, search_type)
        logger.debug(f"Found {len(results)} matches for {search_type} search: {query}")
        
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error searching symbols: {str(e)}")
        return jsonify({'error': str(e)}), 500

@exchange_bp.route('/exchanges/<code>', methods=['GET'])
def get_exchange(code):
    """Get a specific exchange by its code"""
    try:
        # Get provider from query parameter or use default
        provider_name = request.args.get('provider', 'yahoo')
        logger.debug(f"Using exchange data provider: {provider_name}")
        
        # Get the provider
        provider = ExchangeDataFactory.create_provider(provider_name)
        
        # Get exchange
        exchange = provider.get_exchange(code)
        if not exchange:
            return jsonify({'error': f'Exchange {code} not found'}), 404
            
        return jsonify(exchange)
    except Exception as e:
        logger.error(f"Error getting exchange {code}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@exchange_bp.route('/exchanges/search', methods=['GET'])
def search_exchanges():
    """Search exchanges by name or code"""
    try:
        # Get provider from query parameter or use default
        provider_name = request.args.get('provider', 'yahoo')
        logger.debug(f"Using exchange data provider: {provider_name}")
        
        # Get search query
        query = request.args.get('q')
        if not query:
            return jsonify({'error': 'Search query parameter "q" is required'}), 400
            
        # Get the provider
        provider = ExchangeDataFactory.create_provider(provider_name)
        
        # Search exchanges
        exchanges = provider.search_exchanges(query)
        logger.debug(f"Found {len(exchanges)} exchanges matching query: {query}")
        
        return jsonify(exchanges)
    except Exception as e:
        logger.error(f"Error searching exchanges: {str(e)}")
        return jsonify({'error': str(e)}), 500

@exchange_bp.route('/providers', methods=['GET'])
def get_providers():
    """Get list of available exchange data providers"""
    try:
        providers = ExchangeDataFactory.get_available_providers()
        return jsonify(providers)
    except Exception as e:
        logger.error(f"Error getting providers: {str(e)}")
        return jsonify({'error': str(e)}), 500 