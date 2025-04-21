import os
import json
from typing import List, Dict, Any

class ConfigService:
    def __init__(self):
        # Create a data directory if it doesn't exist
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self.exchanges_file = os.path.join(self.data_dir, 'selected_exchanges.json')
    
    def save_selected_exchanges(self, exchanges: List[str]) -> None:
        """Save list of selected exchange codes to a JSON file"""
        try:
            with open(self.exchanges_file, 'w') as f:
                json.dump(exchanges, f)
        except Exception as e:
            raise Exception(f"Failed to save selected exchanges: {str(e)}")
    
    def load_selected_exchanges(self) -> List[str]:
        """Load list of selected exchange codes from a JSON file"""
        try:
            if not os.path.exists(self.exchanges_file):
                return []
            with open(self.exchanges_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            # If there's an error, return an empty list
            return [] 