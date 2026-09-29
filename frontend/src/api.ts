import type { ChatProduct, ChatTurn, ProductDetail, ProductSummary, User } from './types'

const BASE = '/api'

export class ApiError extends Error {}

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) {
    throw new ApiError(`Request to ${path} failed: ${res.status}`)
  }
  return res.json() as Promise<T>
}

async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    throw new ApiError(data?.detail ?? `Request to ${path} failed: ${res.status}`)
  }
  return data as T
}

export function fetchProducts(): Promise<ProductSummary[]> {
  return getJSON('/products')
}

export function fetchProduct(productId: string): Promise<ProductDetail> {
  return getJSON(`/products/${encodeURIComponent(productId)}`)
}

export function signup(payload: {
  first_name: string
  last_name: string
  email: string
  password: string
}): Promise<User> {
  return postJSON('/auth/signup', payload)
}

export function login(payload: { email: string; password: string }): Promise<User> {
  return postJSON('/auth/login', payload)
}

export interface PageContext {
  product_id: string | null
}

export function sendChatMessage(
  message: string,
  history: ChatTurn[],
  user: User | null,
  pageContext: PageContext | null,
): Promise<{ reply: string; products: ChatProduct[] }> {
  return postJSON('/chat', { message, history, user, page_context: pageContext })
}

export interface ChatHistoryTurn {
  role: 'user' | 'assistant'
  content: string
  products: ChatProduct[]
}

export function fetchChatHistory(userId: number): Promise<{ messages: ChatHistoryTurn[] }> {
  return getJSON(`/chat/history?user_id=${encodeURIComponent(String(userId))}`)
}
