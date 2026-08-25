/**
 * AVENZO Business Web — Auth Context
 * Provides centralized authentication state, user profile, role checks, and login/logout methods.
 */

import React, { createContext, useState, useEffect, ReactNode } from 'react';
import { User, LoginRequest, UserRoleName } from '../types/auth';
import { loginApi, getMeApi, logoutApi } from '../api/auth.api';
import { getAccessToken } from '../api/client';

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => void;
  hasRole: (allowedRoles: UserRoleName[]) => boolean;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Initialize auth state on mount
  useEffect(() => {
    async function rehydrateUser() {
      const token = getAccessToken();
      if (!token) {
        setIsLoading(false);
        return;
      }
      try {
        const res = await getMeApi();
        if (res.success && res.data) {
          // Verify CONSUMER role rejection
          if (res.data.role?.name === 'CONSUMER') {
            logoutApi();
            setUser(null);
          } else {
            setUser(res.data);
          }
        } else {
          logoutApi();
          setUser(null);
        }
      } catch {
        logoutApi();
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    }

    rehydrateUser();
  }, []);

  const login = async (credentials: LoginRequest) => {
    setIsLoading(true);
    try {
      const loginRes = await loginApi(credentials);
      if (!loginRes.success || !loginRes.data) {
        throw new Error(loginRes.error?.message || 'Login failed. Please check your credentials.');
      }

      const meRes = await getMeApi();
      if (!meRes.success || !meRes.data) {
        logoutApi();
        throw new Error('Failed to retrieve user profile.');
      }

      // Check CONSUMER role restriction
      if (meRes.data.role?.name === 'CONSUMER') {
        logoutApi();
        throw new Error('Access denied. Consumer role accounts must use the Avenzo Consumer Mobile App.');
      }

      setUser(meRes.data);
    } catch (err: unknown) {
      logoutApi();
      setUser(null);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    logoutApi();
    setUser(null);
  };

  const hasRole = (allowedRoles: UserRoleName[]): boolean => {
    if (!user || !user.role) return false;
    return allowedRoles.includes(user.role.name);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        hasRole,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextType {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
