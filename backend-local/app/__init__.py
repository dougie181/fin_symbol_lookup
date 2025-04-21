from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

def create_app():
    app = Flask(__name__)
    
    # Enable CORS with simpler configuration - allow all origins
    CORS(app, supports_credentials=True)
    
    # Register blueprints
    from app.routes.exchange_routes import exchange_bp
    app.register_blueprint(exchange_bp)
    
    return app