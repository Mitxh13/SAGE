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
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-sage-200 text-sage-950 border border-sage-400 shadow-sage-sm">
            <HelpCircle className="w-3.5 h-3.5 text-sage-800" />
            Guiding Question
          </span>
        );
      case 'HINT':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-sage-200 text-sage-950 border border-sage-400 shadow-sage-sm">
            <Lightbulb className="w-3.5 h-3.5 text-sage-800" />
            Adaptive Hint
          </span>
        );
      case 'EXPLANATION':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-sage-200 text-sage-950 border border-sage-400 shadow-sage-sm">
            <BookOpen className="w-3.5 h-3.5 text-sage-800" />
            Course Explanation
          </span>
        );
      case 'WRAP_UP':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-sage-700 text-cream-50 border border-sage-800 shadow-sage-sm">
            <CheckCircle className="w-3.5 h-3.5 text-cream-50" />
            Topic Mastered
          </span>
        );
      default:
        return null;
    }
  };

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-2xl bg-sage-700 text-cream-50 rounded-3xl rounded-tr-md px-5 py-3.5 shadow-sage-sm text-sm leading-relaxed font-medium">
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start space-x-3 mb-6">
      {/* SAGE Avatar */}
      <div className="w-8 h-8 rounded-xl bg-sage-700 text-cream-50 flex items-center justify-center shrink-0 shadow-sage-sm mt-1">
        <Sparkles className="w-4 h-4 text-cream-100" />
      </div>

      <div className="flex-1 max-w-2xl space-y-2.5">
        {/* Scaffolding Move Indicator */}
        {message.scaffolding_move && (
          <div className="flex items-center space-x-2">
            {renderBadge(message.scaffolding_move)}
          </div>
        )}

        {/* Message Content Card in Sage Component Surface */}
        <div className="bg-sage-100 border border-sage-300 rounded-3xl rounded-tl-md px-5 py-4 text-sage-950 text-sm leading-relaxed whitespace-pre-wrap shadow-sage-sm font-medium">
          {message.content}
        </div>

        {/* Grounded Course Citations */}
        {message.citations && message.citations.length > 0 && (
          <div className="pt-1">
            <button
              onClick={() => setShowCitations(!showCitations)}
              className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-sage-200 hover:bg-sage-300 border border-sage-300 text-xs text-sage-950 font-bold transition-all shadow-sage-sm"
            >
              <FileText className="w-3.5 h-3.5 text-sage-700" />
              <span>Curriculum Reference ({message.citations.length})</span>
              {showCitations ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>

            {showCitations && (
              <div className="mt-2 space-y-2 pl-2 border-l-2 border-sage-400">
                {message.citations.map((c: CitationItem, i: number) => (
                  <div
                    key={i}
                    className="p-3.5 rounded-2xl bg-sage-50 border border-sage-300 text-xs text-sage-950 shadow-sage-sm space-y-1"
                  >
                    <div className="font-bold text-sage-950 flex items-center justify-between">
                      <span>{c.source_title}</span>
                      <span className="text-[10px] bg-sage-200 text-sage-900 px-2 py-0.5 rounded-full border border-sage-300 font-semibold">
                        {c.slide_or_section}
                      </span>
                    </div>
                    <p className="text-sage-800 italic leading-relaxed font-normal">
                      "{c.excerpt}"
                    </p>
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
