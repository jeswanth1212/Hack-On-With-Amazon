import React, { useState, useRef, useEffect } from 'react';
import Image from 'next/image';

// Alexa SVG icon as a React component
function AlexaIcon({ size = 36, className = '', style }: { size?: number; className?: string; style?: React.CSSProperties }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width={size} height={size} fill="currentColor" viewBox="0 0 16 16" className={className} style={style}>
      <path d="M7.996 0A8 8 0 0 0 0 8a8 8 0 0 0 6.93 7.93v-1.613a1.06 1.06 0 0 0-.717-1.008A5.6 5.6 0 0 1 2.4 7.865 5.58 5.58 0 0 1 8.054 2.4a5.6 5.6 0 0 1 5.535 5.81l-.002.046-.012.192-.005.061a5 5 0 0 1-.033.284l-.01.068c-.685 4.516-6.564 7.054-6.596 7.068A7.998 7.998 0 0 0 15.992 8 8 8 0 0 0 7.996.001Z" />
    </svg>
  );
}

const initialMessages = [
  {
    from: 'bot',
    text: "Hi! I'm your Movie Assistant. Ask me for recommendations, info, or help navigating the app!"
  }
];

interface ChatbotProps {
  zIndex?: number;
}

export default function Chatbot({ zIndex = 50 }: ChatbotProps) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState(initialMessages);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // For Gemini API: maintain full message history in Gemini format
  type GeminiRole = 'user' | 'assistant';
  interface GeminiMessage { role: GeminiRole; content: string; }
  const [geminiHistory, setGeminiHistory] = useState<GeminiMessage[]>([]);

  useEffect(() => {
    if (open && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, open]);

  const handleSend = async () => {
    if (!input.trim()) return;
    setError(null);
    const userMsg = { from: 'user', text: input };
    setMessages((msgs) => [...msgs, userMsg]);
    setInput('');
    setLoading(true);
    // Add to Gemini history
    const newHistory: GeminiMessage[] = [...geminiHistory, { role: 'user', content: input }];
    setGeminiHistory(newHistory);
    try {
      const res = await fetch('/api/gemini-chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: newHistory }),
      });
      if (!res.ok) throw new Error('Failed to get reply');
      const data = await res.json();
      if (data.error) throw new Error(data.error);
      const reply = data.reply || 'Sorry, I could not generate a reply.';
      setMessages((msgs) => [...msgs, { from: 'bot', text: reply }]);
      setGeminiHistory((hist) => [...hist, { role: 'assistant', content: reply }]);
    } catch (e: any) {
      setMessages((msgs) => [...msgs, { from: 'bot', text: 'Sorry, there was an error. Please try again.' }]);
      setError(e.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {/* Floating Alexa button */}
      <button
        className={`fixed bottom-6 right-6 flex items-center justify-center transition-all duration-200 focus:outline-none z-[1000] isolate`}
        style={{ background: 'transparent', boxShadow: '0 4px 24px rgba(0,0,0,0.25)', zIndex }}
        onClick={() => setOpen((v) => !v)}
        aria-label="Open Movie Assistant"
      >
        <AlexaIcon
          size={44}
          className="text-white"
          style={{ filter: 'drop-shadow(0 0 0.25rem #3b82f6) drop-shadow(0 0 0.5rem #3b82f6)' }}
        />
      </button>
      {/* Chat window */}
      {open && (
        <div className={`fixed bottom-24 right-6 w-[350px] max-w-[95vw] bg-[#181c24] rounded-2xl shadow-2xl flex flex-col border border-blue-700 animate-in fade-in slide-in-from-bottom duration-300 z-[1000] isolate`}
          style={{ zIndex }}>
          {/* Header */}
          <div className="flex items-center gap-2 px-4 py-3 border-b border-blue-700 bg-[#1e2230] rounded-t-2xl">
            <AlexaIcon size={28} className="text-blue-400" />
            <span className="font-bold text-lg text-blue-400">Fire TV Assistant</span>
            <button className="ml-auto text-gray-400 hover:text-white" onClick={() => setOpen(false)} aria-label="Close chat">✕</button>
          </div>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3 bg-[#181c24] scrollbar-custom" style={{ maxHeight: 400 }}>
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.from === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.from === 'bot' && (
                  <span className="mr-2 flex items-center justify-center" style={{ width: 24, height: 24 }}>
                    <AlexaIcon size={20} className="text-white" />
                  </span>
                )}
                <div
                  className={`rounded-xl px-4 py-2 max-w-[80%] text-sm shadow-md ${
                    msg.from === 'bot'
                      ? 'bg-[#23283a] text-white'
                      : 'bg-gray-800 text-gray-100'
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start items-center gap-2">
                <span className="mr-2 flex items-center justify-center" style={{ width: 24, height: 24 }}>
                  <AlexaIcon size={20} className="text-white" />
                </span>
                <div className="rounded-xl px-4 py-2 bg-[#23283a] text-white text-sm shadow-md animate-pulse">
                  Alexa is typing...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
          {/* Input */}
          <form
            className="flex items-center gap-2 px-4 py-3 border-t border-blue-700 bg-[#1e2230] rounded-b-2xl"
            onSubmit={e => { e.preventDefault(); handleSend(); }}
          >
            <input
              className="flex-1 rounded-lg bg-[#23283a] text-white px-3 py-2 outline-none border border-transparent focus:border-blue-500 transition-all"
              placeholder="Ask me anything..."
              value={input}
              onChange={e => setInput(e.target.value)}
              autoFocus
            />
            <button
              type="submit"
              className="bg-blue-600 hover:bg-blue-700 text-white rounded-lg px-4 py-2 font-semibold transition-all"
              disabled={loading || !input.trim()}
            >
              Send
            </button>
          </form>
          {error && <div className="text-red-400 text-xs px-4 pb-2">{error}</div>}
        </div>
      )}
      <style jsx>{`
        .scrollbar-custom {
          scrollbar-width: none;
          -ms-overflow-style: none;
        }
        .scrollbar-custom::-webkit-scrollbar {
          display: none;
        }
      `}</style>
    </>
  );
} 