'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Send, Menu, Plus } from 'lucide-react';
import MessageBubble from '@/components/MessageBubble';
import QuickPrompts from '@/components/QuickPrompts';
import StreamingIndicator from '@/components/StreamingIndicator';
import { generateSessionId } from '@/lib/api';

type Message = {
  id: string;
  role: 'user' | 'agent';
  content: string;
};

export default function ChatPage() {
  const [sessionId, setSessionId] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Init session on first load
    setSessionId(generateSessionId());
    
    // Auto-welcome message
    setMessages([
      {
        id: 'welcome',
        role: 'agent',
        content: '👋 Chào bạn! Tôi là **BurgerPrintsAgent**.\n\nTôi có thể giúp bạn tìm kiếm sản phẩm, so sánh xưởng fulfillment, và tính toán lợi nhuận. Bạn muốn tìm sản phẩm gì hôm nay?'
      }
    ]);
  }, []);

  useEffect(() => {
    // Scroll to bottom when messages change
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading]);

  const handleSend = async (text: string = inputValue) => {
    if (!text.trim() || isLoading) return;

    const activeSessionId = sessionId || generateSessionId();
    if (!sessionId) {
      setSessionId(activeSessionId);
    }
    
    const userMsgId = Date.now().toString();
    const agentMsgId = (Date.now() + 1).toString();
    
    // Add user message
    setMessages(prev => [...prev, { id: userMsgId, role: 'user', content: text }]);
    setInputValue('');
    setIsLoading(true);

    try {
      const url = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${url}/api/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: text,
          session_id: activeSessionId
        }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      
      if (!response.body) {
        throw new Error('No response body');
      }

      // Add empty agent message that we will stream into
      setMessages(prev => [...prev, { id: agentMsgId, role: 'agent', content: '' }]);
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      
      let done = false;
      let streamedContent = '';
      let eventBuffer = '';
      
      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        
        if (value) {
          eventBuffer += decoder.decode(value, { stream: true });
          const events = eventBuffer.split(/(?:\r?\n){2}/);
          eventBuffer = events.pop() || '';
          
          for (const event of events) {
            const dataStr = event
              .split('\n')
              .filter(line => line.startsWith('data:'))
              .map(line => line.replace(/^data:\s?/, ''))
              .join('\n')
              .trim();

            if (dataStr) {
              if (dataStr === '[DONE]') {
                done = true;
                break;
              }
              try {
                const data = JSON.parse(dataStr);
                if (data.text) {
                  streamedContent += data.text;
                  setMessages(prev => 
                    prev.map(msg => 
                      msg.id === agentMsgId 
                        ? { ...msg, content: streamedContent }
                        : msg
                    )
                  );
                } else if (data.error) {
                  streamedContent += `\n\n**Lỗi:** ${data.error}`;
                  setMessages(prev => 
                    prev.map(msg => 
                      msg.id === agentMsgId 
                        ? { ...msg, content: streamedContent }
                        : msg
                    )
                  );
                }
              } catch (e) {
                console.error('Invalid SSE payload:', dataStr, e);
              }
            }
          }
        }
      }

      if (!streamedContent) {
        setMessages(prev =>
          prev.map(msg =>
            msg.id === agentMsgId
              ? { ...msg, content: '**Lỗi:** Server kết thúc phản hồi nhưng không gửi nội dung.' }
              : msg
          )
        );
      }
    } catch (error) {
      console.error('Error fetching stream:', error);
      setMessages(prev => [...prev, { 
        id: Date.now().toString(), 
        role: 'agent', 
        content: 'Xin lỗi, đã có lỗi kết nối đến server. Vui lòng kiểm tra lại backend (đảm bảo đang chạy ở port 8000).' 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className={`sidebar ${isSidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div className="icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
            </svg>
          </div>
          <h1>BurgerPrints</h1>
        </div>
        
        <button className="glass-light" style={{
          display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.75rem 1rem',
          borderRadius: '0.5rem', color: 'var(--text-primary)', border: '1px solid var(--border)',
          cursor: 'pointer', background: 'transparent', transition: 'all 0.2s'
        }} onClick={() => {
          setSessionId(generateSessionId());
          setMessages([{
            id: 'welcome',
            role: 'agent',
            content: 'Đã tạo phiên chat mới. Bạn cần hỗ trợ gì?'
          }]);
        }}>
          <Plus size={18} />
          <span>New Chat</span>
        </button>

        <QuickPrompts onSelect={(prompt) => handleSend(prompt)} />
      </div>

      {/* Main Chat Area */}
      <div className="main-content">
        {/* Mobile Header */}
        <div style={{ display: 'flex', alignItems: 'center', padding: '1rem', borderBottom: '1px solid var(--border)', background: 'var(--bg-secondary)' }} className="md:hidden">
          <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} style={{ background: 'transparent', border: 'none', color: 'var(--text-primary)' }}>
            <Menu size={24} />
          </button>
          <h2 style={{ marginLeft: '1rem', fontSize: '1.1rem', fontWeight: 600 }}>BurgerPrintsAgent</h2>
        </div>

        <div className="chat-window" ref={scrollContainerRef}>
          {messages.map(msg => (
            <MessageBubble key={msg.id} role={msg.role} content={msg.content} />
          ))}
          {isLoading && <StreamingIndicator />}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-area">
          <div className="input-container glass">
            <input
              type="text"
              className="chat-input"
              placeholder="Hỏi về sản phẩm, giá, so sánh xưởng..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
            />
            <button 
              className="send-button"
              onClick={() => handleSend()}
              disabled={!inputValue.trim() || isLoading}
            >
              <Send size={18} />
            </button>
          </div>
          <div style={{ textAlign: 'center', marginTop: '0.75rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            AI Agent có thể mắc lỗi. Vui lòng kiểm tra lại thông tin quan trọng.
          </div>
        </div>
      </div>
    </div>
  );
}
