import React, { useState } from 'react';
import {
  Activity,
  Award,
  ChevronDown,
  ChevronUp,
  ChevronRight,
  Code2,
  HelpCircle,
  Lightbulb,
  BookOpen,
  CheckCircle,
  X,
  AlertTriangle,
  Flame,
} from 'lucide-react';
import { LearnerState, TurnTrace } from '../types/sage';

interface StateInspectorProps {
  learnerState: LearnerState | null;
  traces: TurnTrace[];
  isOpen: boolean;
  onClose: () => void;
}

const TOPIC_TITLES: Record<string, string> = {
  topic_output_formatting: 'Output Formatting and Structural Constraints',
  topic_system_instructions_vs_user_data: 'System Instructions vs. User Data Separation',
  topic_in_context_exemplars: 'Few-Shot Exemplar Selection and Formatting',
  topic_chain_of_thought: 'Chain-of-Thought (CoT) Prompting',
  topic_decoding_parameters: 'Sampling & Decoding Parameters (Temperature, Top-p)',
  topic_rag_grounding: 'Retrieval-Augmented Generation Grounding',
};

export const StateInspector: React.FC<StateInspectorProps> = ({
  learnerState,
  traces,
  isOpen,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<'metrics' | 'trace'>('metrics');
  const [selectedTraceIndex, setSelectedTraceIndex] = useState<number>(0);
  const [traceExpandedSections, setTraceExpandedSections] = useState<Record<string, boolean>>({
    analyzer: true,
    retriever: false,
    tutor: true,
  });

  const [expandedMastered, setExpandedMastered] = useState<Record<string, boolean>>({});

  const toggleMasteredRecap = (topicId: string) => {
    setExpandedMastered((prev) => ({
      ...prev,
      [topicId]: prev[topicId] === undefined ? false : !prev[topicId],
    }));
  };

  const safeTraces = traces || [];

  React.useEffect(() => {
    if (safeTraces.length > 0) {
      setSelectedTraceIndex(safeTraces.length - 1);
    }
  }, [safeTraces.length]);

  if (!isOpen) return null;

  const latestTrace = safeTraces.length > 0 ? safeTraces[safeTraces.length - 1] : null;
  const currentTrace = safeTraces[selectedTraceIndex] || latestTrace;

  const toggleTraceSection = (section: string) => {
    setTraceExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const stages = [
    { key: 'QUESTION', label: '1. Question', icon: HelpCircle },
    { key: 'HINT', label: '2. Hint', icon: Lightbulb },
    { key: 'EXPLANATION', label: '3. Explanation', icon: BookOpen },
    { key: 'WRAP_UP', label: '4. Wrap-up', icon: CheckCircle },
  ];

  const formatTopicTitle = (topicId?: string | null) => {
    if (!topicId) return 'Topic 1';
    if (TOPIC_TITLES[topicId]) return TOPIC_TITLES[topicId];
    return topicId
      .replace(/^topic_/, '')
      .split('_')
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ');
  };

  // Collect all completed/mastered topics from execution traces
  const masteredTopics = React.useMemo(() => {
    const list: Array<{ topicId: string; title: string; recap?: string }> = [];
    const seen = new Set<string>();

    for (const tr of safeTraces) {
      if (tr.tutor_output?.scaffolding_move === 'WRAP_UP') {
        const tId = tr.analyzer_output?.active_topic_id;
        if (tId && !seen.has(tId)) {
          seen.add(tId);
          list.push({
            topicId: tId,
            title: formatTopicTitle(tId),
            recap: tr.tutor_output?.tutor_message,
          });
        }
      }
    }
    return list;
  }, [safeTraces]);

  const activeTopicId = learnerState?.active_topic_id;
  const lastTurnTopicId = latestTrace?.analyzer_output?.active_topic_id;
  
  // Wrap-up only applies to the active topic if the session has NOT advanced yet
  const isWrapUpOnCurrentTopic =
    latestTrace?.tutor_output?.scaffolding_move === 'WRAP_UP' &&
    activeTopicId === lastTurnTopicId;

  const effectiveStage = isWrapUpOnCurrentTopic
    ? 'WRAP_UP'
    : (learnerState?.scaffolding_stage || 'QUESTION');
  const currentStageIndex = stages.findIndex((s) => s.key === effectiveStage);
  const activeMisconceptions = Object.entries(learnerState?.active_misconceptions || {});

  return (
    <aside className="w-96 bg-[#EFE9DE] border-l border-[#DDD5C7] flex flex-col h-full z-30 select-none shadow-xl transition-all font-sans">
      {/* 1. Header */}
      <div className="p-4 border-b border-[#DDD5C7] flex items-center justify-between bg-[#E8E1D4]">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-[#E2ECE5] border-2 border-[#8EB39D] text-[#244333] flex items-center justify-center shadow-sm">
            <Activity className="w-4 h-4 text-[#244333]" />
          </div>
          <div>
            <h2 className="font-extrabold text-sm text-[#1B3024] tracking-tight">
              Pedagogical Telemetry
            </h2>
            <p className="text-[11px] text-[#3A604B] font-semibold">Live Orchestrator State</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-[#244333] hover:text-[#1B3024] hover:bg-[#DCD4C6] transition-colors"
          title="Close drawer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* 2. Navigation Tabs */}
      <div className="flex border-b border-[#DDD5C7] bg-[#EAE4D8]">
        <button
          onClick={() => setActiveTab('metrics')}
          className={`flex-1 py-2.5 text-xs font-extrabold text-center transition-all ${
            activeTab === 'metrics'
              ? 'text-[#1B3024] border-b-2 border-[#385A48] bg-[#F5F1E9] shadow-sm'
              : 'text-[#244333] hover:text-[#1B3024]'
          }`}
        >
          Learner State
        </button>
        <button
          onClick={() => setActiveTab('trace')}
          className={`flex-1 py-2.5 text-xs font-extrabold text-center transition-all flex items-center justify-center gap-1.5 ${
            activeTab === 'trace'
              ? 'text-[#1B3024] border-b-2 border-[#385A48] bg-[#F5F1E9] shadow-sm'
              : 'text-[#244333] hover:text-[#1B3024]'
          }`}
        >
          <Code2 className="w-3.5 h-3.5" />
          <span>Execution Traces ({traces.length})</span>
        </button>
      </div>

      {/* 3. Tab Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {activeTab === 'metrics' ? (
          <>
            {/* Scaffolding Stage Stepper */}
            <div className="space-y-2">
              <span className="text-[11px] font-extrabold text-[#244333] uppercase tracking-wider block">
                Scaffolding Escalation
              </span>
              <div className="grid grid-cols-2 gap-2">
                {stages.map((stg, idx) => {
                  const Icon = stg.icon;
                  const isCurrent = stg.key === effectiveStage;
                  const isPassed = idx < currentStageIndex;

                  return (
                    <div
                      key={stg.key}
                      className={`p-2.5 rounded-xl border-2 text-xs flex items-center space-x-2 transition-all ${
                        isCurrent
                          ? 'bg-[#D6E6DC] text-[#1B3024] border-[#649377] shadow-sm font-extrabold'
                          : isPassed
                          ? 'bg-[#EAF2ED] text-[#244333] border-[#ADC5B7] font-bold'
                          : 'bg-[#F4F8F5] text-[#557A64] border-[#D5E3DA] font-semibold'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5 shrink-0" />
                      <span className="truncate">{stg.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Core Metrics Cards (Light Sage Components) */}
            <div className="grid grid-cols-2 gap-2.5">
              {/* Struggle Counter */}
              <div className="p-3 rounded-2xl bg-[#EAF2ED] border-2 border-[#9BBFA9] shadow-sm space-y-1">
                <div className="flex items-center space-x-1.5 text-[#244333] text-xs font-bold">
                  <Flame className="w-3.5 h-3.5 text-[#3A604B]" />
                  <span>Struggle Count</span>
                </div>
                <div className="text-2xl font-extrabold text-[#1B3024]">
                  {learnerState?.struggle_turn_count ?? 0}
                  <span className="text-xs font-semibold text-[#3A604B] ml-1">turns</span>
                </div>
              </div>

              {/* LCC Score */}
              <div className="p-3 rounded-2xl bg-[#EAF2ED] border-2 border-[#9BBFA9] shadow-sm space-y-1">
                <div className="flex items-center space-x-1.5 text-[#244333] text-xs font-bold">
                  <Award className="w-3.5 h-3.5 text-[#3A604B]" />
                  <span>LCC Score</span>
                </div>
                <div className="text-2xl font-extrabold text-[#1B3024]">
                  {isWrapUpOnCurrentTopic
                    ? '100%'
                    : learnerState
                    ? `${(learnerState.overall_lcc_score * 100).toFixed(0)}%`
                    : '0%'}
                </div>
              </div>
            </div>

            {/* Active Topic Card */}
            <div className="p-3 rounded-2xl bg-[#EAF2ED] border-2 border-[#9BBFA9] shadow-sm space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-extrabold text-[#244333] uppercase tracking-wider block">
                  Active Topic
                </span>
                <span
                  className={`px-3 py-0.5 rounded-full text-[10px] font-extrabold border-2 ${
                    isWrapUpOnCurrentTopic || learnerState?.topic_status === 'DONE'
                      ? 'bg-[#D6E6DC] text-[#1B3024] border-[#649377] shadow-sm'
                      : 'bg-[#E2ECE5] text-[#244333] border-[#8EB39D]'
                  }`}
                >
                  {isWrapUpOnCurrentTopic || learnerState?.topic_status === 'DONE'
                    ? 'Topic Mastered'
                    : 'In Progress'}
                </span>
              </div>
              <div
                className="text-xs font-extrabold text-[#1B3024] leading-snug"
                title={formatTopicTitle(learnerState?.active_topic_id)}
              >
                {formatTopicTitle(learnerState?.active_topic_id)}
              </div>
            </div>

            {/* Mastered Topics Section */}
            {masteredTopics.length > 0 && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-extrabold text-[#244333] uppercase tracking-wider flex items-center gap-1.5">
                    <CheckCircle className="w-3.5 h-3.5 text-[#3A604B]" />
                    Mastered Topics
                  </span>
                  <span className="text-xs text-[#244333] font-mono font-extrabold bg-[#D6E6DC] px-2 py-0.5 rounded-full border border-[#8EB39D]">
                    {masteredTopics.length}
                  </span>
                </div>

                <div className="space-y-2">
                  {masteredTopics.map((mt) => {
                    const isExpanded = expandedMastered[mt.topicId] ?? true;
                    return (
                      <div
                        key={mt.topicId}
                        className="p-3 rounded-2xl bg-[#F4F8F5] border-2 border-[#8EB39D] shadow-sm space-y-2"
                      >
                        <div
                          className="flex items-center justify-between cursor-pointer"
                          onClick={() => toggleMasteredRecap(mt.topicId)}
                        >
                          <div className="flex items-center space-x-2">
                            <CheckCircle className="w-4 h-4 text-[#2D4D3B] shrink-0" />
                            <span className="text-xs font-extrabold text-[#1B3024]">
                              {mt.title}
                            </span>
                          </div>
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-[#D6E6DC] text-[#1B3024] border border-[#649377] shrink-0">
                            Mastered
                          </span>
                        </div>

                        {mt.recap && (
                          <div className="pt-1.5 border-t border-[#D5E4D9]">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-[10px] uppercase font-extrabold text-[#3A604B]">
                                Mastery Synthesis
                              </span>
                              <button
                                type="button"
                                onClick={() => toggleMasteredRecap(mt.topicId)}
                                className="inline-flex items-center gap-1 text-[10px] text-[#244333] hover:text-[#1B3024] font-bold"
                              >
                                <span>{isExpanded ? 'Hide' : 'Show'}</span>
                                {isExpanded ? (
                                  <ChevronUp className="w-3 h-3 text-[#244333]" />
                                ) : (
                                  <ChevronDown className="w-3 h-3 text-[#244333]" />
                                )}
                              </button>
                            </div>
                            {isExpanded && (
                              <p className="text-xs text-[#1B3024] italic leading-relaxed bg-[#EAF2ED] p-2.5 rounded-xl border border-[#ADC5B7] font-medium whitespace-pre-wrap">
                                "{mt.recap}"
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Active Misconceptions Tracker */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-extrabold text-[#244333] uppercase tracking-wider flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-[#3A604B]" />
                  Active Misconceptions
                </span>
                <span className="text-xs text-[#244333] font-mono font-extrabold">
                  {activeMisconceptions.length}
                </span>
              </div>

              {activeMisconceptions.length === 0 ? (
                <div className="p-3.5 rounded-2xl bg-[#EAF2ED] border-2 border-[#9BBFA9] text-xs text-[#244333] text-center font-bold">
                  No active misconceptions detected in current session.
                </div>
              ) : (
                <div className="space-y-2">
                  {activeMisconceptions.map(([id, conf]) => (
                    <div
                      key={id}
                      className="p-3 rounded-2xl bg-[#F4F8F5] border-2 border-[#8EB39D] shadow-sm space-y-1.5"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-extrabold text-[#1B3024] font-mono truncate max-w-[200px]">
                          {id}
                        </span>
                        <span className="text-[#244333] font-extrabold">
                          {(conf * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="w-full bg-[#D0E2D6] h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-[#385A48] h-full rounded-full transition-all duration-300"
                          style={{ width: `${Math.min(100, Math.max(5, conf * 100))}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        ) : (
          /* Execution Traces Viewer */
          <div className="space-y-3">
            {traces.length === 0 ? (
              <div className="text-center py-8 text-[#244333] text-xs font-bold">
                No turn traces logged yet. Send a message to inspect execution.
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-extrabold text-[#244333] uppercase tracking-wider">
                    Trace Selector
                  </span>
                  <select
                    value={selectedTraceIndex}
                    onChange={(e) => setSelectedTraceIndex(Number(e.target.value))}
                    className="bg-[#E2ECE5] border-2 border-[#8EB39D] text-[#1B3024] font-extrabold text-xs rounded-xl px-2.5 py-1 focus:outline-none"
                  >
                    {traces.map((_, idx) => (
                      <option key={idx} value={idx}>
                        Turn #{idx + 1}
                      </option>
                    ))}
                  </select>
                </div>

                {currentTrace && (
                  <div className="space-y-2.5">
                    {/* Analyzer Stage Trace */}
                    <div className="border-2 border-[#8EB39D] rounded-2xl bg-[#F4F8F5] overflow-hidden shadow-sm">
                      <button
                        onClick={() => toggleTraceSection('analyzer')}
                        className="w-full px-3.5 py-2.5 bg-[#E2ECE5] flex items-center justify-between text-xs font-extrabold text-[#1B3024] text-left"
                      >
                        <span>1. Understanding Analyzer</span>
                        {traceExpandedSections.analyzer ? (
                          <ChevronDown className="w-3.5 h-3.5 text-[#244333]" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5 text-[#244333]" />
                        )}
                      </button>
                      {traceExpandedSections.analyzer && (
                        <div className="p-3 text-[11px] font-mono text-[#1B3024] bg-[#F4F8F5] overflow-x-auto max-h-48 font-semibold">
                          <pre>{JSON.stringify(currentTrace.analyzer_output, null, 2)}</pre>
                        </div>
                      )}
                    </div>

                    {/* Retriever Stage Trace */}
                    <div className="border-2 border-[#8EB39D] rounded-2xl bg-[#F4F8F5] overflow-hidden shadow-sm">
                      <button
                        onClick={() => toggleTraceSection('retriever')}
                        className="w-full px-3.5 py-2.5 bg-[#E2ECE5] flex items-center justify-between text-xs font-extrabold text-[#1B3024] text-left"
                      >
                        <span>2. Course Retriever Context</span>
                        {traceExpandedSections.retriever ? (
                          <ChevronDown className="w-3.5 h-3.5 text-[#244333]" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5 text-[#244333]" />
                        )}
                      </button>
                      {traceExpandedSections.retriever && (
                        <div className="p-3 text-[11px] font-mono text-[#1B3024] bg-[#F4F8F5] overflow-x-auto max-h-48 font-semibold">
                          <pre>{JSON.stringify(currentTrace.retriever_output, null, 2)}</pre>
                        </div>
                      )}
                    </div>

                    {/* Tutor Stage Trace */}
                    <div className="border-2 border-[#8EB39D] rounded-2xl bg-[#F4F8F5] overflow-hidden shadow-sm">
                      <button
                        onClick={() => toggleTraceSection('tutor')}
                        className="w-full px-3.5 py-2.5 bg-[#E2ECE5] flex items-center justify-between text-xs font-extrabold text-[#1B3024] text-left"
                      >
                        <span>3. Tutor Agent Scaffolding</span>
                        {traceExpandedSections.tutor ? (
                          <ChevronDown className="w-3.5 h-3.5 text-[#244333]" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5 text-[#244333]" />
                        )}
                      </button>
                      {traceExpandedSections.tutor && (
                        <div className="p-3 text-[11px] font-mono text-[#1B3024] bg-[#F4F8F5] overflow-x-auto max-h-48 font-semibold">
                          <pre>{JSON.stringify(currentTrace.tutor_output, null, 2)}</pre>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </aside>
  );
};
