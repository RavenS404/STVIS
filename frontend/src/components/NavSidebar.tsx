import { NavLink } from "react-router-dom";

import { BRAND_NAME, BRAND_SHORT, BRAND_TAGLINE_AR } from "../app/presentation";
import type { UserRole } from "../app/types";

const baseLinks = [
  { to: "/", label: "لوحة القيادة" },
  { to: "/review", label: "طابور المراجعة" },
  { to: "/history", label: "السجل" },
  { to: "/reports", label: "التقارير" },
  { to: "/health", label: "الصحة" },
  { to: "/audit", label: "التدقيق" },
];

const adminLinks = [
  { to: "/settings", label: "الإعدادات" },
  { to: "/users", label: "المستخدمون" },
  { to: "/devices", label: "الأجهزة" },
];

export function NavSidebar({ role }: { role: UserRole }) {
  const links = role === "admin" ? [...baseLinks, ...adminLinks] : baseLinks;

  return (
    <aside className="sidebar surface">
      <div className="brand-block">
        <h2>{BRAND_SHORT}</h2>
        <p>{BRAND_TAGLINE_AR}</p>
      </div>
      <nav className="nav-list">
        {links.map((item) => (
          <NavLink key={item.to} to={item.to} className={({ isActive }) => `nav-link${isActive ? " nav-link--active" : ""}`}>
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
