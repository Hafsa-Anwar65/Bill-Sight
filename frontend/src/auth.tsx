import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { getMe, signOut as apiSignOut, type User } from "./api";

interface AuthState {
  user: User | null;
  ready: boolean;
  setUser: (u: User | null) => void;
  signOut: () => Promise<void>;
  openAuth: (mode?: "signin" | "signup") => void;
  authMode: "signin" | "signup" | null;
  closeAuth: () => void;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);
  const [authMode, setAuthMode] = useState<"signin" | "signup" | null>(null);

  useEffect(() => {
    getMe().then((r) => setUser(r.user)).catch(() => setUser(null)).finally(() => setReady(true));
  }, []);

  const signOut = useCallback(async () => {
    try { await apiSignOut(); } finally { setUser(null); }
  }, []);

  return (
    <AuthContext.Provider value={{
      user, ready, setUser, signOut, authMode,
      openAuth: (mode = "signin") => setAuthMode(mode),
      closeAuth: () => setAuthMode(null),
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
