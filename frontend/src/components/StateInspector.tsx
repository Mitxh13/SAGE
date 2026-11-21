import React, { useState } from 'react';
import {
  Activity,
  Award,
  ChevronDown,
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

  if (!isOpen) return null;

  const latestTrace = traces.length > 0 ? traces[traces.length - 1] : null;
  const currentTrace = traces[selectedTraceIndex] || latestTrace;

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

  const currentStageIndex = stages.findIndex((s) => s.key === learnerState?.scaffolding_stage);
  const activeMisconceptions = Object.entries(learnerState?.active_misconceptions || {});

  return (
    <aside className="w-96 bg-cream-50 border-l border-cream-300 flex flex-col h-full z-30 select-none shadow-xl transition-all font-sans">
      {/* 1. Header */}
      <div className="p-4 border-b border-cream-300 flex items-center justify-between bg-cream-150">
        <div className="flex items-center space-x-2.5">
          <div className="w-7 h-7 rounded-lg bg-sage-100 border border-sage-300 flex items-center justify-center text-sage-700">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <h2 className="font-semibold text-sm text-charcoal-900 tracking-tight">
              Pedagogical Telemetry
            </h2>
            <p className="text-[11px] text-charcoal-500">Live Orchestrator State</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-charcoal-400 hover:text-charcoal-800 hover:bg-cream-200 transition-colors"
          title="Close drawer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* 2. Navigation Tabs */}
      <div className="flex border-b border-cream-300 bg-cream-100">
        <button
          onClick={() => setActiveTab('metrics')}
          className={`flex-1 py-2.5 text-xs font-medium text-center transition-all ${
            activeTab === 'metrics'
              ? 'text-sage-800 border-b-2 border-sage-700 bg-white'
              : 'text-charcoal-500 hover:text-charcoal-800'
          }`}
        >
          Learner State
        </button>
        <button
          onClick={() => setActiveTab('trace')}
          className={`flex-1 py-2.5 text-xs font-medium text-center transition-all flex items-center justify-center gap-1.5 ${
            activeTab === 'trace'
              ? 'text-sage-800 border-b-2 border-sage-700 bg-white'
              : 'text-charcoal-500 hover:text-charcoal-800'
          }`}
        >
          <Code2 className="w-3.5 h-3.5" />
          <span>Execution Traces ({traces.length})</span>
        </button>
      </div>

      {/* 3. Tab Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {activeTab === 'metrics' ? (
          <>
            {/* Scaffolding Stage Stepper */}
            <div className="space-y-2">
              <span className="text-[11px] font-semibold text-charcoal-500 uppercase tracking-wider block">
                Scaffolding Escalation
              </span>
              <div className="grid grid-cols-2 gap-2">
                {stages.map((stg, idx) => {
                  const Icon = stg.icon;
                  const isCurrent = stg.key === learnerState?.scaffolding_stage;
                  const isPassed = idx < currentStageIndex;

                  return (
                    <div
                      key={stg.key}
                      className={`p-2.5 rounded-xl border text-xs flex items-center space-x-2 transition-all ${
                        isCurrent
                          ? 'bg-sage-700 text-white border-sage-800 shadow-sage-soft font-medium'
                          : isPassed
                          ? 'bg-sage-50 text-sage-800 border-sage-200'
                          : 'bg-white text-charcoal-400 border-cream-200'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5 shrink-0" />
                      <span className="truncate">{stg.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Core Metrics Cards */}
            <div className="grid grid-cols-2 gap-2.5">
              {/* Struggle Counter */}
              <div className="p-3 rounded-2xl bg-white border border-cream-300 shadow-sm space-y-1">
                <div className="flex items-center space-x-1.5 text-charcoal-500 text-xs">
                  <Flame className="w-3.5 h-3.5 text-amber-600" />
                  <span>Struggle Count</span>
                </div>
                <div className="text-xl font-bold text-charcoal-900">
                  {learnerState?.struggle_turn_count ?? 0}
                  <span className="text-xs font-normal text-charcoal-400 ml-1">turns</span>
                </div>
              </div>

              {/* LCC Score */}
              <div className="p-3 rounded-2xl bg-white border border-cream-300 shadow-sm space-y-1">
                <div className="flex items-center space-x-1.5 text-charcoal-500 text-xs">
                  <Award className="w-3.5 h-3.5 text-sage-600" />
                  <span>LCC Score</span>
                </div>
                <div className="text-xl font-bold text-charcoal-900">
                  {learnerState ? `${(learnerState.overall_lcc_score * 100).toFixed(0)}%` : '0%'}
                </div>
              </div>
            </div>

            {/* Topic Status */}
            <div className="p-3 rounded-2xl bg-white border border-cream-300 shadow-sm space-y-2">
              <span className="text-[11px] font-semibold text-charcoal-500 uppercase tracking-wider block">
                Topic Mastery Status
              </span>
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-charcoal-800">
                  {learnerState?.topic_status || 'IN_PROGRESS'}
                </span>
                <span
                  className={`px-2.5 py-0.5 rounded-full text-[10px] font-medium border ${
                    learnerState?.topic_status === 'DONE'
                      ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                      : 'bg-sage-100 text-sage-800 border-sage-200'
                  }`}
                >
                  {learnerState?.topic_status === 'DONE' ? 'Topic Mastered' : 'In Progress'}
                </span>
              </div>
            </div>

            {/* Active Misconceptions Tracker */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-charcoal-500 uppercase tracking-wider flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                  Active Misconceptions
                </span>
                <span className="text-xs text-charcoal-400 font-mono">
                  {activeMisconceptions.length}
                </span>
              </div>

              {activeMisconceptions.length === 0 ? (
                <div className="p-3 rounded-2xl bg-white border border-cream-300 text-xs text-charcoal-500 text-center">
                  No active misconceptions detected in current session.
                </div>
              ) : (
                <div className="space-y-2">
                  {activeMisconceptions.map(([id, conf]) => (
                    <div
                      key={id}
                      className="p-3 rounded-2xl bg-white border border-cream-300 shadow-sm space-y-1.5"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-charcoal-800 font-mono truncate max-w-[200px]">
                          {id}
                        </span>
                        <span className="text-sage-700 font-medium">
                          {(conf * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="w-full bg-cream-200 h-1.5 rounded-full overflow-hidden">
                        <div
                          className="bg-sage-600 h-full rounded-full transition-all duration-300"
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
              <div className="text-center py-8 text-charcoal-400 text-xs">
                No turn traces logged yet. Send a message to inspect execution.
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold text-charcoal-500 uppercase tracking-wider">
                    Trace Selector
                  </span>
                  <select
                    value={selectedTraceIndex}
                    onChange={(e) => setSelectedTraceIndex(Number(e.target.value))}
                    className="bg-white border border-cream-300 text-charcoal-800 text-xs rounded-xl px-2.5 py-1 focus:outline-none"
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
                    <div className="border border-cream-300 rounded-2xl bg-white overflow-hidden shadow-sm">
                      <button
                        onClick={() => toggleTraceSection('analyzer')}
                        className="w-full px-3.5 py-2.5 bg-cream-100 flex items-center justify-between text-xs font-semibold text-charcoal-800 text-left"
                      >
                        <span>1. Understanding Analyzer</span>
                        {traceExpandedSections.analyzer ? (
                          <ChevronDown className="w-3.5 h-3.5 text-charcoal-400" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5 text-charcoal-400" />
                        )}
                      </button>
                      {traceExpandedSections.analyzer && (
                        <div className="p-3 text-[11px] font-mono text-charcoal-700 bg-cream-50 overflow-x-auto max-h-48">
                          <pre>{JSON.stringify(currentTrace.analyzer_output, null, 2)}</pre>
                        </div>
                      )}
                    </div>

                    {/* Retriever Stage Trace */}
                    <div className="border border-cream-300 rounded-2xl bg-white overflow-hidden shadow-sm">
                      <button
                        onClick={() => toggleTraceSection('retriever')}
                        className="w-full px-3.5 py-2.5 bg-cream-100 flex items-center justify-between text-xs font-semibold text-charcoal-800 text-left"
                      >
                        <span>2. Course Retriever Context</span>
                        {traceExpandedSections.retriever ? (
                          <ChevronDown className="w-3.5 h-3.5 text-charcoal-400" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5 text-charcoal-400" />
                        )}
                      </button>
                      {traceExpandedSections.retriever && (
                        <div className="p-3 text-[11px] font-mono text-charcoal-700 bg-cream-50 overflow-x-auto max-h-48">
                          <pre>{JSON.stringify(currentTrace.retriever_output, null, 2)}</pre>
                        </div>
                      )}
                    </div>

                    {/* Tutor Stage Trace */}
                    <div className="border border-cream-300 rounded-2xl bg-white overflow-hidden shadow-sm">
                      <button
                        onClick={() => toggleTraceSection('tutor')}
                        className="w-full px-3.5 py-2.5 bg-cream-100 flex items-center justify-between text-xs font-semibold text-charcoal-800 text-left"
                      >
                        <span>3. Tutor Agent Scaffolding</span>
                        {traceExpandedSections.tutor ? (
                          <ChevronDown className="w-3.5 h-3.5 text-charcoal-400" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5 text-charcoal-400" />
                        )}
                      </button>
                      {traceExpandedSections.tutor && (
                        <div className="p-3 text-[11px] font-mono text-charcoal-700 bg-cream-50 overflow-x-auto max-h-48">
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
