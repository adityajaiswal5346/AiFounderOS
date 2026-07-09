"use client";

import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";

interface Digest {
  run_id: string;
  date: string;
  markdown: string;
  pending_approval_count: number;
  created_at: string;
}

export default function DashboardPage() {
  const [digest, setDigest] = useState<Digest | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchDigest() {
      try {
        const response = await fetch("http://localhost:8000/api/digest/latest");
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        setDigest(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to fetch digest");
      } finally {
        setLoading(false);
      }
    }
    fetchDigest();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-500">Loading daily digest...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 font-semibold">Error</p>
          <p className="text-gray-600 text-sm">{error}</p>
          <p className="text-gray-500 text-xs mt-2">
            Make sure the backend is running on http://localhost:8000
          </p>
        </div>
      </div>
    );
  }

  if (!digest) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-500">No digest available yet. Run the daily cycle first.</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Daily Digest</h1>
        <p className="text-gray-600 text-sm mt-1">
          {digest.date} • Run ID: {digest.run_id}
        </p>
        {digest.pending_approval_count > 0 && (
          <div className="mt-3 inline-block bg-yellow-100 border border-yellow-400 text-yellow-800 px-3 py-1 rounded text-sm">
            ⚠️ {digest.pending_approval_count} pending approval{digest.pending_approval_count > 1 ? "s" : ""}
          </div>
        )}
      </header>

      <div className="bg-white shadow rounded-lg p-6 prose prose-sm max-w-none">
        <ReactMarkdown>{digest.markdown}</ReactMarkdown>
      </div>
    </div>
  );
}
