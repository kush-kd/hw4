import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import * as api from '../api'
import type { User } from '../types'

const STORAGE_KEY = 'campus-customs-user'

interface AuthContextValue {
  user: User | null
  login: (email: string, password: string) => Promise<User>
  signup: (firstName: string, lastName: string, email: string, password: string) => Promise<User>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) setUser(JSON.parse(stored))
    } catch {
      // ignore malformed/blocked storage
    }
  }, [])

  function persist(nextUser: User) {
    setUser(nextUser)
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(nextUser))
    } catch {
      // ignore write failures (e.g. private browsing)
    }
  }

  async function login(email: string, password: string) {
    const loggedInUser = await api.login({ email, password })
    persist(loggedInUser)
    return loggedInUser
  }

  async function signup(firstName: string, lastName: string, email: string, password: string) {
    const newUser = await api.signup({ first_name: firstName, last_name: lastName, email, password })
    persist(newUser)
    return newUser
  }

  function logout() {
    setUser(null)
    try {
      localStorage.removeItem(STORAGE_KEY)
    } catch {
      // ignore
    }
  }

  return <AuthContext.Provider value={{ user, login, signup, logout }}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}
