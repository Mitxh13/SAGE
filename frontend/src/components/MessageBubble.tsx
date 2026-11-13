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

interface CurriculumTopicInfo {
  unitTitle: string;
  topicTitle: string;
  targetUnderstanding: string;
}

const CURRICULUM_MAP: Record<string, CurriculumTopicInfo> = {
  // Unit 1
  unit1_topic0: {
    unitTitle: 'Unit 1: Prompt Structure, Role, Constraints & Output Formatting',
    topicTitle: 'Topic 1: Output Formatting and Structural Constraints',
    targetUnderstanding:
      'Explicitly specify target format schemas (JSON schema, markdown tables, bullet points) and use clear boundary delimiters (XML tags, triple backticks) with a defined system persona to strictly constrain the output distribution.',
  },
  unit1_topic1: {
    unitTitle: 'Unit 1: Prompt Structure, Role, Constraints & Output Formatting',
    topicTitle: 'Topic 2: System Instructions vs. User Data Separation',
    targetUnderstanding:
      'Clearly isolate untrusted user data within dedicated delimiter tags (<user_input>) distinct from system instructions. Enforce defensive boundary rules to prevent prompt injection and core rule overrides.',
  },
  // Unit 2
  unit2_topic0: {
    unitTitle: 'Unit 2: In-Context Learning — Zero-Shot, Few-Shot & Chain-of-Thought',
    topicTitle: 'Topic 1: Few-Shot Exemplar Selection and Formatting',
    targetUnderstanding:
      'Provide balanced and diverse input-output demonstration pairs covering edge cases. Keep demonstration syntax, label conventions, and delimiters strictly uniform across all exemplars to prevent majority label bias and recency bias.',
  },
  unit2_topic1: {
    unitTitle: 'Unit 2: In-Context Learning — Zero-Shot, Few-Shot & Chain-of-Thought',
    topicTitle: 'Topic 2: Chain-of-Thought (CoT) Prompting',
    targetUnderstanding:
      'Chain-of-Thought prompting allocates intermediate reasoning tokens ("Think step by step"). Placing the rationale trace before the final answer allows subsequent output tokens to condition on explicit deduction rather than immediate guessing.',
  },
  // Unit 3
  unit3_topic0: {
    unitTitle: 'Unit 3: LLM Decoding Parameters, Hallucinations & RAG Concepts',
    topicTitle: 'Topic 1: Sampling & Decoding Parameters (Temperature, Top-p)',
    targetUnderstanding:
      'Temperature controls the flatness of the softmax token probability distribution (randomness), not factual pretraining truth. Greedy decoding (temperature=0) does not eliminate hallucinations; Top-p nucleus sampling dynamically truncates the probability mass tail.',
  },
  unit3_topic1: {
    unitTitle: 'Unit 3: LLM Decoding Parameters, Hallucinations & RAG Concepts',
    topicTitle: 'Topic 2: Retrieval-Augmented Generation Grounding',
    targetUnderstanding:
      'Retrieval-Augmented Generation (RAG) injects dynamic, proprietary, or post-cutoff course excerpts directly into the prompt context window, grounding generation in verifiable evidence to eliminate extrinsic hallucinations.',
  },
};

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

  const resolveCurriculumInfo = (c: CitationItem): { unitTitle: string; sectionTitle: string; excerptText: string } => {
    const rawSrc = c.source_title || '';
    const rawRef = c.slide_or_section || '';
    const rawExc = c.excerpt || '';

    // Determine unit index (1, 2, or 3)
    let unitNum = 1;
    if (rawSrc.includes('Unit 2') || rawSrc.includes('unit_2')) unitNum = 2;
    else if (rawSrc.includes('Unit 3') || rawSrc.includes('unit_3')) unitNum = 3;

    // Determine topic index (0 or 1)
    let topicNum = 0;
    if (
      rawRef.includes('/topics/1') ||
      rawRef.includes('System Instructions') ||
      rawRef.includes('Chain-of-Thought') ||
      rawRef.includes('Retrieval-Augmented')
    ) {
      topicNum = 1;
    }

    const key = `unit${unitNum}_topic${topicNum}`;
    const info = CURRICULUM_MAP[key] || CURRICULUM_MAP.unit1_topic0;

    const cleanUnit = info.unitTitle;
    let cleanSection = info.topicTitle;
    if (rawRef.includes('Slide')) {
      cleanSection = `${rawRef} • ${info.topicTitle.split(':')[1]?.trim() || info.topicTitle}`;
    }

    let cleanExcerpt = rawExc.trim();
    if (!cleanExcerpt || cleanExcerpt === '""' || cleanExcerpt === 'None') {
      cleanExcerpt = info.targetUnderstanding;
    }

    return { unitTitle: cleanUnit, sectionTitle: cleanSection, excerptText: cleanExcerpt };
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
                {message.citations.map((c: CitationItem, i: number) => {
                  const resolved = resolveCurriculumInfo(c);
                  return (
                    <div
                      key={i}
                      className="p-3.5 rounded-2xl bg-[#F4F8F5] border-2 border-[#8EB39D] text-xs text-[#1B3024] shadow-sm space-y-1.5"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                        <span className="font-extrabold text-[#1B3024] text-xs">
                          {resolved.unitTitle}
                        </span>
                        <span className="inline-block text-[10px] bg-[#D0E2D6] text-[#1B3024] px-2.5 py-0.5 rounded-full border border-[#8EB39D] font-bold shrink-0 self-start sm:self-auto">
                          {resolved.sectionTitle}
                        </span>
                      </div>
                      <p className="text-[#244333] italic leading-relaxed font-medium bg-[#EAF2ED] p-2.5 rounded-xl border border-[#ADC5B7]">
                        "{resolved.excerptText}"
                      </p>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
