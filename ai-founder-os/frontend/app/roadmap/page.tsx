"use client";

import { useState, useEffect } from "react";

interface RoadmapItem {
  title: string;
  status: string;
  notes?: string;
}

interface RoadmapSection {
  section: string;
  items: RoadmapItem[];
}

interface RoadmapData {
  sections: RoadmapSection[];
  last_updated: string;
}

export default function RoadmapPage() {
  const [roadmap, setRoadmap] = useState<RoadmapData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchRoadmap() {
      try {
        const response = await fetch("http://localhost:8000/api/roadmap/");
        const data = await response.json();
        setRoadmap(data);
      } catch (err) {
        console.error("Failed to fetch roadmap:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchRoadmap();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-500">Loading roadmap...</p>
      </div>
    );
  }

  if (!roadmap) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-500">Failed to load roadmap</p>
      </div>
    );
  }

  const statusColors: Record<string, string> = {
    built: "bg-green-100 text-green-800 border-green-300",
    planned: "bg-blue-100 text-blue-800 border-blue-300",
    stub: "bg-gray-100 text-gray-800 border-gray-300",
  };

  return (
    <div className="max-w-5xl mx-auto p-6">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Project Roadmap</h1>
        <p className="text-gray-600 text-sm mt-1">Last updated: {roadmap.last_updated}</p>
      </header>

      <div className="space-y-8">
        {roadmap.sections.map((section) => (
          <div key={section.section}>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">{section.section}</h2>
            <div className="space-y-2">
              {section.items.map((item, idx) => (
                <div
                  key={idx}
                  className="bg-white shadow-sm rounded-lg p-4 border border-gray-200 flex items-start justify-between"
                >
                  <div className="flex-1">
                    <p className="text-gray-900 font-medium">{item.title}</p>
                    {item.notes && <p className="text-gray-500 text-sm mt-1">{item.notes}</p>}
                  </div>
                  <span
                    className={`ml-4 px-3 py-1 text-xs font-semibold border rounded-full ${
                      statusColors[item.status] || "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {item.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
