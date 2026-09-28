import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkAuth();
  }, []);

  async function checkAuth() {
    try {
      const data = await authAPI.me();
      setUser(data.user);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }

  async function login(email, password) {
    const data = await authAPI.login({ email, password });
    setUser(data.user);
    return data;
  }

  async function register(name, email, password, confirmPassword) {
    const data = await authAPI.register({ name, email, password, confirmPassword });
    setUser(data.user);
    return data;
  }

  async function logout() {
    await authAPI.logout();
    setUser(null);
  }

  async function updateProfile(profileData) {
    const data = await authAPI.updateProfile(profileData);
    setUser(data.user);
    return data;
  }

  async function refreshUser() {
    try {
      const data = await authAPI.me();
      setUser(data.user);
    } catch {
      /* ignore */
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, updateProfile, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
