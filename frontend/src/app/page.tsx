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

interface Provider {
  code: string;
  name: string;
}

// Use relative URLs for the API to leverage Next.js rewrites
const API_BASE_URL = '/api';

const Home: React.FC = () => {
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>('yahoo');
  const [selectedExchange, setSelectedExchange] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchType, setSearchType] = useState<'symbol' | 'company'>('symbol');
  const [searchResults, setSearchResults] = useState<Symbol[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [providerError, setProviderError] = useState<string | null>(null);

  // Fetch available providers on component mount
  useEffect(() => {
    const fetchProviders = async () => {
      try {
        const response = await fetch('/api/providers');
        if (!response.ok) {
          throw new Error(`Failed to fetch providers: ${response.status}`);
        }
        const data = await response.json();
        setProviders(data);
      } catch (error) {
        console.error('Error fetching providers:', error);
        setError('Failed to fetch available providers. Please try again later.');
      }
    };

    fetchProviders();
  }, []);

  // Fetch available exchanges when provider changes
  useEffect(() => {
    const fetchExchanges = async () => {
      setProviderError(null);
      try {
        console.log('Fetching exchanges from: /api/exchanges');
        const response = await fetch(`/api/exchanges?provider=${selectedProvider}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        });
        console.log('Response status:', response.status);
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.error || `Failed to fetch exchanges: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Received exchanges:', data);
        setExchanges(data);
      } catch (err: any) {
        console.error('Error fetching exchanges:', err);
        setProviderError(`Error with ${selectedProvider}: ${err.message}`);
        setExchanges([]);
      }
    };

    fetchExchanges();
  }, [selectedProvider]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!searchQuery.trim()) {
      setError('Please enter a search term');
      return;
    }
    
    setLoading(true);
    setError(null);
    setProviderError(null);
    
    try {
      console.log('Searching for:', searchQuery, 'on exchange:', selectedExchange);
      const response = await fetch(
        `/api/search?query=${encodeURIComponent(searchQuery)}&exchange=${encodeURIComponent(selectedExchange)}&type=${searchType}&provider=${selectedProvider}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json'
          }
        }
      );
      console.log('Search response status:', response.status);
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.error || `Failed to search symbols: ${response.status}`);
      }
      
      console.log('Search results:', data);
      setSearchResults(data);
      
      if (data.length === 0) {
        setError('No results found matching your search criteria');
      }
    } catch (err: any) {
      console.error('Error searching symbols:', err);
      if (err.message.includes('API key')) {
        setProviderError(`${providers.find(p => p.code === selectedProvider)?.name} is not properly configured. Please contact the administrator.`);
      } else {
        setError('Error searching symbols. Please try again later.');
      }
      setSearchResults([]);
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
            <label htmlFor="provider" className="block mb-2 font-medium">
              Data Provider
            </label>
            <select
              id="provider"
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              className="w-full px-4 py-2 border rounded-md"
            >
              {providers.map((provider) => (
                <option key={provider.code} value={provider.code}>
                  {provider.name}
                </option>
              ))}
            </select>
            {providerError && (
              <div className="mt-2 text-sm text-red-600">
                {providerError}
              </div>
            )}
          </div>

          <div className="mb-4">
            <label htmlFor="exchange" className="block mb-2 font-medium">
              Exchange (Optional)
            </label>
            <select
              id="exchange"
              value={selectedExchange}
              onChange={(e) => setSelectedExchange(e.target.value)}
              className="w-full px-4 py-2 border rounded-md"
              disabled={!!providerError}
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
            <label htmlFor="searchType" className="block mb-2 font-medium">
              Search By
            </label>
            <select
              id="searchType"
              value={searchType}
              onChange={(e) => setSearchType(e.target.value as 'symbol' | 'company')}
              className="w-full px-4 py-2 border rounded-md"
              disabled={!!providerError}
            >
              <option value="symbol">Symbol</option>
              <option value="company">Company Name</option>
            </select>
          </div>
          
          <div className="mb-4">
            <label htmlFor="search" className="block mb-2 font-medium">
              {searchType === 'symbol' ? 'Symbol' : 'Company Name'}
            </label>
            <input
              id="search"
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={searchType === 'symbol' ? 'e.g. AAPL, MSFT' : 'e.g. Apple, Microsoft'}
              className="w-full px-4 py-2 border rounded-md"
              required
              disabled={!!providerError}
            />
          </div>
          
          <button
            type="submit"
            disabled={loading || !!providerError}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-blue-300"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>
        
        {error && !providerError && (
          <div className="p-4 mb-4 text-red-700 bg-red-100 rounded-md">
            {error}
          </div>
        )}
        
        {searchResults.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full table-auto">
              <thead>
                <tr className="bg-gray-100">
                  <th className="px-4 py-2 text-left">Symbol</th>
                  <th className="px-4 py-2 text-left">Exchange</th>
                  <th className="px-4 py-2 text-left">Result</th>
                  <th className="px-4 py-2 text-left">Description</th>
                </tr>
              </thead>
              <tbody>
                {searchResults.map((result, index) => (
                  <tr key={index} className="border-t">
                    <td className="px-4 py-2">{result.symbol}</td>
                    <td className="px-4 py-2">{result.exchange}</td>
                    <td className="px-4 py-2">{result.result}</td>
                    <td className="px-4 py-2">{result.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Home;
