import { createBrowserRouter, Navigate } from "react-router-dom";

import { AppLayout } from "../layouts/AppLayout";
import { AuthLayout } from "../layouts/AuthLayout";
import { AuditPage } from "../pages/AuditPage";
import { CaseDetailsPage } from "../pages/CaseDetailsPage";
import { DashboardPage } from "../pages/DashboardPage";
import { DevicesPage } from "../pages/DevicesPage";
import { HealthPage } from "../pages/HealthPage";
import { HistoryPage } from "../pages/HistoryPage";
import { LoginPage } from "../pages/LoginPage";
import { ReportsPage } from "../pages/ReportsPage";
import { ReviewQueuePage } from "../pages/ReviewQueuePage";
import { RouteErrorPage } from "../pages/RouteErrorPage";
import { SettingsPage } from "../pages/SettingsPage";
import { UsersPage } from "../pages/UsersPage";

export const router = createBrowserRouter([
  {
    path: "/login",
    element: <AuthLayout />,
    errorElement: <RouteErrorPage />,
    children: [{ index: true, element: <LoginPage /> }],
  },
  {
    path: "/",
    element: <AppLayout />,
    errorElement: <RouteErrorPage />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "review", element: <ReviewQueuePage /> },
      { path: "cases/:caseId", element: <CaseDetailsPage /> },
      { path: "history", element: <HistoryPage /> },
      { path: "reports", element: <ReportsPage /> },
      { path: "health", element: <HealthPage /> },
      { path: "audit", element: <AuditPage /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "users", element: <UsersPage /> },
      { path: "devices", element: <DevicesPage /> },
    ],
  },
  { path: "*", element: <Navigate to="/" replace /> },
]);
