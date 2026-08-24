"use client";

import useSWR from "swr";
import { useState } from "react";
import { fetcher, postApi } from "../../lib/api";
import { Card, PageHeader, Badge, Button, Input } from "../../components/ui";

export default function CompanyBrainPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const { data, error, isLoading, mutate } = useSWR("/memory/", fetcher);
  const [searchResults, setSearchResults] = useState<any>(null);

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    try {
      const res = await postApi("/memory/search", { query: searchQuery, top_k: 5 });
      setSearchResults(res.results);
    } catch (err) {
      alert("Search failed.");
    }
  };

  const displayData = searchResults !== null ? searchResults : data;

  return (
    <div style={{ animation: "fadeIn 0.5s ease-out" }}>
      <PageHeader 
        title="Company Brain" 
        subtitle="Shared memory, knowledge, and brand guidelines for all agents."
      >
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <Input 
            placeholder="Search memory..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            style={{ width: "250px" }}
          />
          <Button variant="secondary" onClick={handleSearch}>Search</Button>
        </div>
      </PageHeader>

      {isLoading && <p style={{ color: "var(--text-muted)" }}>Loading memory...</p>}
      {error && (
        <Card style={{ borderColor: "var(--danger)" }}>
          <p style={{ color: "var(--danger)" }}>Failed to load memory: {error.message}</p>
        </Card>
      )}

      {displayData && displayData.length === 0 && (
        <Card style={{ textAlign: "center", padding: "3rem 1rem", borderStyle: "dashed" }}>
          <p style={{ color: "var(--text-muted)" }}>No knowledge stored yet.</p>
        </Card>
      )}

      <div style={{ display: "grid", gap: "1.5rem", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))" }}>
        {displayData && displayData.map((item: any, idx: number) => (
          <Card key={item.key || idx} className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <h3 style={{ margin: "0", fontSize: "1.125rem", color: "var(--text-primary)", wordBreak: "break-all" }}>
                {item.key || "Unnamed Entry"}
              </h3>
              {item.distance !== undefined && (
                <Badge variant="primary">Match: {(1 - item.distance).toFixed(2)}</Badge>
              )}
            </div>
            
            <div style={{ backgroundColor: "rgba(0,0,0,0.2)", padding: "1rem", borderRadius: "var(--radius-md)", flex: 1 }}>
              <p style={{ margin: 0, fontSize: "0.875rem", color: "var(--text-secondary)", whiteSpace: "pre-wrap" }}>
                {item.value || item.content}
              </p>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
