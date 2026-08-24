import Link from "next/link";
import "./globals.css";
import { Sidebar } from "../components/Sidebar";

export const metadata = {
  title: "AI Founder OS",
  description: "Autonomous multi-agent OS for early-stage startups",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="app-layout">
          <Sidebar />
          <main className="main-content">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
