# Financial Symbol Lookup

A simple application that allows users to search for financial symbols across different exchanges. The application consists of a NextJS frontend and a Flask backend.

## Features

- Multiple data provider support with easy switching
- View a list of major stock exchanges
- Search for financial symbols by either:
  - Symbol (e.g., AAPL, MSFT)
  - Company Name (e.g., Apple, Microsoft)
- Filter search results by specific exchange
- View symbol details including full name and exchange
- Support for multiple exchanges including:
  - US Markets (NASDAQ, NYSE, OTC Markets)
  - International Markets (ASX, LSE, TSX, HKEX)
- Special handling for CHESS Depositary Interests (CDIs) on ASX

## Prerequisites

- Python 3.8+
- Node.js 14+

## Setup

1. Clone the repository
2. Install backend dependencies:
   ```bash
   cd backend-local
   pip install -r requirements.txt
   ```
3. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

## Running the Application

### Backend

```bash
cd backend-local
./start.sh
```

The backend will be available at http://localhost:5001

### Frontend

```bash
cd frontend
./start.sh
```

The frontend will be available at http://localhost:3000

## API Endpoints

All API endpoints support both trailing and non-trailing slashes (e.g., both `/api/exchanges` and `/api/exchanges/` will work).
All endpoints accept an optional `provider` query parameter to specify the data provider (defaults to 'yahoo').

### Exchange Related
- `GET /api/exchanges` - Get a list of all available exchanges
  - Query parameters:
    - `provider`: (Optional) Data provider to use
- `GET /api/exchanges/<code>` - Get details for a specific exchange
  - Query parameters:
    - `provider`: (Optional) Data provider to use
- `GET /api/exchanges/search` - Search exchanges by name or code
  - Query parameters:
    - `q`: Search query string
    - `provider`: (Optional) Data provider to use
- `GET /api/exchanges/selected` - Get user's selected exchanges
- `POST /api/exchanges/selected` - Update user's selected exchanges
  - Body: `{ "exchanges": ["ASX", "NYSE", ...] }`

### Symbol Search
- `GET /api/search` - Search for symbols with the following parameters:
  - `query`: The search term
  - `exchange`: (Optional) Filter by exchange code
  - `type`: Search type ('symbol' or 'company')
  - `provider`: (Optional) Data provider to use
  - Example: `/api/search?query=AAPL&exchange=NMS&type=symbol&provider=yahoo`

### Provider Information
- `GET /api/providers` - Get list of available data providers
  - Returns: Array of provider objects with `code` and `name`
  - Example response: `[{"code": "yahoo", "name": "Yahoo Finance"}, ...]`

## Technologies Used

- **Frontend:** Next.js, React, TypeScript, TailwindCSS
- **Backend:** Flask, Python
- **Data Providers:**
  - Yahoo Finance API (default)
  - Additional providers can be easily integrated
- **Styling:** Modern UI with responsive design

## Development Notes

- The backend uses Flask-CORS to allow cross-origin requests from the frontend
- Symbol search supports both exact and partial matches
- Exchange codes are standardized (e.g., .AX for ASX, .L for LSE)
- Special handling for different market types:
  - NASDAQ/NYSE listed securities
  - OTC Markets (Pink, Expert, OTCQX, OTCQB)
  - International exchanges
  - CHESS Depositary Interests
- URLs support both trailing and non-trailing slashes
- Provider system is extensible - new providers can be added by implementing the ExchangeDataProvider interface
