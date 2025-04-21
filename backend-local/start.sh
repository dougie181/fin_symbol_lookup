#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Financial Symbol Lookup Backend...${NC}"

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo -e "${GREEN}Activating virtual environment...${NC}"
    source .venv/bin/activate
else
    echo -e "${RED}Virtual environment not found. Creating one...${NC}"
    python3 -m venv .venv
    source .venv/bin/activate
fi

# Install requirements
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -r requirements.txt

# Make sure we have an API key
if [ ! -f ".env" ] || ! grep -q "FINNHUB_API_KEY" .env; then
    echo -e "${RED}Warning: FINNHUB_API_KEY not found in .env file.${NC}"
    echo -e "${RED}You'll need a valid API key from https://finnhub.io${NC}"
fi

# Run the application
echo -e "${GREEN}Starting Flask application...${NC}"
export FLASK_ENV=development
export FLASK_APP=app.py
echo -e "${BLUE}Server running at http://localhost:5000${NC}"
python3 app.py 