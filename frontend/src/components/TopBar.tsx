import { BRAND_SHORT, translateRole } from "../app/presentation";
import { useAuth } from "../hooks/useAuth";

export function TopBar() {
  const { user, logout } = useAuth();

  return (
    <header className="topbar surface">
      <div>
        <span className="eyebrow">{BRAND_SHORT}</span>
        <strong>{translateRole(user?.role)}</strong>
      </div>
      <div className="topbar__actions">
        <div className="user-pill">
          <span>{user?.full_name}</span>
          <small>{user?.username}</small>
        </div>
        <button className="ghost-button" onClick={logout} type="button">
          تسجيل الخروج
        </button>
      </div>
    </header>
  );
}
