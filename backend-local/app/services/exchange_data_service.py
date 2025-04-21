import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import os

@dataclass
class Exchange:
    code: str
    name: str
    country: str
    market_code: str
    suffix: str
    status: str

class ExchangeDataService:
    def __init__(self, data_file: str = None):
        # Use absolute path to the data file
        if data_file is None:
            current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
            self.data_file = current_dir.parent / 'data' / 'exchanges.json'
        else:
            self.data_file = Path(data_file)
            
        self._exchanges: Dict[str, Exchange] = {}
        self._load_exchanges()
        
    def _load_exchanges(self) -> None:
        """Load exchange data from JSON file"""
        try:
            if not self.data_file.exists():
                print(f"Exchange data file not found at: {self.data_file}")
                return
                
            with open(self.data_file) as f:
                data = json.load(f)
                for exchange_data in data["exchanges"]:
                    exchange = Exchange(**exchange_data)
                    self._exchanges[exchange.code] = exchange
                print(f"Loaded {len(self._exchanges)} exchanges from {self.data_file}")
        except Exception as e:
            print(f"Error loading exchanges: {str(e)}")
            self._exchanges = {}
            
    def get_exchange(self, code: str) -> Optional[Exchange]:
        """Get exchange by code"""
        return self._exchanges.get(code.upper())
        
    def get_all_exchanges(self) -> List[Exchange]:
        """Get all exchanges"""
        return list(self._exchanges.values())
        
    def get_exchanges_by_country(self, country: str) -> List[Exchange]:
        """Get exchanges by country"""
        return [
            exchange for exchange in self._exchanges.values()
            if exchange.country.lower() == country.lower()
        ]
        
    def get_exchange_suffix(self, code: str) -> Optional[str]:
        """Get exchange suffix by code"""
        exchange = self.get_exchange(code)
        return exchange.suffix if exchange else None
        
    def update_exchange_data(self, new_data: List[Dict]) -> None:
        """Update exchange data"""
        try:
            # Validate new data
            validated_data = []
            for item in new_data:
                if all(k in item for k in ['code', 'name', 'country', 'market_code', 'suffix']):
                    validated_data.append(item)
                    
            # Update in-memory data
            self._exchanges = {
                ex['code']: Exchange(**ex)
                for ex in validated_data
            }
            
            # Save to file
            with open(self.data_file, 'w') as f:
                json.dump({"exchanges": validated_data}, f, indent=4)
        except Exception as e:
            print(f"Error updating exchange data: {str(e)}") 