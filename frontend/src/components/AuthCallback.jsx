import React, { useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';

const API_BASE = process.env.REACT_APP_BACKEND_URL || '';

export default function AuthCallback() {
  const location = useLocation();
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const hasProcessed = useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const hash = location.hash || '';
    const match = hash.match(/session_id=([^&]+)/);

    const search = location.search || '';
    const params = new URLSearchParams(search.startsWith('?') ? search.slice(1) : search);

    const sessionId = match
      ? decodeURIComponent(match[1])
      : (params.get('session_id') ? decodeURIComponent(params.get('session_id')) : null);

    const run = async () => {
      if (!sessionId) {
        navigate('/', { replace: true });
        return;
      }

      const res = await fetch(`${API_BASE}/api/auth/session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ session_id: sessionId }),
      });

      if (res.ok) {
        const u = await res.json();
        // On localhost, cookies may not persist; use header token fallback.
        if (u?.session_token) {
          window.localStorage.setItem('session_token', u.session_token);
        }
        setUser(u);
      }

      navigate('/', { replace: true });
    };

    run();
  }, [location.hash, location.search, navigate, setUser]);

  return null;
}
