import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  SlidersHorizontal,
  Loader2,
  Plus,
  HelpCircle,
  Lightbulb,
  Compass,
  Code2,
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
    label: "Direct Solution Request",
    prompt: "My prompt keeps giving inconsistent answers. Can you just fix it?",
    desc: "Evaluates Socratic refusal and format diagnosis redirection",
  },
  {
    icon: Lightbulb,
    label: "Reasoning Reflection",
    prompt: "No, I just asked the question directly without specifying any format schema.",
    desc: "Provides self-reflection on missing structural delimiters",
  },
  {
    icon: Compass,
    label: "Hyperparameter Exploration",
    prompt: "Why does setting temperature=0 not guarantee complete factual accuracy?",
    desc: "Investigates decoding strategy vs training knowledge boundaries",
  },
  {
    icon: Code2,
    label: "Schema Synthesis",
    prompt: "I should specify an explicit JSON format schema with clear boundary delimiters.",
    desc: "Synthesizes correct pattern to advance topic mastery",
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
  const [activeTab, setActiveTab] = useState<'chat' | 'task'>('chat');
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

  // Reusable Pill Input Component (Sage on Cream)
  const renderInputBar = (isCentered: boolean = false) => (
    <form
      onSubmit={handleSubmit}
      className={`w-full flex items-center bg-sage-50 border-2 border-sage-300 rounded-full px-4 py-2 transition-all ${
        isCentered
          ? 'shadow-pill hover:border-sage-500 focus-within:border-sage-600 focus-within:ring-2 focus-within:ring-sage-400/30'
          : 'shadow-sage-sm focus-within:border-sage-600 focus-within:ring-2 focus-within:ring-sage-400/30'
      }`}
    >
      <button
        type="button"
        className="p-1.5 rounded-full hover:bg-sage-200 text-sage-700 hover:text-sage-950 transition-colors shrink-0"
        title="Add context or notes"
      >
        <Plus className="w-4 h-4" />
      </button>

      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask SAGE a question or describe a prompt challenge..."
        rows={1}
        disabled={isLoading}
        className="flex-1 bg-transparent px-3 py-1.5 text-sm text-sage-950 placeholder-sage-600 font-medium focus:outline-none resize-none leading-relaxed disabled:opacity-50 max-h-32"
      />

      <div className="hidden sm:flex items-center mr-2 shrink-0">
        <select
          value={selectedUnitId}
          onChange={(e) => onSelectUnit(e.target.value)}
          className="bg-sage-200 text-sage-900 font-semibold text-xs rounded-full px-3 py-1 border border-sage-300 focus:outline-none hover:bg-sage-300 transition-colors cursor-pointer"
        >
          {units.map((u) => (
            <option key={u.unit_id} value={u.unit_id}>
              {u.title.split(':')[0]}
            </option>
          ))}
        </select>
      </div>

      <button
        type="submit"
        disabled={!input.trim() || isLoading}
        className="w-8 h-8 rounded-full bg-sage-700 hover:bg-sage-800 text-cream-50 flex items-center justify-center transition-all disabled:opacity-30 disabled:hover:bg-sage-700 hover:scale-105 shadow-sage-sm shrink-0"
        title="Send message (Enter)"
      >
        <Send className="w-3.5 h-3.5 text-cream-50" />
      </button>
    </form>
  );

  return (
    <div className="flex-1 flex flex-col h-full bg-cream-100 overflow-hidden relative font-sans">
      {/* 1. Header Bar */}
      <header className="h-16 px-6 flex items-center justify-between border-b border-cream-300 bg-cream-100/90 backdrop-blur-md z-10">
        <div className="flex items-center space-x-3">
          <div className="w-2.5 h-2.5 rounded-full bg-sage-700 animate-pulse"></div>
          <span className="text-sm font-bold text-sage-950">
            {activeUnitTitle || "Prompt Engineering & GenAI"}
          </span>
          <span className="hidden sm:inline-block text-xs font-semibold px-2.5 py-0.5 rounded-full bg-sage-100 text-sage-800 border border-sage-300">
            Socratic Guidance
          </span>
        </div>

        {/* X-Ray Inspector Toggle Button */}
        <div className="flex items-center space-x-2.5">
          <button
            onClick={onToggleInspector}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all shadow-sage-sm ${
              inspectorOpen
                ? 'bg-sage-700 text-cream-50 border border-sage-800'
                : 'bg-sage-100 text-sage-800 hover:bg-sage-200 border border-sage-300'
            }`}
            title="Toggle Live Pedagogical Telemetry Drawer"
          >
            <SlidersHorizontal className="w-3.5 h-3.5 text-sage-700" />
            <span>X-Ray Telemetry</span>
            {inspectorOpen && (
              <span className="w-1.5 h-1.5 rounded-full bg-cream-50"></span>
            )}
          </button>
        </div>
      </header>

      {/* 2. Main Content Canvas */}
      <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 relative">
        <div className="max-w-3xl mx-auto h-full flex flex-col">
          {isDialogueEmpty ? (
            /* Gemini-Style Centered Hero (Cream Canvas + Sage Components) */
            <div className="flex-1 flex flex-col items-center justify-center text-center px-4 relative py-8">
              {/* Centered 4-pointed Sparkle Emblem in Sage Green */}
              <div className="w-12 h-12 rounded-2xl bg-sage-200 border border-sage-300 flex items-center justify-center shadow-sage-sm mb-5">
                <svg
                  className="w-7 h-7 text-sage-800"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path d="M12 0C12 6.627 6.627 12 0 12C6.627 12 12 17.373 12 24C12 17.373 17.373 12 24 12C17.373 12 12 6.627 12 0Z" />
                </svg>
              </div>

              {/* Clean Greeting */}
              <h1 className="text-3xl md:text-4xl font-bold text-sage-950 tracking-tight mb-2">
                Hello, Mitesh
              </h1>
              <p className="text-sage-800 text-sm md:text-base max-w-md mb-8 leading-relaxed font-medium">
                How can SAGE assist your understanding of Prompt Engineering today?
              </p>

              {/* Centered Floating Pill Input Bar */}
              <div className="w-full max-w-2xl mb-5">
                {renderInputBar(true)}
              </div>

              {/* Pill Tabs: Dialogue / Exercise */}
              <div className="flex items-center gap-1.5 bg-sage-200/80 p-1 rounded-full mb-8 border border-sage-300">
                <button
                  type="button"
                  onClick={() => setActiveTab('chat')}
                  className={`px-3 py-1 rounded-full text-xs font-semibold transition-all ${
                    activeTab === 'chat'
                      ? 'bg-sage-700 text-cream-50 shadow-sage-sm'
                      : 'text-sage-800 hover:text-sage-950'
                  }`}
                >
                  Socratic Dialogue
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('task')}
                  className={`px-3 py-1 rounded-full text-xs font-semibold transition-all ${
                    activeTab === 'task'
                      ? 'bg-sage-700 text-cream-50 shadow-sage-sm'
                      : 'text-sage-800 hover:text-sage-950'
                  }`}
                >
                  Curriculum Exercise
                </button>
              </div>

              {/* Prompt Suggestions List (Sage Component Cards) */}
              <div className="w-full max-w-2xl space-y-2 text-left">
                {QUICK_TEST_PROMPTS.map((item, idx) => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={idx}
                      onClick={() => handleQuickPromptClick(item.prompt)}
                      className="w-full p-3.5 rounded-2xl bg-sage-100 hover:bg-sage-200 border border-sage-300 text-left transition-all hover:scale-[1.005] shadow-sage-sm flex items-center justify-between group"
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-xl bg-sage-200 border border-sage-300 flex items-center justify-center text-sage-800 group-hover:bg-sage-300 transition-colors shrink-0">
                          <Icon className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="text-xs font-bold text-sage-950 group-hover:text-sage-900 transition-colors">
                            "{item.prompt}"
                          </div>
                          <div className="text-[11px] text-sage-700 font-medium">
                            {item.desc}
                          </div>
                        </div>
                      </div>
                      <span className="text-[11px] font-bold text-sage-800 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pl-2">
                        Test Scenario →
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          ) : (
            /* Active Dialogue Messages Flow */
            <div className="space-y-4 flex-1 pb-4">
              {messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}

              {/* Thinking / Loading Animation */}
              {isLoading && (
                <div className="flex items-center space-x-3 text-sage-800 text-xs py-3 px-2 font-medium">
                  <div className="w-7 h-7 rounded-full bg-sage-100 border border-sage-300 flex items-center justify-center">
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-sage-700" />
                  </div>
                  <span>SAGE is analyzing reasoning and inspecting curriculum slides...</span>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
      </div>

      {/* 3. Docked Pill Input Area (When Chat is Active) */}
      {!isDialogueEmpty && (
        <div className="p-4 md:p-6 bg-gradient-to-t from-cream-100 via-cream-100 to-transparent">
          <div className="max-w-3xl mx-auto space-y-3">
            {/* Quick Prompts Bar */}
            <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
              <span className="text-[11px] text-sage-800 font-bold whitespace-nowrap pl-1">
                Suggested prompts:
              </span>
              {QUICK_TEST_PROMPTS.map((item, idx) => (
                <button
                  key={idx}
                  onClick={() => handleQuickPromptClick(item.prompt)}
                  disabled={isLoading}
                  className="px-3.5 py-1.5 rounded-full bg-sage-100 hover:bg-sage-200 text-sage-900 text-[11px] font-bold whitespace-nowrap border border-sage-300 transition-colors disabled:opacity-50 shadow-sage-sm"
                >
                  {item.label}
                </button>
              ))}
            </div>

            {/* Docked Form */}
            {renderInputBar(false)}

            {/* Minimal Disclaimer */}
            <p className="text-[11px] text-center text-sage-700 font-medium">
              SAGE guides your reasoning with targeted hints rather than giving direct solutions.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
