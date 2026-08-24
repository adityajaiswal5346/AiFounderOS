"use client";

import useSWR from "swr";
import { fetcher, postApi } from "../../lib/api";
import { Card, PageHeader, Badge, Button } from "../../components/ui";

export default function ApprovalsPage() {
  const { data, error, isLoading, mutate } = useSWR("/approvals/pending", fetcher);

  const handleDecision = async (id: string, decision: "approve" | "reject") => {
    try {
      await postApi(`/approvals/${id}/decide`, { decision });
      // Remove from optimistic UI
      mutate({
        ...data,
        approvals: data.approvals.filter((a: any) => a.id !== id)
      }, false);
    } catch (err) {
      alert("Failed to record decision.");
    }
  };

  return (
    <div style={{ animation: "fadeIn 0.5s ease-out" }}>
      <PageHeader 
        title="Pending Approvals" 
        subtitle="Review and authorize actions requested by specialist agents." 
      />

      {isLoading && <p style={{ color: "var(--text-muted)" }}>Loading approvals...</p>}
      {error && (
        <Card style={{ borderColor: "var(--danger)" }}>
          <p style={{ color: "var(--danger)" }}>Failed to load approvals: {error.message}</p>
        </Card>
      )}

      {data && data.approvals && data.approvals.length === 0 && (
        <Card style={{ textAlign: "center", padding: "3rem 1rem", borderStyle: "dashed" }}>
          <p style={{ color: "var(--text-muted)" }}>No pending approvals.</p>
        </Card>
      )}

      <div style={{ display: "grid", gap: "1.5rem" }}>
        {data && data.approvals && data.approvals.map((approval: any) => (
          <Card key={approval.id} className="glass-panel" style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div>
                <h3 style={{ margin: "0 0 0.25rem 0", fontSize: "1.125rem", color: "var(--text-primary)" }}>
                  {approval.tool_name}
                </h3>
                <p style={{ margin: 0, fontSize: "0.875rem", color: "var(--text-secondary)" }}>
                  Task ID: {approval.task_id}
                </p>
              </div>
              <Badge variant="warning">Requires Action</Badge>
            </div>
            
            <div style={{ backgroundColor: "rgba(0,0,0,0.2)", padding: "1rem", borderRadius: "var(--radius-md)", overflowX: "auto" }}>
              <pre style={{ margin: 0, fontSize: "0.875rem", color: "var(--text-primary)" }}>
                {JSON.stringify(approval.tool_input, null, 2)}
              </pre>
            </div>

            <div style={{ display: "flex", gap: "1rem", justifyContent: "flex-end", marginTop: "0.5rem" }}>
              <Button variant="danger" onClick={() => handleDecision(approval.id, "reject")}>Reject</Button>
              <Button variant="primary" onClick={() => handleDecision(approval.id, "approve")}>Approve Action</Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
