import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';


// API base must come from env; all backend endpoints are prefixed with /api.

const AuthContext = createContext(null);

const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [team, setTeam] = useState(null);
  const [checking, setChecking] = useState(true);

  const login = (redirectPath = '/') => {
    // Force a clean session exchange each time we login.
    window.localStorage.removeItem('session_token');
    const redirectUrl = `${window.location.origin}${redirectPath}`;
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  const logout = async () => {
    const token = window.localStorage.getItem('session_token');
    await fetch(`${API_BASE}/api/auth/logout`, {
      method: 'POST',
      credentials: 'include',
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });
    window.localStorage.removeItem('session_token');
    setUser(null);
    setTeam(null);
  };

  const refreshUser = async () => {
    const token = window.localStorage.getItem('session_token');
    const res = await fetch(`${API_BASE}/api/auth/me`, {
      credentials: 'include',
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });
    if (!res.ok) {
      setUser(null);
      return null;
    }
    const u = await res.json();
    setUser(u);
    return u;
  };

  const refreshTeam = async () => {
    try {
      const token = window.localStorage.getItem('session_token');
      const res = await fetch(`${API_BASE}/api/team/me`, {
        credentials: 'include',
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      });
      if (!res.ok) {
        setTeam(null);
        return;
      }

  // After returning from Emergent auth, the browser may set cookies; refresh auth.

      const t = await res.json();
      setTeam(t);
    } catch {
      setTeam(null);
    }
  };

  useEffect(() => {
    // CRITICAL: If we are returning from Emergent auth, the URL may contain session_id
    // (either as hash or querystring). In that case, AuthCallback will exchange the session
    // and set user. Avoid racing it.
    if (
      window.location.hash?.includes('session_id=') ||
      window.location.search?.includes('session_id=')
    ) {
      setChecking(false);
      return;
    }

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
  }, [user]);

  const value = useMemo(
    () => ({
      user,
      team,
      setUser,
      setTeam,
      checking,
      login,
      logout,
      refreshUser,
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
