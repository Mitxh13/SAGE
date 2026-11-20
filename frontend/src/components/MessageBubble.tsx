import React, { useState } from 'react';
import {
  HelpCircle,
  Lightbulb,
  BookOpen,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  FileText,
  Sparkles,
} from 'lucide-react';
import { CitationItem, Message, ScaffoldingMove } from '../types/sage';

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const [showCitations, setShowCitations] = useState<boolean>(false);

  const renderBadge = (move?: ScaffoldingMove | null) => {
    switch (move) {
      case 'QUESTION':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-300 border border-blue-500/20 shadow-sm">
            <HelpCircle className="w-3.5 h-3.5 text-blue-400" />
            Guiding Question
          </span>
        );
      case 'HINT':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-amber-500/10 text-amber-300 border border-amber-500/20 shadow-sm">
            <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
            Adaptive Hint
          </span>
        );
      case 'EXPLANATION':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-purple-500/10 text-purple-300 border border-purple-500/20 shadow-sm">
            <BookOpen className="w-3.5 h-3.5 text-purple-400" />
            Course Explanation
          </span>
        );
      case 'WRAP_UP':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/20 shadow-sm">
            <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
            Topic Mastered
          </span>
        );
      default:
        return null;
    }
  };

  if (isUser) {
    return (
      <div className="flex justify-end mb-6 animate-fade-in">
        <div className="max-w-2xl bg-gemini-700 text-gemini-100 rounded-3xl rounded-tr-md px-5 py-3.5 shadow-sm border border-gemini-600/30 text-sm leading-relaxed">
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start space-x-3.5 mb-8 animate-fade-in">
      {/* SAGE Gemini Sparkle Avatar */}
      <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 via-purple-500 to-amber-500 p-0.5 shrink-0 shadow-md mt-0.5">
        <div className="w-full h-full bg-gemini-900 rounded-full flex items-center justify-center">
          <Sparkles className="w-4 h-4 text-amber-300" />
        </div>
      </div>

      <div className="flex-1 max-w-2xl space-y-3">
        {/* Scaffolding Move Indicator */}
        {message.scaffolding_move && (
          <div className="flex items-center space-x-2">
            {renderBadge(message.scaffolding_move)}
          </div>
        )}

        {/* Message Content */}
        <div className="text-gemini-200 text-sm leading-relaxed whitespace-pre-wrap font-sans">
          {message.content}
        </div>

        {/* Grounded Course Citations Chips */}
        {message.citations && message.citations.length > 0 && (
          <div className="pt-2">
            <button
              onClick={() => setShowCitations(!showCitations)}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gemini-800 hover:bg-gemini-750 border border-gemini-600/40 text-xs text-gemini-300 transition-all shadow-sm group"
            >
              <FileText className="w-3.5 h-3.5 text-amber-400 group-hover:scale-110 transition-transform" />
              <span>Grounded in Course Material ({message.citations.length})</span>
              {showCitations ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>

            {showCitations && (
              <div className="mt-3 space-y-2 animate-fade-in">
                {message.citations.map((cite: CitationItem, idx: number) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-2xl bg-gemini-800/90 border border-gemini-700/60 text-xs space-y-1.5 shadow-sm"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-gemini-200">{cite.source_title}</span>
                      <span className="px-2 py-0.5 rounded-full bg-gemini-700 text-amber-300 text-[10px] font-mono border border-gemini-600/50">
                        {cite.slide_or_section}
                      </span>
                    </div>
                    {cite.excerpt && (
                      <p className="text-gemini-400 text-xs italic leading-relaxed border-l-2 border-amber-500/40 pl-2 mt-1">
                        "{cite.excerpt}"
                      </p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
