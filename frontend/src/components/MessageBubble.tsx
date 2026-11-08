import React, { useState } from 'react';
import { HelpCircle, Lightbulb, BookOpen, CheckCircle, ChevronDown, ChevronUp, FileText, User, Bot } from 'lucide-react';
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
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-sky-500/10 text-sky-400 border border-sky-500/20">
            <HelpCircle className="w-3 h-3" /> Guiding Question
          </span>
        );
      case 'HINT':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Lightbulb className="w-3 h-3" /> Adaptive Hint
          </span>
        );
      case 'EXPLANATION':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <BookOpen className="w-3 h-3" /> Course Explanation
          </span>
        );
      case 'WRAP_UP':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle className="w-3 h-3" /> Topic Complete
          </span>
        );
      default:
        return null;
    }
  };

  if (isUser) {
    return (
      <div className="flex justify-end space-x-3 mb-4">
        <div className="max-w-2xl bg-emerald-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-md">
          <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
        </div>
        <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0 text-slate-300">
          <User className="w-4 h-4" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex space-x-3 mb-6">
      <div className="w-8 h-8 rounded-full bg-emerald-950 border border-emerald-500/40 flex items-center justify-center shrink-0 text-emerald-400">
        <Bot className="w-4 h-4" />
      </div>

      <div className="max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl rounded-tl-sm p-4 shadow-sm space-y-3">
        {/* Scaffolding Move Indicator */}
        {message.scaffolding_move && (
          <div className="flex items-center justify-between">
            {renderBadge(message.scaffolding_move)}
            <span className="text-[10px] text-slate-500">Socratic Mode</span>
          </div>
        )}

        {/* Tutor Message Content */}
        <p className="text-sm text-slate-200 whitespace-pre-wrap leading-relaxed">
          {message.content}
        </p>

        {/* Course Citations Card */}
        {message.citations && message.citations.length > 0 && (
          <div className="mt-3 pt-3 border-t border-slate-800/80">
            <button
              onClick={() => setShowCitations(!showCitations)}
              className="text-[11px] font-medium text-emerald-400 hover:text-emerald-300 flex items-center gap-1.5 transition-colors"
            >
              <FileText className="w-3 h-3" />
              <span>Grounded in Course Material ({message.citations.length})</span>
              {showCitations ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>

            {showCitations && (
              <div className="mt-2 space-y-2">
                {message.citations.map((cite: CitationItem, idx: number) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800 text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between text-slate-400">
                      <span className="font-semibold text-slate-300 truncate">{cite.source_title}</span>
                      <span className="text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-emerald-300/80">
                        {cite.slide_or_section}
                      </span>
                    </div>
                    {cite.excerpt && (
                      <p className="text-slate-400 text-[11px] leading-relaxed italic border-l-2 border-emerald-500/50 pl-2 mt-1">
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
