import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext.tsx'
import { SearchResultsProvider } from './context/SearchResultsContext.tsx'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <AuthProvider>
        <SearchResultsProvider>
          <App />
        </SearchResultsProvider>
      </AuthProvider>
    </BrowserRouter>
  </StrictMode>,
)
