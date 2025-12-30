import React, { useState, useRef, useEffect } from 'react';
import { chatAPI } from '../services/api';
import './Chatbot.css';

function Chatbot() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      type: 'bot',
      text: 'Hi! I\'m your financial assistant . Ask me about your spending, income, or get financial advice!',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
  if (!input.trim() || loading) return;

  const userMessage = {
    type: 'user',
    text: input,
    timestamp: new Date()
  };

  setMessages(prev => [...prev, userMessage]);
  setInput('');
  setLoading(true);

  try {
    const response = await chatAPI.sendMessage(input);  // ← Use chatAPI
    
    const botMessage = {
      type: 'bot',
      text: response.data.response,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, botMessage]);
  } catch (error) {
    console.error('Chat error:', error);
    const errorMessage = {
      type: 'bot',
      text: 'Sorry, I encountered an error. Please try again.',
      timestamp: new Date()
    };
    setMessages(prev => [...prev, errorMessage]);
  } finally {
    setLoading(false);
  }
};

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const quickActions = [
    "What's my balance?",
    "Show my expenses",
    "Give me savings tips",
    "Budget advice"
  ];

  const handleQuickAction = (action) => {
    setInput(action);
  };

  return (
    <>
    {/* Chat Button - with inline styles for testing */}
    <button
      className="chat-toggle"
      onClick={() => setIsOpen(!isOpen)}
      style={{
        position: 'fixed',
        bottom: '30px',
        right: '30px',
        width: '60px',
        height: '60px',
        borderRadius: '50%',
        background: 'linear-gradient(135deg, #667eea 0%, #1014d4ff 100%)',
        border: 'none',
        fontSize: '24px',
        color: 'white',
        cursor: 'pointer',
        zIndex: '9999'
      }}
    >
      {isOpen ? '✖️' : '💬'}
    </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="chatbot-container">
          <div className="chat-header">
            <div className="chat-header-content">
              <span className="chat-icon"></span>
              <div>
                <h3>Financial Assistant</h3>
                <span className="chat-status">Online</span>
              </div>
            </div>
          </div>

          <div className="chat-messages">
            {messages.map((msg, index) => (
              <div key={index} className={`message ${msg.type}`}>
                <div className="message-content">
                  {msg.text}
                </div>
                <span className="message-time">
                  {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            ))}
            {loading && (
              <div className="message bot">
                <div className="message-content typing">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Actions */}
          <div className="quick-actions">
            {quickActions.map((action, index) => (
              <button
                key={index}
                className="quick-action-btn"
                onClick={() => handleQuickAction(action)}
              >
                {action}
              </button>
            ))}
          </div>

          <div className="chat-input-container">
            <input
              type="text"
              className="chat-input"
              placeholder="Ask me anything..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
            />
            <button
              className="send-button"
              onClick={handleSend}
              disabled={loading || !input.trim()}
            >
              {loading ? '⏳' : '➤'}
            </button>
          </div>
        </div>
      )}
    </>
  );
}

export default Chatbot;