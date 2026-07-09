"use client";

import { useState, useEffect } from "react";

interface Approval {
  id: string;
  task_id: string | null;
  tool_name: string;
  description: string;
  payload: any;
  status: string;
  created_at: string;
}

export default function ApprovalsPage() {
  const [approvals, setApprovals] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchApprovals();
  }, []);

  async function fetchApprovals() {
    try {
      const response = await fetch("http://localhost:8000/api/approvals/pending");
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      setApprovals(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch approvals");
    } finally {
      setLoading(false);
    }
  }

  async function handleDecision(approvalId: string, decision: "approved" | "rejected") {
    try {
      const response = await fetch(`http://localhost:8000/api/approvals/${approvalId}/decide`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision, reviewed_by: "founder" }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      // Refresh the list
      await fetchApprovals();
    } catch (err) {
      alert(`Failed to ${decision}: ${err instanceof Error ? err.message : "Unknown error"}`);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-500">Loading approvals...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-600 font-semibold">Error</p>
          <p className="text-gray-600 text-sm">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto p-6">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Approval Queue</h1>
        <p className="text-gray-600 text-sm mt-1">
          {approvals.length} pending action{approvals.length !== 1 ? "s" : ""}
        </p>
      </header>

      {approvals.length === 0 ? (
        <div className="bg-white shadow rounded-lg p-8 text-center">
          <p className="text-gray-500">✓ No pending approvals</p>
        </div>
      ) : (
        <div className="space-y-4">
          {approvals.map((approval) => (
            <div key={approval.id} className="bg-white shadow rounded-lg p-6 border border-gray-200">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900">{approval.tool_name}</h3>
                  <p className="text-gray-600 text-sm mt-1">{approval.description}</p>
                  <div className="mt-3 bg-gray-50 p-3 rounded text-xs font-mono text-gray-700 overflow-auto max-h-48">
                    <pre>{JSON.stringify(approval.payload, null, 2)}</pre>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">
                    Created: {new Date(approval.created_at).toLocaleString()}
                  </p>
                </div>
                <div className="ml-4 flex flex-col gap-2">
                  <button
                    onClick={() => handleDecision(approval.id, "approved")}
                    className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded text-sm font-medium"
                  >
                    ✓ Approve
                  </button>
                  <button
                    onClick={() => handleDecision(approval.id, "rejected")}
                    className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded text-sm font-medium"
                  >
                    ✗ Reject
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
