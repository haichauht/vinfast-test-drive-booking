import React, { useState, useEffect, useRef } from 'react'

function App() {
  const [messages, setMessages] = useState([
    { text: 'Xin chào! Tôi là AI Agent kết hợp LangGraph. Tôi có thể giúp gì cho bạn hôm nay?', sender: 'agent', timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef(null)

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!inputValue.trim() || isLoading) return

    const userMessage = inputValue
    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    
    // Add user message
    setMessages(prev => [...prev, { text: userMessage, sender: 'user', timestamp }])
    setInputValue('')
    setIsLoading(true)

    try {
      const response = await fetch(`${apiUrl}/api/v1/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage }),
      })

      if (!response.ok) {
        throw new Error('API server returned error')
      }

      const data = await response.json()
      
      // Add agent reply
      setMessages(prev => [...prev, { 
        text: data.response || 'Không có phản hồi từ Agent.', 
        sender: 'agent', 
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        analysis: data.analysis 
      }])
    } catch (error) {
      console.error(error)
      setMessages(prev => [...prev, { 
        text: 'Lỗi: Không thể kết nối tới Backend API. Vui lòng kiểm tra server đang chạy ở port 8000.', 
        sender: 'agent', 
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
      }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <div>
          <h1 className="app-title">AI20K LangGraph Agent</h1>
        </div>
        <div className="status-badge">
          <span className="status-dot"></span>
          Agent v1.0 Connected
        </div>
      </header>

      <main className="messages-list">
        {messages.map((msg, index) => (
          <div key={index} className={`message-item ${msg.sender}`}>
            <div className="message-bubble">
              <div>{msg.text}</div>
              {msg.analysis && (
                <div style={{ 
                  marginTop: '0.5rem', 
                  padding: '0.4rem 0.6rem', 
                  fontSize: '0.8rem', 
                  background: 'rgba(255,255,255,0.03)', 
                  borderLeft: '2px solid #6366f1',
                  borderRadius: '4px',
                  color: 'rgba(255,255,255,0.6)'
                }}>
                  <strong>Suy nghĩ:</strong> {msg.analysis}
                </div>
              )}
            </div>
            <div className="message-meta">{msg.timestamp}</div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </main>

      <footer className="input-area">
        <form onSubmit={handleSubmit} className="input-form">
          <input
            type="text"
            className="chat-input"
            placeholder={isLoading ? "Agent đang suy nghĩ..." : "Nhập câu hỏi tại đây..."}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            disabled={isLoading}
          />
          <button type="submit" className="send-button" disabled={isLoading}>
            {isLoading ? 'Đang gửi...' : 'Gửi'}
          </button>
        </form>
      </footer>
    </div>
  )
}

export default App
