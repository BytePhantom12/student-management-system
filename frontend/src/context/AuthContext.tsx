import {useEffect, useState, type ReactNode} from 'react';
import {api} from '../services/api';
import type {User} from '../types';
import {AuthContext} from './auth';

export function AuthProvider({children}: {children: ReactNode}) {
  const hasStoredSession = Boolean(localStorage.getItem('access'));
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(hasStoredSession);

  useEffect(() => {
    if (!hasStoredSession) return;
    let active = true;
    api.get<User>('/auth/me/')
      .then(response => { if (active) setUser(response.data); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [hasStoredSession]);

  async function login(username: string, password: string) {
    const {data} = await api.post('/auth/login/', {username, password});
    localStorage.setItem('access', data.access);
    localStorage.setItem('refresh', data.refresh);
    setUser((await api.get<User>('/auth/me/')).data);
  }

  async function logout() {
    try {
      await api.post('/auth/logout/', {refresh: localStorage.getItem('refresh')});
    } finally {
      localStorage.clear();
      setUser(null);
    }
  }

  return <AuthContext.Provider value={{user, loading, login, logout}}>{children}</AuthContext.Provider>;
}
