'use client';

import React, { useState, useEffect } from 'react';

interface Exchange {
  code: string;
  name: string;
  country: string;
}

interface Symbol {
  symbol: string;
  description: string;
  displaySymbol: string;
  exchange: string;
  type: string;
  result: string;
}

// Use relative URLs for the API to leverage Next.js rewrites
const API_BASE_URL = '/api';

const Home: React.FC = () => {
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [selectedExchange, setSelectedExchange] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<Symbol[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch available exchanges on component mount
  useEffect(() => {
    const fetchExchanges = async () => {
      try {
        console.log('Fetching exchanges from: /api/exchanges');
        const response = await fetch('/api/exchanges', {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        console.log('Response status:', response.status);
        if (!response.ok) {
          const errorText = await response.text();
          console.error('Error response:', errorText);
          throw new Error(`Failed to fetch exchanges: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Received exchanges:', data);
        setExchanges(data);
      } catch (error) {
        console.error('Error fetching exchanges:', error);
      }
    };

    fetchExchanges();
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!searchQuery.trim()) {
      setError('Please enter a search term');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      console.log('Searching for:', searchQuery, 'on exchange:', selectedExchange);
      const response = await fetch(`/api/search?query=${encodeURIComponent(searchQuery)}&exchange=${encodeURIComponent(selectedExchange)}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      console.log('Search response status:', response.status);
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response:', errorText);
        throw new Error(`Failed to search symbols: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Search results:', data);
      setSearchResults(data);
      
      if (data.length === 0) {
        setError('No symbols found matching your search criteria');
      }
    } catch (error) {
      console.error('Error searching symbols:', error);
      setError('Error searching symbols. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-8 text-center">Financial Symbol Lookup</h1>
      
      <div className="max-w-2xl mx-auto bg-white shadow-md rounded-lg p-6">
        <form onSubmit={handleSearch} className="mb-6">
          <div className="mb-4">
            <label htmlFor="exchange" className="block mb-2 font-medium">
              Exchange (Optional)
            </label>
            <select
              id="exchange"
              value={selectedExchange}
              onChange={(e) => setSelectedExchange(e.target.value)}
              className="w-full px-4 py-2 border rounded-md"
            >
              <option value="">All Exchanges</option>
              {exchanges.map((exchange) => (
                <option key={exchange.code} value={exchange.code}>
                  {exchange.name} ({exchange.code}) - {exchange.country}
                </option>
              ))}
            </select>
          </div>
          
          <div className="mb-4">
            <label htmlFor="search" className="block mb-2 font-medium">
              Symbol or Company Name
            </label>
            <input
              id="search"
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="e.g. AAPL, Apple, MSFT"
              className="w-full px-4 py-2 border rounded-md"
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-blue-300"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>
        
        {error && (
          <div className="p-4 mb-4 text-red-700 bg-red-100 rounded-md">
            {error}
          </div>
        )}
        
        {searchResults.length > 0 && (
          <div>
            <h2 className="text-xl font-semibold mb-4">Search Results</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full border-collapse">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="border p-2 text-left">Symbol</th>
                    <th className="border p-2 text-left">Exchange</th>
                    <th className="border p-2 text-left">Result</th>
                    <th className="border p-2 text-left">Description</th>
                  </tr>
                </thead>
                <tbody>
                  {searchResults.map((result, index) => (
                    <tr key={index} className="border-b hover:bg-gray-50">
                      <td className="border p-2">{result.displaySymbol}</td>
                      <td className="border p-2">{result.exchange}</td>
                      <td className="border p-2 font-mono">{result.result}</td>
                      <td className="border p-2">{result.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;
