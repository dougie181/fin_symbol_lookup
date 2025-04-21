#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Starting Financial Symbol Lookup Frontend...${NC}"

# Check if node_modules exists
if [ -d "node_modules" ]; then
    echo -e "${GREEN}Node modules found.${NC}"
else
    echo -e "${RED}Installing node modules...${NC}"
    npm install
fi

# Run the application
echo -e "${GREEN}Starting Next.js application...${NC}"
echo -e "${BLUE}Server running at http://localhost:3000${NC}"
npm run dev 