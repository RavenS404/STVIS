import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { authTokenStorageKey } from "../services/api";
import { fetchCurrentUser, loginRequest } from "../services/auth";
import type { CurrentUser } from "../app/types";

interface AuthContextValue {
  user: CurrentUser | null;
  isBootstrapping: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [isBootstrapping, setIsBootstrapping] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem(authTokenStorageKey);
    if (!token) {
      setIsBootstrapping(false);
      return;
    }
    fetchCurrentUser()
      .then(setUser)
      .catch(() => {
        localStorage.removeItem(authTokenStorageKey);
        setUser(null);
      })
      .finally(() => setIsBootstrapping(false));
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isBootstrapping,
      async login(username: string, password: string) {
        const token = await loginRequest(username, password);
        localStorage.setItem(authTokenStorageKey, token.access_token);
        const nextUser = await fetchCurrentUser();
        setUser(nextUser);
      },
      logout() {
        localStorage.removeItem(authTokenStorageKey);
        setUser(null);
      },
    }),
    [user, isBootstrapping],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuthContext() {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuthContext must be used within AuthProvider");
  }
  return value;
}
