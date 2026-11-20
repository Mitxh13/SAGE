import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Sparkles,
  SlidersHorizontal,
  Loader2,
  Plus,
  HelpCircle,
  Lightbulb,
  Code,
  Compass,
} from 'lucide-react';
import { Message, UnitSummary } from '../types/sage';
import { MessageBubble } from './MessageBubble';

interface ChatWindowProps {
  messages: Message[];
  onSendMessage: (content: string) => void;
  isLoading: boolean;
  onToggleInspector: () => void;
  inspectorOpen: boolean;
  activeUnitTitle?: string;
  units: UnitSummary[];
  selectedUnitId: string;
  onSelectUnit: (unitId: string) => void;
}

const QUICK_TEST_PROMPTS = [
  {
    icon: HelpCircle,
    label: "Ask for direct fix",
    prompt: "My prompt keeps giving inconsistent answers. Can you just fix it?",
  },
  {
    icon: Lightbulb,
    label: "Reflect on format",
    prompt: "No, I just asked the question directly without any format.",
  },
  {
    icon: Compass,
    label: "Explore temperature",
    prompt: "Why does setting temperature=0 not guarantee complete factual accuracy?",
  },
  {
    icon: Code,
    label: "Synthesize correct fix",
    prompt: "I should specify an explicit JSON format schema with boundary delimiters.",
  },
];

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  onSendMessage,
  isLoading,
  onToggleInspector,
  inspectorOpen,
  activeUnitTitle,
  units,
  selectedUnitId,
  onSelectUnit,
}) => {
  const [input, setInput] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleQuickPromptClick = (promptText: string) => {
    if (isLoading) return;
    onSendMessage(promptText);
  };

  const isDialogueEmpty = messages.length === 0;

  return (
    <div className="flex-1 flex flex-col h-full bg-gemini-900 overflow-hidden relative font-sans">
      {/* 1. Sleek Top Bar (Gemini Style) */}
      <header className="h-16 px-6 flex items-center justify-between border-b border-gemini-800/80 bg-gemini-900/90 backdrop-blur-md z-10">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-gemini-200">
              {activeUnitTitle || "Prompt Engineering & GenAI"}
            </span>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center space-x-2.5">
          <button
            onClick={onToggleInspector}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-medium transition-all shadow-sm ${
              inspectorOpen
                ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 text-blue-300 border border-blue-500/40 shadow-glow-blue'
                : 'bg-gemini-800 text-gemini-300 hover:bg-gemini-700 hover:text-gemini-100 border border-gemini-700'
            }`}
            title="Toggle Live Pedagogical Telemetry Drawer"
          >
            <SlidersHorizontal className="w-3.5 h-3.5 text-blue-400" />
            <span>X-Ray Inspector</span>
            {inspectorOpen && (
              <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></span>
            )}
          </button>
        </div>
      </header>

      {/* 2. Main Content Canvas */}
      <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 relative">
        <div className="max-w-3xl mx-auto h-full flex flex-col">
          {/* Empty / Welcome State with Ambient Warm Glow (Like User's Gemini Screenshot) */}
          {isDialogueEmpty ? (
            <div className="flex-1 flex flex-col items-center justify-center text-center px-4 relative gemini-ambient-bg py-12">
              {/* Centered Sparkle Star */}
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-blue-500 via-purple-500 to-amber-500 p-0.5 shadow-2xl mb-6 hover:scale-105 transition-transform duration-300">
                <div className="w-full h-full bg-gemini-900 rounded-[14px] flex items-center justify-center">
                  <Sparkles className="w-8 h-8 text-amber-300 animate-pulse" />
                </div>
              </div>

              {/* Friendly Greeting Header */}
              <h2 className="text-3xl md:text-4xl font-normal text-gemini-100 tracking-tight mb-2">
                Welcome to <span className="font-semibold gemini-sparkle-gradient">SAGE</span>
              </h2>
              <p className="text-gemini-400 text-sm md:text-base max-w-md mb-8 leading-relaxed">
                Your AI Socratic tutor for Generative AI and Prompt Engineering. Ask a question or explore a concept.
              </p>

              {/* Sample Prompt Chips (Below Header) */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-xl">
                {QUICK_TEST_PROMPTS.map((item, idx) => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={idx}
                      onClick={() => handleQuickPromptClick(item.prompt)}
                      className="p-3.5 rounded-2xl bg-gemini-800/80 hover:bg-gemini-750 border border-gemini-700/60 text-left transition-all hover:scale-[1.01] hover:border-gemini-600 shadow-sm group"
                    >
                      <div className="flex items-center space-x-2.5 mb-1 text-gemini-300 group-hover:text-amber-300 transition-colors">
                        <Icon className="w-4 h-4" />
                        <span className="text-xs font-semibold">{item.label}</span>
                      </div>
                      <p className="text-xs text-gemini-400 line-clamp-2 leading-relaxed">
                        "{item.prompt}"
                      </p>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            <div className="space-y-2 flex-1 pb-4">
              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}

              {/* Thinking / Loading Animation */}
              {isLoading && (
                <div className="flex items-center space-x-3 text-gemini-400 text-xs py-3 px-2 animate-pulse">
                  <div className="w-7 h-7 rounded-full bg-gemini-800 border border-gemini-700 flex items-center justify-center">
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-400" />
                  </div>
                  <span>SAGE is reasoning and referencing course notes...</span>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* 3. Floating Pill Input Area (Iconic Gemini Bar) */}
      <div className="p-4 md:p-6 bg-gradient-to-t from-gemini-900 via-gemini-900 to-transparent">
        <div className="max-w-3xl mx-auto space-y-3">
          {/* Quick Prompts Bar (When chat has messages) */}
          {!isDialogueEmpty && (
            <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
              <span className="text-[11px] text-gemini-500 font-medium whitespace-nowrap pl-1">
                Suggested prompts:
              </span>
              {QUICK_TEST_PROMPTS.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => handleQuickPromptClick(item.prompt)}
                  disabled={isLoading}
                  className="px-3 py-1 rounded-full bg-gemini-800 hover:bg-gemini-750 text-gemini-300 hover:text-gemini-100 text-[11px] font-medium whitespace-nowrap border border-gemini-700/60 transition-colors disabled:opacity-50"
                >
                  {item.label}
                </button>
              ))}
            </div>
          )}

          {/* Gemini Floating Pill Form */}
          <form
            onSubmit={handleSubmit}
            className="flex items-center bg-gemini-800 border border-gemini-700/80 rounded-full px-4 py-2 shadow-pill focus-within:border-blue-500/60 focus-within:ring-2 focus-within:ring-blue-500/20 transition-all"
          >
            {/* Left '+' Icon Button */}
            <button
              type="button"
              className="p-1.5 rounded-full hover:bg-gemini-700 text-gemini-400 hover:text-gemini-200 transition-colors"
              title="Add context or options"
            >
              <Plus className="w-4 h-4" />
            </button>

            {/* Input Field */}
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask SAGE a question or describe your prompt..."
              rows={1}
              disabled={isLoading}
              className="flex-1 bg-transparent px-3 py-1.5 text-sm text-gemini-100 placeholder-gemini-400 focus:outline-none resize-none leading-relaxed disabled:opacity-50 max-h-32"
            />

            {/* Right Unit Selector Dropdown Pill */}
            <div className="hidden sm:flex items-center mr-2">
              <select
                value={selectedUnitId}
                onChange={(e) => onSelectUnit(e.target.value)}
                className="bg-gemini-700 text-gemini-300 text-xs rounded-full px-2.5 py-1 border border-gemini-600/60 focus:outline-none hover:text-gemini-100 transition-colors cursor-pointer"
              >
                {units.map((u) => (
                  <option key={u.unit_id} value={u.unit_id}>
                    {u.title.split(':')[0]}
                  </option>
                ))}
              </select>
            </div>

            {/* Send Button */}
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="w-8 h-8 rounded-full bg-gemini-700 hover:bg-gemini-600 text-gemini-100 flex items-center justify-center transition-all disabled:opacity-40 disabled:hover:bg-gemini-700 hover:scale-105 shadow-sm"
              title="Send message (Enter)"
            >
              <Send className="w-3.5 h-3.5 text-amber-300" />
            </button>
          </form>

          {/* Minimal Disclaimer Footer */}
          <p className="text-[11px] text-center text-gemini-500">
            SAGE is an AI Socratic tutor. It guides your thinking using targeted hints rather than giving away direct solutions.
          </p>
        </div>
      </div>
    </div>
  );
};
