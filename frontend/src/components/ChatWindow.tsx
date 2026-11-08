import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, SlidersHorizontal, Loader2 } from 'lucide-react';
import { Message } from '../types/sage';
import { MessageBubble } from './MessageBubble';

interface ChatWindowProps {
  messages: Message[];
  onSendMessage: (content: string) => void;
  isLoading: boolean;
  onToggleInspector: () => void;
  inspectorOpen: boolean;
}

const QUICK_TEST_PROMPTS = [
  "My prompt keeps giving inconsistent answers. Can you just fix it?",
  "No, I didn't specify any format instruction.",
  "What if I make the prompt longer by adding more descriptive adjectives?",
  "I should specify an explicit JSON format schema with boundary delimiters.",
];

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  onSendMessage,
  isLoading,
  onToggleInspector,
  inspectorOpen,
}) => {
  const [input, setInput] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-900 overflow-hidden relative">
      {/* Top Header */}
      <header className="h-14 border-b border-slate-800 px-6 flex items-center justify-between bg-slate-900/80 backdrop-blur-sm z-10">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-sm font-semibold text-slate-200">Active Socratic Session</span>
        </div>

        <button
          onClick={onToggleInspector}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
            inspectorOpen
              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
              : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border border-slate-700'
          }`}
          title="Toggle Evaluator Inspector Drawer"
        >
          <SlidersHorizontal className="w-3.5 h-3.5" />
          <span>{inspectorOpen ? 'Hide Inspector' : 'X-Ray State Inspector'}</span>
        </button>
      </header>

      {/* Message List */}
      <div className="flex-1 overflow-y-auto px-6 py-6">
        <div className="max-w-3xl mx-auto">
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex items-center space-x-3 text-slate-400 text-xs py-2">
              <div className="w-8 h-8 rounded-full bg-emerald-950/60 border border-emerald-500/20 flex items-center justify-center">
                <Loader2 className="w-4 h-4 animate-spin text-emerald-400" />
              </div>
              <span>SAGE is reasoning and consulting course materials...</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area & Quick Prompts */}
      <div className="border-t border-slate-800 bg-slate-950/70 p-4">
        <div className="max-w-3xl mx-auto space-y-3">
          {/* Quick Test Scenarios Bar */}
          <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
            <span className="text-[11px] font-semibold text-slate-500 flex items-center gap-1 shrink-0">
              <Sparkles className="w-3 h-3 text-emerald-400" /> Demo Prompts:
            </span>
            {QUICK_TEST_PROMPTS.map((prompt, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setInput(prompt)}
                disabled={isLoading}
                className="shrink-0 px-2.5 py-1 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700/60 text-[11px] truncate max-w-xs transition-colors disabled:opacity-50"
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Chat Form */}
          <form onSubmit={handleSubmit} className="flex items-end gap-2">
            <div className="flex-1 relative">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask a question, paste a prompt, or test your reasoning... (Enter to send, Shift+Enter for newline)"
                rows={2}
                disabled={isLoading}
                className="w-full bg-slate-900 border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500/80 focus:ring-1 focus:ring-emerald-500/50 resize-none transition-all disabled:opacity-50"
              />
            </div>

            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="h-11 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 disabled:text-slate-600 text-white font-medium text-sm flex items-center justify-center transition-all shadow-md shrink-0"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
