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
import { SageLogo } from './SageLogo';

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

  // Reusable Pill Input Component (Light Sage & Cream)
  const renderInputBar = (isCentered: boolean = false) => (
    <form
      onSubmit={handleSubmit}
      className={`w-full flex items-center bg-[#F4F8F5] border-2 border-[#8EB39D] rounded-full px-4 py-2 transition-all ${
        isCentered
          ? 'shadow-pill hover:border-[#649377] focus-within:border-[#385A48] focus-within:ring-2 focus-within:ring-[#8EB39D]/40'
          : 'shadow-sm focus-within:border-[#385A48] focus-within:ring-2 focus-within:ring-[#8EB39D]/40'
      }`}
    >
      <button
        type="button"
        className="p-1.5 rounded-full hover:bg-[#DCE8E0] text-[#244333] transition-colors shrink-0"
        title="Add context or notes"
      >
        <Plus className="w-4 h-4 text-[#244333]" />
      </button>

      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask SAGE a question or describe a prompt challenge..."
        rows={1}
        disabled={isLoading}
        className="flex-1 bg-transparent px-3 py-1.5 text-sm text-[#1B3024] placeholder-[#4A725D] font-semibold focus:outline-none resize-none leading-relaxed disabled:opacity-50 max-h-32"
      />

      <div className="hidden sm:flex items-center mr-2 shrink-0">
        <select
          value={selectedUnitId}
          onChange={(e) => onSelectUnit(e.target.value)}
          className="bg-[#E2ECE5] text-[#1B3024] font-bold text-xs rounded-full px-3 py-1 border border-[#8EB39D] focus:outline-none hover:bg-[#D5E4D9] transition-colors cursor-pointer"
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
        className="w-8 h-8 rounded-full bg-[#2D4D3B] hover:bg-[#1E3628] text-white flex items-center justify-center transition-all disabled:opacity-40 hover:scale-105 shadow-sm shrink-0"
        title="Send message (Enter)"
      >
        <Send className="w-3.5 h-3.5 text-white" />
      </button>
    </form>
  );

  return (
    <div className="flex-1 flex flex-col h-full bg-[#F5F1E9] overflow-hidden relative font-sans">
      {/* 1. Header Bar */}
      <header className="h-16 px-6 flex items-center justify-between border-b border-[#DDD5C7] bg-[#F5F1E9]/95 backdrop-blur-md z-10">
        <div className="flex items-center space-x-3">
          <div className="w-2.5 h-2.5 rounded-full bg-[#3A604B]"></div>
          <span className="text-sm font-extrabold text-[#1B3024]">
            {activeUnitTitle || "Prompt Engineering & GenAI"}
          </span>
          <span className="hidden sm:inline-block text-xs font-bold px-2.5 py-0.5 rounded-full bg-[#E2ECE5] text-[#1B3024] border border-[#8EB39D]">
            Socratic Guidance
          </span>
        </div>

        {/* X-Ray Inspector Toggle Button */}
        <div className="flex items-center space-x-2.5">
          <button
            onClick={onToggleInspector}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-bold transition-all shadow-sm ${
              inspectorOpen
                ? 'bg-[#2D4D3B] text-white border-2 border-[#1E3628]'
                : 'bg-[#E2ECE5] hover:bg-[#D5E4D9] text-[#1B3024] border-2 border-[#8EB39D]'
            }`}
            title="Toggle Live Pedagogical Telemetry Drawer"
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            <span>X-Ray Telemetry</span>
            {inspectorOpen && (
              <span className="w-1.5 h-1.5 rounded-full bg-white"></span>
            )}
          </button>
        </div>
      </header>

      {/* 2. Main Content Canvas */}
      <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 relative">
        <div className="max-w-3xl mx-auto h-full flex flex-col">
          {isDialogueEmpty ? (
            /* Gemini-Style Centered Hero (Cream Canvas + Light Sage Components) */
            <div className="flex-1 flex flex-col items-center justify-center text-center px-4 relative py-8">
              {/* Centered SAGE Custom Wisdom Emblem */}
              <div className="mb-5 flex items-center justify-center hover:scale-105 transition-transform">
                <SageLogo size={56} />
              </div>

              {/* Clean Greeting */}
              <h1 className="text-3xl md:text-4xl font-extrabold text-[#1B3024] tracking-tight mb-2">
                Hello, Student
              </h1>
              <p className="text-[#244333] text-sm md:text-base max-w-md mb-8 leading-relaxed font-semibold">
                How can SAGE assist your understanding of Prompt Engineering today?
              </p>

              {/* Centered Floating Pill Input Bar */}
              <div className="w-full max-w-2xl mb-5">
                {renderInputBar(true)}
              </div>

              {/* Pill Tabs: Dialogue / Exercise */}
              <div className="flex items-center gap-1.5 bg-[#EAE4D8] p-1 rounded-full mb-8 border border-[#DDD5C7]">
                <button
                  type="button"
                  onClick={() => setActiveTab('chat')}
                  className={`px-3 py-1 rounded-full text-xs font-bold transition-all ${
                    activeTab === 'chat'
                      ? 'bg-[#E2ECE5] text-[#1B3024] border border-[#8EB39D] shadow-sm'
                      : 'text-[#244333] hover:text-[#1B3024]'
                  }`}
                >
                  Socratic Dialogue
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('task')}
                  className={`px-3 py-1 rounded-full text-xs font-bold transition-all ${
                    activeTab === 'task'
                      ? 'bg-[#E2ECE5] text-[#1B3024] border border-[#8EB39D] shadow-sm'
                      : 'text-[#244333] hover:text-[#1B3024]'
                  }`}
                >
                  Curriculum Exercise
                </button>
              </div>

              {/* Prompt Suggestions List (Light Sage Cards with Bold Dark Text) */}
              <div className="w-full max-w-2xl space-y-2.5 text-left">
                {QUICK_TEST_PROMPTS.map((item, idx) => {
                  const Icon = item.icon;
                  return (
                    <button
                      key={idx}
                      onClick={() => handleQuickPromptClick(item.prompt)}
                      className="w-full p-3.5 rounded-2xl bg-[#EAF2ED] hover:bg-[#DCE9DF] border-2 border-[#9BBFA9] text-left transition-all hover:scale-[1.005] shadow-sm flex items-center justify-between group"
                    >
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-xl bg-[#D0E2D6] border border-[#8EB39D] flex items-center justify-center text-[#1B3024] group-hover:bg-[#C2D8CB] transition-colors shrink-0">
                          <Icon className="w-4 h-4 text-[#1B3024]" />
                        </div>
                        <div>
                          <div className="text-xs font-extrabold text-[#1B3024] group-hover:text-[#122219] transition-colors">
                            "{item.prompt}"
                          </div>
                          <div className="text-[11px] text-[#244333] font-semibold">
                            {item.desc}
                          </div>
                        </div>
                      </div>
                      <span className="text-[11px] font-extrabold text-[#244333] opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pl-2">
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
                <div className="flex items-center space-x-3 text-[#244333] text-xs py-3 px-2 font-bold">
                  <div className="w-7 h-7 rounded-full bg-[#E2ECE5] border border-[#8EB39D] flex items-center justify-center">
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-[#244333]" />
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
        <div className="p-4 md:p-6 bg-gradient-to-t from-[#F5F1E9] via-[#F5F1E9] to-transparent">
          <div className="max-w-3xl mx-auto space-y-3">
            {/* Docked Form */}
            {renderInputBar(false)}

            {/* Minimal Disclaimer */}
            <p className="text-[11px] text-center text-[#3A604B] font-bold">
              SAGE guides your reasoning with targeted hints rather than giving direct solutions.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};
