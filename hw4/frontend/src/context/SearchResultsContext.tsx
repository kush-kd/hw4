import { createContext, useContext, useState, type ReactNode } from 'react'
import type { ChatProduct } from '../types'

interface SearchResults {
  query: string
  products: ChatProduct[]
}

interface SearchResultsContextValue {
  results: SearchResults | null
  setResults: (query: string, products: ChatProduct[]) => void
  clearResults: () => void
}

const SearchResultsContext = createContext<SearchResultsContextValue | null>(null)

export function SearchResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResultsState] = useState<SearchResults | null>(null)

  function setResults(query: string, products: ChatProduct[]) {
    setResultsState(products.length > 0 ? { query, products } : null)
  }

  function clearResults() {
    setResultsState(null)
  }

  return (
    <SearchResultsContext.Provider value={{ results, setResults, clearResults }}>
      {children}
    </SearchResultsContext.Provider>
  )
}

export function useSearchResults(): SearchResultsContextValue {
  const ctx = useContext(SearchResultsContext)
  if (!ctx) throw new Error('useSearchResults must be used within a SearchResultsProvider')
  return ctx
}
