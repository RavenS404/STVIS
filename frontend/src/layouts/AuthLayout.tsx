import { Outlet } from "react-router-dom";

import { BRAND_NAME, BRAND_SHORT, BRAND_TAGLINE_AR } from "../app/presentation";

export function AuthLayout() {
  return (
    <main className="auth-shell">
      <section className="auth-hero">
        <span className="brand-chip">{BRAND_SHORT}</span>
        <h1>{BRAND_NAME}</h1>
        <p>{BRAND_TAGLINE_AR}</p>
      </section>
      <section className="auth-form-wrapper">
        <Outlet />
      </section>
    </main>
  );
}
