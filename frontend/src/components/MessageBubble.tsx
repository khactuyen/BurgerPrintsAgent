import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, User } from 'lucide-react';

interface MessageBubbleProps {
  role: 'user' | 'agent';
  content: string;
}

export default function MessageBubble({ role, content }: MessageBubbleProps) {
  const isUser = role === 'user';
  
  return (
    <div className={`animate-fade-in`} style={{
      display: 'flex',
      flexDirection: isUser ? 'row-reverse' : 'row',
      gap: '1rem',
      alignItems: 'flex-start',
      width: '100%'
    }}>
      {/* Avatar */}
      <div style={{
        width: '36px',
        height: '36px',
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: isUser ? 'var(--accent)' : 'var(--bg-glass-light)',
        border: isUser ? 'none' : '1px solid var(--border)',
        flexShrink: 0
      }}>
        {isUser ? <User size={20} color="white" /> : <Bot size={20} color="var(--accent)" />}
      </div>
      
      {/* Bubble */}
      <div className={isUser ? '' : 'glass-light'} style={{
        maxWidth: '80%',
        padding: '1rem 1.25rem',
        borderRadius: '1rem',
        borderTopRightRadius: isUser ? '0.25rem' : '1rem',
        borderTopLeftRadius: !isUser ? '0.25rem' : '1rem',
        background: isUser ? 'var(--bg-secondary)' : '',
        border: isUser ? '1px solid var(--border)' : '',
      }}>
        <div className="markdown-body" style={{ color: 'var(--text-primary)' }}>
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={{
              table: ({node, ...props}) => <div style={{ overflowX: 'auto', margin: '1rem 0' }}><table style={{ width: '100%', borderCollapse: 'collapse' }} {...props} /></div>,
              th: ({node, ...props}) => <th style={{ borderBottom: '2px solid var(--border)', padding: '0.75rem', textAlign: 'left', color: 'var(--accent)' }} {...props} />,
              td: ({node, ...props}) => <td style={{ borderBottom: '1px solid var(--border-light)', padding: '0.75rem' }} {...props} />,
              a: ({node, ...props}) => <a style={{ color: 'var(--accent)', textDecoration: 'none' }} {...props} />,
              p: ({node, ...props}) => <p style={{ marginBottom: '0.75rem' }} {...props} />,
              ul: ({node, ...props}) => <ul style={{ paddingLeft: '1.5rem', marginBottom: '0.75rem' }} {...props} />,
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
