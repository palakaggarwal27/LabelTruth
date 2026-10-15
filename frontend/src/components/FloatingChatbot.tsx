"use client";

import React, { useState } from 'react';
import { MessageSquare, X, Send, Bot } from 'lucide-react';
import { useHealthProfile } from '@/context/HealthProfileContext';
import { sendChatMessage } from '@/lib/api';
import { LabelAnalysisResult } from '@/types';

interface FloatingChatbotProps {
  activeProductContext?: LabelAnalysisResult | null;
}

export const FloatingChatbot: React.FC<FloatingChatbotProps> = ({ activeProductContext }) => {
  const { profile } = useHealthProfile();
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([
    {
      role: 'assistant',
      content: activeProductContext
        ? `Audit loaded for ${activeProductContext.product_name} (Score: ${activeProductContext.health_score}/100 — ${activeProductContext.personalized_verdict}). What would you like to know about its ingredients or health impact?`
        : 'Clinical food intelligence active. You can ask me follow-up questions about this product, your medical conditions, or FSSAI regulatory compliance.',
    },
  ]);

  // Update greeting when active scanned product changes
  React.useEffect(() => {
    if (activeProductContext) {
      setMessages((prev) => {
        // If user hasn't chatted yet or only has greeting, update to product-specific greeting
        if (prev.length <= 1) {
          return [
            {
              role: 'assistant',
              content: `Audit loaded for ${activeProductContext.product_name} (Score: ${activeProductContext.health_score}/100 — ${activeProductContext.personalized_verdict}). What would you like to know about its ingredients or health impact?`,
            },
          ];
        }
        return prev;
      });
    }
  }, [activeProductContext]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userText = input.trim();
    setInput('');
    const newHistory = [...messages, { role: 'user', content: userText }];
    setMessages(newHistory);
    setLoading(true);

    try {
      const reply = await sendChatMessage(userText, messages, profile, activeProductContext);
      setMessages([...newHistory, { role: 'assistant', content: reply }]);
    } catch (err) {
      console.error('Chat error:', err);
      setMessages([
        ...newHistory,
        {
          role: 'assistant',
          content:
            'Unable to communicate with the clinical analysis engine. Please ensure backend is running.',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-5 right-5 z-50">
      {/* Floating Toggle Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="p-3.5 bg-zinc-900 text-white rounded-md shadow-sm border border-zinc-700 hover:bg-zinc-800 transition-all flex items-center gap-2 text-xs font-semibold"
        >
          <MessageSquare className="w-4 h-4" />
          <span>Ask Nutritionist AI</span>
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div className="w-80 sm:w-96 h-[460px] bg-white border border-zinc-200 rounded-md shadow-sm flex flex-col overflow-hidden">
          {/* Header */}
          <div className="p-4 border-b border-zinc-200 bg-zinc-50 flex items-center justify-between">
            <div>
              <div className="text-xs font-semibold text-zinc-900 flex items-center gap-1.5">
                <Bot className="w-3.5 h-3.5 text-zinc-700" />
                <span>LabelTruth AI Assistant</span>
              </div>
              <div className="text-[10px] text-zinc-500 font-mono">
                {activeProductContext ? `Auditing: ${activeProductContext.product_name}` : 'Personalized health consultation'}
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1 text-zinc-400 hover:text-zinc-800 rounded transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Messages list */}
          <div className="flex-1 p-4 overflow-y-auto space-y-3 text-xs">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`flex gap-2 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`p-3 rounded-md max-w-[85%] leading-relaxed whitespace-pre-line ${
                    m.role === 'user'
                      ? 'bg-zinc-900 text-white'
                      : 'bg-zinc-100 text-zinc-800 border border-zinc-200'
                  }`}
                >
                  {m.content}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="p-2.5 rounded-md bg-zinc-100 text-zinc-500 text-xs italic">
                  Consulting clinical guidelines...
                </div>
              </div>
            )}
          </div>

          {/* Input form */}
          <form onSubmit={handleSend} className="p-3 border-t border-zinc-200 flex gap-2 bg-white">
            <input
              type="text"
              aria-label="Ask nutrition and FSSAI question"
              placeholder="E.g., Is maltodextrin safe for my diabetes?"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              className="flex-1 px-3 py-1.5 text-xs border border-zinc-200 rounded-md focus:outline-none focus:border-zinc-900"
            />
            <button
              type="submit"
              aria-label="Send message to Nutrition AI"
              disabled={loading || !input.trim()}
              className="p-2 bg-zinc-900 hover:bg-zinc-800 text-white rounded-md disabled:opacity-40"
            >
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      )}
    </div>
  );
};
