import Link from "next/link";
import "./globals.css";

export const metadata = {
  title: "AI Founder OS",
  description: "Autonomous multi-agent OS for early-stage startups",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-50 min-h-screen">
        <nav className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <Link href="/dashboard" className="text-xl font-bold text-gray-900">
              AI Founder OS
            </Link>
            <div className="flex gap-6">
              <Link href="/dashboard" className="text-gray-700 hover:text-gray-900 font-medium">
                Dashboard
              </Link>
              <Link href="/approvals" className="text-gray-700 hover:text-gray-900 font-medium">
                Approvals
              </Link>
              <Link href="/roadmap" className="text-gray-700 hover:text-gray-900 font-medium">
                Roadmap
              </Link>
              <Link href="/company-brain" className="text-gray-700 hover:text-gray-900 font-medium">
                Company Brain
              </Link>
            </div>
          </div>
        </nav>
        {children}
      </body>
    </html>
  );
}
