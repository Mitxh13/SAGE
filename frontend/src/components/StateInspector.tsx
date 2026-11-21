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
    <aside className="w-96 bg-cream-200 border-l border-cream-300 flex flex-col h-full z-30 select-none shadow-sage-lg transition-all font-sans">
      {/* 1. Header */}
      <div className="p-4 border-b border-cream-300 flex items-center justify-between bg-cream-300/40">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-sage-700 text-cream-50 flex items-center justify-center shadow-sage-sm">
            <Activity className="w-4 h-4 text-cream-100" />
          </div>
          <div>
            <h2 className="font-bold text-sm text-sage-950 tracking-tight">
              Pedagogical Telemetry
            </h2>
            <p className="text-[11px] text-sage-700 font-medium">Live Orchestrator State</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-lg text-sage-700 hover:text-sage-950 hover:bg-cream-300 transition-colors"
          title="Close drawer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* 2. Navigation Tabs */}
      <div className="flex border-b border-cream-300 bg-cream-200">
        <button
          onClick={() => setActiveTab('metrics')}
          className={`flex-1 py-2.5 text-xs font-bold text-center transition-all ${
            activeTab === 'metrics'
              ? 'text-sage-950 border-b-2 border-sage-700 bg-cream-100 shadow-sm'
              : 'text-sage-700 hover:text-sage-950'
          }`}
        >
          Learner State
        </button>
        <button
          onClick={() => setActiveTab('trace')}
          className={`flex-1 py-2.5 text-xs font-bold text-center transition-all flex items-center justify-center gap-1.5 ${
            activeTab === 'trace'
              ? 'text-sage-950 border-b-2 border-sage-700 bg-cream-100 shadow-sm'
              : 'text-sage-700 hover:text-sage-950'
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
              <span className="text-[11px] font-bold text-sage-800 uppercase tracking-wider block">
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
                          ? 'bg-sage-700 text-cream-50 border-sage-800 shadow-sage-sm font-bold'
                          : isPassed
                          ? 'bg-sage-200 text-sage-950 border-sage-300 font-semibold'
                          : 'bg-sage-50 text-sage-600 border-sage-200 font-medium'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5 shrink-0" />
                      <span className="truncate">{stg.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Core Metrics Cards (Sage Components) */}
            <div className="grid grid-cols-2 gap-2.5">
              {/* Struggle Counter */}
              <div className="p-3 rounded-2xl bg-sage-100 border border-sage-300 shadow-sage-sm space-y-1">
                <div className="flex items-center space-x-1.5 text-sage-800 text-xs font-semibold">
                  <Flame className="w-3.5 h-3.5 text-sage-700" />
                  <span>Struggle Count</span>
                </div>
                <div className="text-2xl font-extrabold text-sage-950">
                  {learnerState?.struggle_turn_count ?? 0}
                  <span className="text-xs font-normal text-sage-700 ml-1">turns</span>
                </div>
              </div>

              {/* LCC Score */}
              <div className="p-3 rounded-2xl bg-sage-100 border border-sage-300 shadow-sage-sm space-y-1">
                <div className="flex items-center space-x-1.5 text-sage-800 text-xs font-semibold">
                  <Award className="w-3.5 h-3.5 text-sage-700" />
                  <span>LCC Score</span>
                </div>
                <div className="text-2xl font-extrabold text-sage-950">
                  {learnerState ? `${(learnerState.overall_lcc_score * 100).toFixed(0)}%` : '0%'}
                </div>
              </div>
            </div>

            {/* Topic Status */}
            <div className="p-3 rounded-2xl bg-sage-100 border border-sage-300 shadow-sage-sm space-y-2">
              <span className="text-[11px] font-bold text-sage-800 uppercase tracking-wider block">
                Topic Mastery Status
              </span>
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-sage-950">
                  {learnerState?.topic_status || 'IN_PROGRESS'}
                </span>
                <span
                  className={`px-3 py-1 rounded-full text-[10px] font-bold border ${
                    learnerState?.topic_status === 'DONE'
                      ? 'bg-sage-700 text-cream-50 border-sage-800 shadow-sage-sm'
                      : 'bg-sage-200 text-sage-900 border-sage-300'
                  }`}
                >
                  {learnerState?.topic_status === 'DONE' ? 'Topic Mastered' : 'In Progress'}
                </span>
              </div>
            </div>

            {/* Active Misconceptions Tracker */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-sage-800 uppercase tracking-wider flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-sage-700" />
                  Active Misconceptions
                </span>
                <span className="text-xs text-sage-700 font-mono font-bold">
                  {activeMisconceptions.length}
                </span>
              </div>

              {activeMisconceptions.length === 0 ? (
                <div className="p-3 rounded-2xl bg-sage-100 border border-sage-300 text-xs text-sage-700 text-center font-medium">
                  No active misconceptions detected in current session.
                </div>
              ) : (
                <div className="space-y-2">
                  {activeMisconceptions.map(([id, conf]) => (
                    <div
                      key={id}
                      className="p-3 rounded-2xl bg-sage-50 border border-sage-300 shadow-sage-sm space-y-1.5"
                    >
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold text-sage-950 font-mono truncate max-w-[200px]">
                          {id}
                        </span>
                        <span className="text-sage-800 font-bold">
                          {(conf * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="w-full bg-sage-200 h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-sage-700 h-full rounded-full transition-all duration-300"
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
              <div className="text-center py-8 text-sage-700 text-xs font-medium">
                No turn traces logged yet. Send a message to inspect execution.
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold text-sage-800 uppercase tracking-wider">
                    Trace Selector
                  </span>
                  <select
                    value={selectedTraceIndex}
                    onChange={(e) => setSelectedTraceIndex(Number(e.target.value))}
                    className="bg-sage-100 border border-sage-300 text-sage-950 font-semibold text-xs rounded-xl px-2.5 py-1 focus:outline-none"
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
                    <div className="border border-sage-300 rounded-2xl bg-sage-50 overflow-hidden shadow-sage-sm">
                      <button
                        onClick={() => toggleTraceSection('analyzer')}
                        className="w-full px-3.5 py-2.5 bg-sage-200 flex items-center justify-between text-xs font-bold text-sage-950 text-left"
                      >
                        <span>1. Understanding Analyzer</span>
                        {traceExpandedSections.analyzer ? (
                          <ChevronDown className="w-3.5 h-3.5 text-sage-700" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5 text-sage-700" />
                        )}
                      </button>
                      {traceExpandedSections.analyzer && (
                        <div className="p-3 text-[11px] font-mono text-sage-950 bg-sage-50 overflow-x-auto max-h-48">
                          <pre>{JSON.stringify(currentTrace.analyzer_output, null, 2)}</pre>
                        </div>
                      )}
                    </div>

                    {/* Retriever Stage Trace */}
                    <div className="border border-sage-300 rounded-2xl bg-sage-50 overflow-hidden shadow-sage-sm">
                      <button
                        onClick={() => toggleTraceSection('retriever')}
                        className="w-full px-3.5 py-2.5 bg-sage-200 flex items-center justify-between text-xs font-bold text-sage-950 text-left"
                      >
                        <span>2. Course Retriever Context</span>
                        {traceExpandedSections.retriever ? (
                          <ChevronDown className="w-3.5 h-3.5 text-sage-700" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5 text-sage-700" />
                        )}
                      </button>
                      {traceExpandedSections.retriever && (
                        <div className="p-3 text-[11px] font-mono text-sage-950 bg-sage-50 overflow-x-auto max-h-48">
                          <pre>{JSON.stringify(currentTrace.retriever_output, null, 2)}</pre>
                        </div>
                      )}
                    </div>

                    {/* Tutor Stage Trace */}
                    <div className="border border-sage-300 rounded-2xl bg-sage-50 overflow-hidden shadow-sage-sm">
                      <button
                        onClick={() => toggleTraceSection('tutor')}
                        className="w-full px-3.5 py-2.5 bg-sage-200 flex items-center justify-between text-xs font-bold text-sage-950 text-left"
                      >
                        <span>3. Tutor Agent Scaffolding</span>
                        {traceExpandedSections.tutor ? (
                          <ChevronDown className="w-3.5 h-3.5 text-sage-700" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5 text-sage-700" />
                        )}
                      </button>
                      {traceExpandedSections.tutor && (
                        <div className="p-3 text-[11px] font-mono text-sage-950 bg-sage-50 overflow-x-auto max-h-48">
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
