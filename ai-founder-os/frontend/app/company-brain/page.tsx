"use client";

import { useState, useEffect } from "react";

interface MemoryEntry {
  key: string;
  value: string;
  updated_at: string;
}

export default function CompanyBrainPage() {
  const [entries, setEntries] = useState<MemoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    fetchMemory();
  }, []);

  async function fetchMemory() {
    try {
      const response = await fetch("http://localhost:8000/api/memory/?limit=50");
      if (!response.ok) throw new Error("Failed to fetch");
      const data = await response.json();
      setEntries(data);
    } catch (err) {
      console.error("Failed to fetch memory:", err);
    } finally {
      setLoading(false);
    }
  }

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setSearching(true);
    try {
      const response = await fetch("http://localhost:8000/api/memory/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: searchQuery, top_k: 5 }),
      });
      if (!response.ok) throw new Error("Search failed");
      const data = await response.json();
      setSearchResults(data.results);
    } catch (err) {
      console.error("Search error:", err);
    } finally {
      setSearching(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-500">Loading company brain...</p>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto p-6">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Company Brain</h1>
        <p className="text-gray-600 text-sm mt-1">Long-term memory and knowledge base</p>
      </header>

      {/* Semantic Search */}
      <div className="bg-white shadow rounded-lg p-6 mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Semantic Search</h2>
        <form onSubmit={handleSearch} className="flex gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search company knowledge..."
            className="flex-1 border border-gray-300 rounded px-4 py-2 focus:outline-none focus:border-blue-500"
          />
          <button
            type="submit"
            disabled={searching}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded font-medium disabled:opacity-50"
          >
            {searching ? "Searching..." : "Search"}
          </button>
        </form>

        {searchResults.length > 0 && (
          <div className="mt-6 space-y-3">
            <h3 className="font-semibold text-gray-900">Results:</h3>
            {searchResults.map((result, idx) => (
              <div key={idx} className="border border-gray-200 rounded p-3 bg-gray-50">
                <p className="text-sm font-semibold text-gray-900">{result.key}</p>
                <p className="text-sm text-gray-700 mt-1">{result.content.slice(0, 200)}...</p>
                <p className="text-xs text-gray-500 mt-2">
                  Similarity: {(result.similarity * 100).toFixed(1)}%
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* All Memory Entries */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">All Memory Entries</h2>
        {entries.length === 0 ? (
          <p className="text-gray-500">No memory entries yet. Run seed_onboarding.py to populate.</p>
        ) : (
          <div className="space-y-3">
            {entries.map((entry) => (
              <div key={entry.key} className="bg-white shadow-sm rounded-lg p-4 border border-gray-200">
                <h3 className="font-semibold text-gray-900">{entry.key}</h3>
                <p className="text-sm text-gray-700 mt-2 whitespace-pre-wrap">{entry.value.slice(0, 300)}</p>
                {entry.value.length > 300 && <span className="text-gray-400 text-sm">...</span>}
                <p className="text-xs text-gray-400 mt-3">
                  Updated: {new Date(entry.updated_at).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
