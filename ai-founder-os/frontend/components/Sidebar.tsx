"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, CheckSquare, Map, BrainCircuit } from "lucide-react";
import clsx from "clsx";

export function Sidebar() {
  const pathname = usePathname();

  const links = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "Approvals", href: "/approvals", icon: CheckSquare },
    { name: "Roadmap", href: "/roadmap", icon: Map },
    { name: "Company Brain", href: "/company-brain", icon: BrainCircuit },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div style={{
          width: '32px', height: '32px', borderRadius: '8px', 
          background: 'linear-gradient(135deg, #A78BFA 0%, #6366F1 100%)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 0 15px rgba(139, 92, 246, 0.5)'
        }}>
          <BrainCircuit size={18} color="white" />
        </div>
        <span>Founder OS</span>
      </div>
      <nav className="sidebar-nav">
        {links.map((link) => {
          const Icon = link.icon;
          const isActive = pathname.startsWith(link.href);
          return (
            <Link
              key={link.name}
              href={link.href}
              className={clsx("nav-link", { active: isActive })}
            >
              <Icon size={20} />
              {link.name}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
