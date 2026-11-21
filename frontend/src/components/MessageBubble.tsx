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
          <span className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full text-xs font-medium bg-sage-100 text-sage-800 border border-sage-200 shadow-sm">
            <HelpCircle className="w-3.5 h-3.5 text-sage-700" />
            Guiding Question
          </span>
        );
      case 'HINT':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-800 border border-amber-200 shadow-sm">
            <Lightbulb className="w-3.5 h-3.5 text-amber-600" />
            Adaptive Hint
          </span>
        );
      case 'EXPLANATION':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-800 border border-blue-200 shadow-sm">
            <BookOpen className="w-3.5 h-3.5 text-blue-600" />
            Course Explanation
          </span>
        );
      case 'WRAP_UP':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-800 border border-emerald-200 shadow-sm">
            <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
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
        <div className="max-w-2xl bg-sage-700 text-white rounded-3xl rounded-tr-md px-5 py-3.5 shadow-sage-soft text-sm leading-relaxed">
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start space-x-3 mb-6">
      {/* SAGE Avatar */}
      <div className="w-8 h-8 rounded-xl bg-sage-100 border border-sage-200 flex items-center justify-center text-sage-700 shrink-0 shadow-sm mt-1">
        <Sparkles className="w-4 h-4 text-sage-700" />
      </div>

      <div className="flex-1 max-w-2xl space-y-2.5">
        {/* Scaffolding Move Indicator */}
        {message.scaffolding_move && (
          <div className="flex items-center space-x-2">
            {renderBadge(message.scaffolding_move)}
          </div>
        )}

        {/* Message Content Card */}
        <div className="bg-white border border-cream-300 rounded-3xl rounded-tl-md px-5 py-4 text-charcoal-800 text-sm leading-relaxed whitespace-pre-wrap shadow-sm">
          {message.content}
        </div>

        {/* Grounded Course Citations */}
        {message.citations && message.citations.length > 0 && (
          <div className="pt-1">
            <button
              onClick={() => setShowCitations(!showCitations)}
              className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white hover:bg-cream-150 border border-cream-300 text-xs text-charcoal-600 hover:text-charcoal-800 transition-all shadow-sm"
            >
              <FileText className="w-3.5 h-3.5 text-sage-600" />
              <span className="font-medium">Curriculum Reference ({message.citations.length})</span>
              {showCitations ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>

            {showCitations && (
              <div className="mt-2 space-y-2 pl-2 border-l-2 border-sage-300">
                {message.citations.map((c: CitationItem, i: number) => (
                  <div
                    key={i}
                    className="p-3 rounded-2xl bg-white border border-cream-300 text-xs text-charcoal-700 shadow-sm space-y-1"
                  >
                    <div className="font-semibold text-sage-800 flex items-center justify-between">
                      <span>{c.source_title}</span>
                      <span className="text-[10px] bg-sage-50 text-sage-700 px-2 py-0.5 rounded-full border border-sage-200">
                        {c.slide_or_section}
                      </span>
                    </div>
                    <p className="text-charcoal-600 italic leading-relaxed">
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
