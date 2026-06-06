import React from 'react';

export default function StreamingIndicator() {
  return (
    <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', padding: '1rem', color: 'var(--text-muted)' }}>
      <div className="glass-light" style={{
        padding: '0.75rem 1rem',
        borderRadius: '1rem',
        borderBottomLeftRadius: '0.25rem',
        display: 'inline-block'
      }}>
        <span style={{ fontSize: '0.9rem', fontStyle: 'italic' }}>
          Đang suy nghĩ
          <span className="typing-animation" style={{ display: 'inline-block', width: '20px', textAlign: 'left' }}>
            ...
          </span>
        </span>
      </div>
      <style dangerouslySetInnerHTML={{__html: `
        .typing-animation {
          animation: typingDots 1.5s infinite;
        }
      `}} />
    </div>
  );
}
