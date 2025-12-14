import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';


// API base must come from env; all backend endpoints are prefixed with /api.

const AuthContext = createContext(null);

const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [team, setTeam] = useState(null);
  const [checking, setChecking] = useState(true);

  const login = () => {
    const redirectUrl = `${window.location.origin}/agents`;
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const logout = async () => {
    await fetch(`${API_BASE}/api/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    });
    setUser(null);
    setTeam(null);
  };

  const refreshTeam = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/team/me`, { credentials: 'include' });
      if (!res.ok) {
        setTeam(null);
        return;
      }
      const t = await res.json();
      setTeam(t);
    } catch {
      setTeam(null);
    }
  };

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/auth/me`, {
          credentials: 'include',
        });
        if (!res.ok) throw new Error('not authed');
        const u = await res.json();
        if (cancelled) return;
        setUser(u);
      } catch {
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setChecking(false);
      }
    };
    run();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!user) {
      setTeam(null);
      return;
    }
    refreshTeam();
  }, [user?.user_id]);

  const value = useMemo(
    () => ({
      user,
      team,
      setUser,
      setTeam,
      checking,
      login,
      logout,
      refreshTeam,
      isAuthenticated: !!user,
    }),
    [user, team, checking]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
