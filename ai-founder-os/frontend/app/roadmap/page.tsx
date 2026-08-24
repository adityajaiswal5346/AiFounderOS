"use client";

import useSWR from "swr";
import { fetcher } from "../../lib/api";
import { Card, PageHeader, Badge } from "../../components/ui";

export default function RoadmapPage() {
  const { data, error, isLoading } = useSWR("/roadmap/", fetcher);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed": return <Badge variant="success">Completed</Badge>;
      case "running": return <Badge variant="primary">Running</Badge>;
      case "failed": return <Badge variant="danger">Failed</Badge>;
      default: return <Badge variant="warning">{status}</Badge>;
    }
  };

  return (
    <div style={{ animation: "fadeIn 0.5s ease-out" }}>
      <PageHeader 
        title="Roadmap & Task Queue" 
        subtitle="Current operating plan and active agent tasks." 
      />

      {isLoading && <p style={{ color: "var(--text-muted)" }}>Loading roadmap...</p>}
      {error && (
        <Card style={{ borderColor: "var(--danger)" }}>
          <p style={{ color: "var(--danger)" }}>Failed to load roadmap: {error.message}</p>
        </Card>
      )}

      {data && (
        <div style={{ display: "grid", gap: "2rem" }}>
          <Card className="glass-panel">
            <h2 style={{ fontSize: "1.25rem", fontWeight: "600", marginTop: 0, marginBottom: "1rem" }}>Current Plan</h2>
            {data.plan ? (
              <p style={{ color: "var(--text-primary)", whiteSpace: "pre-wrap", margin: 0 }}>{data.plan.plan_text}</p>
            ) : (
              <p style={{ color: "var(--text-muted)", margin: 0 }}>No active plan.</p>
            )}
          </Card>

          <div>
            <h2 style={{ fontSize: "1.25rem", fontWeight: "600", marginBottom: "1rem", color: "var(--text-primary)" }}>Tasks</h2>
            
            {data.tasks && data.tasks.length === 0 && (
              <p style={{ color: "var(--text-muted)" }}>No tasks in the queue.</p>
            )}

            <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
              {data.tasks && data.tasks.map((task: any) => (
                <Card key={task.id} style={{ display: "flex", alignItems: "flex-start", gap: "1.5rem", padding: "1.25rem" }}>
                  <div style={{ flexShrink: 0, width: "120px" }}>
                    <p style={{ margin: "0 0 0.5rem 0", fontWeight: "600", color: "var(--text-primary)", textTransform: "capitalize" }}>
                      {task.agent_name}
                    </p>
                    {getStatusBadge(task.status)}
                  </div>
                  
                  <div style={{ flex: 1 }}>
                    <p style={{ margin: "0 0 0.5rem 0", color: "var(--text-primary)", fontWeight: "500" }}>{task.description}</p>
                    {task.output && task.output.summary && (
                      <div style={{ backgroundColor: "rgba(0,0,0,0.1)", padding: "0.75rem", borderRadius: "var(--radius-sm)", marginTop: "0.5rem" }}>
                        <p style={{ margin: 0, fontSize: "0.875rem", color: "var(--text-secondary)" }}>
                          <strong>Outcome:</strong> {task.output.summary}
                        </p>
                      </div>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
