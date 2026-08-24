"use client";

import useSWR from "swr";
import { fetcher } from "../../lib/api";
import { Card, PageHeader, Badge } from "../../components/ui";
import ReactMarkdown from "react-markdown";

export default function DashboardPage() {
  const { data, error, isLoading } = useSWR("/digest/latest", fetcher);

  return (
    <div style={{ animation: "fadeIn 0.5s ease-out" }}>
      <PageHeader 
        title="CEO Daily Digest" 
        subtitle="Your morning briefing synthesized from all specialist agents." 
      />

      {isLoading && <p style={{ color: "var(--text-muted)" }}>Loading digest...</p>}
      {error && (
        <Card style={{ borderColor: "var(--danger)" }}>
          <p style={{ color: "var(--danger)" }}>Failed to load digest: {error.message}</p>
        </Card>
      )}

      {data && (
        <div style={{ display: "grid", gap: "2rem" }}>
          <Card className="glass-panel">
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "1.5rem" }}>
              <h2 style={{ fontSize: "1.25rem", fontWeight: "600", margin: 0 }}>Latest Synthesis</h2>
              <Badge variant="primary">{new Date(data.created_at).toLocaleDateString()}</Badge>
            </div>
            
            <div className="prose">
              <ReactMarkdown>{data.digest}</ReactMarkdown>
            </div>
          </Card>

          {data.conflicts && data.conflicts.length > 0 && (
            <Card style={{ borderColor: "var(--warning)", background: "rgba(245, 158, 11, 0.05)" }}>
              <h3 style={{ color: "var(--warning)", marginTop: 0, marginBottom: "1rem" }}>Detected Conflicts</h3>
              <ul style={{ paddingLeft: "1.5rem", margin: 0, color: "var(--text-secondary)" }}>
                {data.conflicts.map((conflict: any, idx: number) => (
                  <li key={idx} style={{ marginBottom: "0.5rem" }}>
                    <strong>{conflict.severity.toUpperCase()}:</strong> {conflict.description}
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
