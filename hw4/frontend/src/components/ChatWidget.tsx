import { useEffect, useRef, useState, type CSSProperties, type FormEvent } from 'react'
import { useMatch } from 'react-router-dom'
import { ApiError, fetchChatHistory, sendChatMessage } from '../api'
import { useAuth } from '../context/AuthContext'
import { useSearchResults } from '../context/SearchResultsContext'
import type { ChatProduct, ChatTurn } from '../types'
import './ChatWidget.css'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  products?: ChatProduct[]
}

const GREETING: ChatMessage = {
  role: 'assistant',
  content: "Hi! I'm the Campus Customs assistant. Ask me about our merch.",
}

const SUGGESTIONS = ['Show me hoodies', 'What crewnecks do you have?', 'Anything under $40?']

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false)
  const [hasEverOpened, setHasEverOpened] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([GREETING])
  const [draft, setDraft] = useState('')
  const [isSending, setIsSending] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { results, setResults } = useSearchResults()
  const { user } = useAuth()
  const productPageMatch = useMatch('/products/:productId')

  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isOpen])

  // Problem 8: reload a logged-in shopper's saved history when they log in
  // (or on first load if already logged in); reset to a clean slate on
  // logout so the next person using this browser doesn't see someone else's
  // conversation.
  useEffect(() => {
    let cancelled = false
    if (!user) {
      setMessages([GREETING])
      return
    }
    fetchChatHistory(user.id)
      .then(({ messages: history }) => {
        if (cancelled) return
        setMessages(history.length > 0 ? history : [GREETING])
      })
      .catch(() => {
        if (!cancelled) setMessages([GREETING])
      })
    return () => {
      cancelled = true
    }
  }, [user?.id])

  async function sendMessage(text: string) {
    if (!text || isSending) return

    const nextMessages: ChatMessage[] = [...messages, { role: 'user', content: text }]
    setMessages(nextMessages)
    setDraft('')
    setIsSending(true)
    try {
      const history: ChatTurn[] = messages.map((m) => ({
        role: m.role,
        content: m.content,
        product_ids: m.products?.map((p) => p.product_id) ?? [],
      }))
      const pageContext = { product_id: productPageMatch?.params.productId ?? null }
      const { reply, products } = await sendChatMessage(text, history, user, pageContext)
      setMessages((prev) => [...prev, { role: 'assistant', content: reply, products }])
      // The real product cards render on the page itself (SearchResultsShelf),
      // not inside this small panel — see prompts/prompt.md and
      // output/harness.md for why.
      setResults(text, products)
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Sorry, I couldn't reach the shop assistant."
      setMessages((prev) => [...prev, { role: 'assistant', content: message }])
    } finally {
      setIsSending(false)
    }
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    sendMessage(draft.trim())
  }

  function toggleOpen() {
    setIsOpen((open) => !open)
    setHasEverOpened(true)
  }

  const widgetStyle = results
    ? ({ bottom: 'calc(var(--shelf-height) + 24px)', '--panel-reserved': 'calc(var(--shelf-height) + 112px)' } as CSSProperties)
    : undefined

  const showSuggestions = messages.length === 1 && messages[0] === GREETING && !isSending

  return (
    <div className="chat-widget" style={widgetStyle}>
      {isOpen && (
        <div className="chat-panel">
          <div className="chat-panel-header">
            <div className="chat-panel-title">
              <span className="chat-avatar">CC</span>
              <div>
                <p className="chat-panel-name">Campus Customs</p>
                <p className="chat-panel-status">{user ? `Chatting as ${user.first_name}` : 'Online'}</p>
              </div>
            </div>
            <button type="button" className="chat-close" onClick={() => setIsOpen(false)} aria-label="Close chat">
              ×
            </button>
          </div>
          <div className="chat-messages">
            {messages.map((message, index) => (
              <div key={index} className={`chat-bubble chat-bubble-${message.role}`}>
                {message.content}
                {message.products && message.products.length > 0 && (
                  <p className="chat-products-hint">
                    ↓ {message.products.length} matching {message.products.length === 1 ? 'item' : 'items'} shown on
                    the page
                  </p>
                )}
              </div>
            ))}
            {showSuggestions && (
              <div className="chat-suggestions">
                {SUGGESTIONS.map((suggestion) => (
                  <button key={suggestion} type="button" className="chat-suggestion-chip" onClick={() => sendMessage(suggestion)}>
                    {suggestion}
                  </button>
                ))}
              </div>
            )}
            {isSending && (
              <div className="chat-bubble chat-bubble-assistant chat-typing">
                <span />
                <span />
                <span />
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          <form className="chat-input-row" onSubmit={handleSubmit}>
            <input
              type="text"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              placeholder="Ask about a product..."
              disabled={isSending}
            />
            <button type="submit" disabled={isSending || !draft.trim()}>
              Send
            </button>
          </form>
        </div>
      )}
      <button
        type="button"
        className={`chat-toggle ${!hasEverOpened ? 'chat-toggle-invite' : ''}`}
        onClick={toggleOpen}
      >
        {isOpen ? '×' : '💬'}
      </button>
    </div>
  )
}
