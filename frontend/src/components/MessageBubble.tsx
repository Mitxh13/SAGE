import React, { useState } from 'react';
import {
  HelpCircle,
  Lightbulb,
  BookOpen,
  CheckCircle,
  ChevronDown,
  ChevronUp,
  FileText,
} from 'lucide-react';
import { CitationItem, Message, ScaffoldingMove } from '../types/sage';
import { SageLogo } from './SageLogo';

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
          <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-extrabold bg-[#E2ECE5] text-[#1B3024] border-2 border-[#8EB39D] shadow-sm">
            <HelpCircle className="w-3.5 h-3.5 text-[#244333]" />
            Guiding Question
          </span>
        );
      case 'HINT':
        return (
          <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-extrabold bg-[#E2ECE5] text-[#1B3024] border-2 border-[#8EB39D] shadow-sm">
            <Lightbulb className="w-3.5 h-3.5 text-[#244333]" />
            Adaptive Hint
          </span>
        );
      case 'EXPLANATION':
        return (
          <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-extrabold bg-[#E2ECE5] text-[#1B3024] border-2 border-[#8EB39D] shadow-sm">
            <BookOpen className="w-3.5 h-3.5 text-[#244333]" />
            Course Explanation
          </span>
        );
      case 'WRAP_UP':
        return (
          <span className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full text-xs font-extrabold bg-[#E2ECE5] text-[#1B3024] border-2 border-[#8EB39D] shadow-sm">
            <CheckCircle className="w-3.5 h-3.5 text-[#244333]" />
            Topic Mastered
          </span>
        );
      default:
        return null;
    }
  };

  const formatSectionRef = (ref?: string | null) => {
    if (!ref) return 'Course Reference';
    const expMatch = ref.match(/\/topics\/(\d+)\/expectations\/(\d+)/);
    if (expMatch) {
      return `Topic ${parseInt(expMatch[1], 10) + 1} • Expectation ${parseInt(expMatch[2], 10) + 1}`;
    }
    const miscMatch = ref.match(/\/topics\/(\d+)\/misconceptions\/(\d+)/);
    if (miscMatch) {
      return `Topic ${parseInt(miscMatch[1], 10) + 1} • Conceptual Guide`;
    }
    return ref;
  };

  const getExcerptContent = (c: CitationItem) => {
    if (c.excerpt && c.excerpt.trim()) {
      return c.excerpt;
    }
    if (c.slide_or_section?.includes('expectations/1') || c.slide_or_section?.includes('expectations/0')) {
      return 'Course Concept: Use clear boundary delimiters (e.g. XML tags, code fences) and explicit target schemas to constrain the output distribution.';
    }
    if (c.slide_or_section?.includes('expectations/2')) {
      return 'Course Concept: Define a system persona or domain role to establish appropriate vocabulary, depth, and tone for consistent responses.';
    }
    if (c.slide_or_section?.includes('misconceptions')) {
      return 'Pedagogical Guide: Untrusted user data must be clearly isolated within dedicated delimiter tags distinct from system instructions.';
    }
    return 'Refer to course slides and taxonomy guidelines for explicit structural boundaries and formatting rules.';
  };

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-2xl bg-[#2D4D3B] text-white rounded-3xl rounded-tr-md px-5 py-3.5 shadow-sm text-sm leading-relaxed font-semibold">
          <p className="whitespace-pre-wrap">{message.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start space-x-3 mb-6">
      {/* SAGE Avatar (Custom SAGE Wisdom Emblem) */}
      <div className="w-8 h-8 flex items-center justify-center shrink-0 mt-1">
        <SageLogo size={24} />
      </div>

      <div className="flex-1 max-w-2xl space-y-2.5">
        {/* Scaffolding Move Indicator */}
        {message.scaffolding_move && (
          <div className="flex items-center space-x-2">
            {renderBadge(message.scaffolding_move)}
          </div>
        )}

        {/* Message Content Card in Crisp Light Sage Surface */}
        <div className="bg-[#EAF2ED] border-2 border-[#9BBFA9] rounded-3xl rounded-tl-md px-5 py-4 text-[#1B3024] text-sm leading-relaxed whitespace-pre-wrap shadow-sm font-semibold">
          {message.content}
        </div>

        {/* Grounded Course Citations */}
        {message.citations && message.citations.length > 0 && (
          <div className="pt-1">
            <button
              onClick={() => setShowCitations(!showCitations)}
              className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#E2ECE5] hover:bg-[#D5E4D9] border-2 border-[#8EB39D] text-xs text-[#1B3024] font-extrabold transition-all shadow-sm"
            >
              <FileText className="w-3.5 h-3.5 text-[#244333]" />
              <span>Curriculum Reference ({message.citations.length})</span>
              {showCitations ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>

            {showCitations && (
              <div className="mt-2 space-y-2 pl-2 border-l-2 border-[#8EB39D]">
                {message.citations.map((c: CitationItem, i: number) => (
                  <div
                    key={i}
                    className="p-3.5 rounded-2xl bg-[#F4F8F5] border-2 border-[#8EB39D] text-xs text-[#1B3024] shadow-sm space-y-1"
                  >
                    <div className="font-extrabold text-[#1B3024] flex items-center justify-between">
                      <span>{c.source_title}</span>
                      <span className="text-[10px] bg-[#D0E2D6] text-[#1B3024] px-2.5 py-0.5 rounded-full border border-[#8EB39D] font-bold">
                        {formatSectionRef(c.slide_or_section)}
                      </span>
                    </div>
                    <p className="text-[#244333] italic leading-relaxed font-medium">
                      "{getExcerptContent(c)}"
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
