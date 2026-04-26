import { Navigate, Outlet } from "react-router-dom";

import { LoadingBlock } from "../components/LoadingBlock";
import { NavSidebar } from "../components/NavSidebar";
import { TopBar } from "../components/TopBar";
import { useAuth } from "../hooks/useAuth";

export function AppLayout() {
  const { user, isBootstrapping } = useAuth();

  if (isBootstrapping) return <LoadingBlock label="جارٍ تهيئة الجلسة..." />;
  if (!user) return <Navigate to="/login" replace />;

  return (
    <div className="app-shell">
      <NavSidebar role={user.role} />
      <div className="content-shell">
        <TopBar />
        <Outlet />
      </div>
    </div>
  );
}
