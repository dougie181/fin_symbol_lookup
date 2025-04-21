from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()  # Load environment variables

def create_app():
    """Create and configure the Flask application"""
    
    # Create Flask app
    app = Flask(__name__)
    
    # Configure app
    app.url_map.strict_slashes = False  # Allow URLs with or without trailing slashes
    
    # Enable CORS
    CORS(app)
    
    # Register blueprints
    from app.routes.exchange_routes import exchange_bp
    app.register_blueprint(exchange_bp)
    
    return app