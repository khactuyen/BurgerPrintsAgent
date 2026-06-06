export async function sendMessageSync(sessionId: string, message: string) {
  const url = getApiBaseUrl();
  const res = await fetch(`${url}/api/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message, session_id: sessionId }),
  });
  
  if (!res.ok) {
    throw new Error('Failed to send message');
  }
  return res.json();
}

export function getApiBaseUrl(): string {
  const configuredUrl = process.env.NEXT_PUBLIC_API_URL;
  if (configuredUrl && !configuredUrl.includes('localhost')) {
    return configuredUrl;
  }

  if (typeof window !== 'undefined') {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }

  return configuredUrl || 'http://localhost:8000';
}

export function generateSessionId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  // Fallback for older browsers
  return 'sess-' + Math.random().toString(36).substring(2, 15);
}
