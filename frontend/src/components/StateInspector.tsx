import React, { useState } from 'react';
import {
  Activity,
  Award,
  ChevronDown,
  ChevronRight,
  Code2,
  Gauge,
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
    { key: 'QUESTION', label: '1. Question', icon: HelpCircle, color: 'text-blue-400 border-blue-500/40 bg-blue-500/10' },
    { key: 'HINT', label: '2. Hint', icon: Lightbulb, color: 'text-amber-400 border-amber-500/40 bg-amber-500/10' },
    { key: 'EXPLANATION', label: '3. Explanation', icon: BookOpen, color: 'text-purple-400 border-purple-500/40 bg-purple-500/10' },
    { key: 'WRAP_UP', label: '4. Wrap-up', icon: CheckCircle, color: 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10' },
  ];

  const currentStageIndex = stages.findIndex((s) => s.key === learnerState?.scaffolding_stage);
  const activeMisconceptions = Object.entries(learnerState?.active_misconceptions || {});

  return (
    <aside className="w-96 bg-gemini-800 border-l border-gemini-700/60 flex flex-col h-full z-30 select-none shadow-2xl transition-all font-sans">
      {/* 1. Header */}
      <div className="p-4 border-b border-gemini-700/60 flex items-center justify-between bg-gemini-850">
        <div className="flex items-center space-x-2.5">
          <div className="w-6 h-6 rounded-lg bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
            <Activity className="w-3.5 h-3.5" />
          </div>
          <h2 className="font-semibold text-sm text-gemini-100 tracking-tight">
            X-Ray State Inspector
          </h2>
        </div>
        <button
          onClick={onClose}
          className="p-1.5 rounded-full text-gemini-400 hover:text-gemini-100 hover:bg-gemini-700 transition-colors"
          title="Close drawer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* 2. Tabs */}
      <div className="flex border-b border-gemini-700/60 text-xs font-medium bg-gemini-850/50">
        <button
          onClick={() => setActiveTab('metrics')}
          className={`flex-1 py-3 text-center border-b-2 transition-all flex items-center justify-center gap-2 ${
            activeTab === 'metrics'
              ? 'border-blue-500 text-blue-300 bg-gemini-800'
              : 'border-transparent text-gemini-400 hover:text-gemini-200'
          }`}
        >
          <Gauge className="w-3.5 h-3.5" />
          <span>Learner Telemetry</span>
        </button>
        <button
          onClick={() => setActiveTab('trace')}
          className={`flex-1 py-3 text-center border-b-2 transition-all flex items-center justify-center gap-2 ${
            activeTab === 'trace'
              ? 'border-blue-500 text-blue-300 bg-gemini-800'
              : 'border-transparent text-gemini-400 hover:text-gemini-200'
          }`}
        >
          <Code2 className="w-3.5 h-3.5" />
          <span>Pipeline Trace ({traces.length})</span>
        </button>
      </div>

      {/* 3. Tab Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5">
        {activeTab === 'metrics' ? (
          <>
            {/* Scaffolding Stage Stepper */}
            <div className="p-4 rounded-2xl bg-gemini-750 border border-gemini-700/60 space-y-3 shadow-sm">
              <span className="text-[11px] font-semibold text-gemini-400 uppercase tracking-wider block">
                Active Scaffolding Stage
              </span>
              <div className="grid grid-cols-2 gap-2">
                {stages.map((stage, idx) => {
                  const Icon = stage.icon;
                  const isActive = stage.key === learnerState?.scaffolding_stage;
                  const isPassed = currentStageIndex > idx;
                  return (
                    <div
                      key={stage.key}
                      className={`p-2.5 rounded-xl border text-xs flex items-center space-x-2 transition-all ${
                        isActive
                          ? `${stage.color} font-semibold shadow-sm ring-1 ring-white/10`
                          : isPassed
                          ? 'border-gemini-600/40 bg-gemini-800/40 text-gemini-400 line-through'
                          : 'border-gemini-700/30 bg-gemini-800/20 text-gemini-500'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5 shrink-0" />
                      <span className="truncate">{stage.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Core Cognitive Telemetry */}
            <div className="grid grid-cols-2 gap-3">
              {/* Struggle Counter */}
              <div className="p-3.5 rounded-2xl bg-gemini-750 border border-gemini-700/60 shadow-sm">
                <div className="flex items-center space-x-2 text-gemini-400 text-xs mb-1">
                  <Flame className="w-3.5 h-3.5 text-amber-400" />
                  <span>Struggle Count</span>
                </div>
                <div className="text-xl font-bold text-gemini-100">
                  {learnerState?.struggle_turn_count ?? 0}
                  <span className="text-xs font-normal text-gemini-400 ml-1">turns</span>
                </div>
                <p className="text-[10px] text-gemini-400 mt-1">
                  {learnerState?.struggle_turn_count && learnerState.struggle_turn_count >= 2
                    ? 'Escalation triggered'
                    : 'Exploring conceptually'}
                </p>
              </div>

              {/* Hu et al. LCC Mastery Score */}
              <div className="p-3.5 rounded-2xl bg-gemini-750 border border-gemini-700/60 shadow-sm">
                <div className="flex items-center space-x-2 text-gemini-400 text-xs mb-1">
                  <Award className="w-3.5 h-3.5 text-blue-400" />
                  <span>LCC Mastery</span>
                </div>
                <div className="text-xl font-bold text-gemini-100">
                  {learnerState?.overall_lcc_score ? learnerState.overall_lcc_score.toFixed(2) : '0.00'}
                  <span className="text-xs font-normal text-gemini-400 ml-1">/ 1.0</span>
                </div>
                <p className="text-[10px] text-gemini-400 mt-1">
                  Topic: {learnerState?.topic_status || 'IN_PROGRESS'}
                </p>
              </div>
            </div>

            {/* Misconception Progress Meters (Thonge & Thakkar) */}
            <div className="p-4 rounded-2xl bg-gemini-750 border border-gemini-700/60 space-y-3 shadow-sm">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-semibold text-gemini-400 uppercase tracking-wider flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                  Active Misconceptions ({activeMisconceptions.length})
                </span>
                <span className="text-[10px] text-gemini-500">Confidence</span>
              </div>

              {activeMisconceptions.length === 0 ? (
                <div className="text-center py-6 text-xs text-gemini-400 border border-dashed border-gemini-700 rounded-xl">
                  ✨ No active cognitive misconceptions detected.
                </div>
              ) : (
                <div className="space-y-3">
                  {activeMisconceptions.map(([miscId, confidence]) => {
                    const pct = Math.round(confidence * 100);
                    return (
                      <div key={miscId} className="space-y-1.5">
                        <div className="flex justify-between text-xs">
                          <span className="font-mono text-[11px] text-gemini-300 truncate max-w-[200px]">
                            {miscId.replace('misc_', '').replace(/_/g, ' ')}
                          </span>
                          <span className="font-semibold text-amber-300">{pct}%</span>
                        </div>
                        <div className="w-full h-1.5 bg-gemini-800 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              pct >= 70
                                ? 'bg-rose-500'
                                : pct >= 40
                                ? 'bg-amber-400'
                                : 'bg-blue-400'
                            }`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </>
        ) : (
          /* Pipeline Trace Tab */
          <div className="space-y-4">
            {traces.length === 0 ? (
              <div className="text-center py-12 text-xs text-gemini-400">
                No turn traces recorded yet. Send a message to inspect execution telemetry.
              </div>
            ) : (
              <>
                {/* Turn Selector Chips */}
                <div className="flex items-center space-x-1.5 overflow-x-auto pb-1">
                  {traces.map((_, idx) => (
                    <button
                      key={idx}
                      onClick={() => setSelectedTraceIndex(idx)}
                      className={`px-3 py-1 rounded-full text-xs font-mono transition-all ${
                        selectedTraceIndex === idx
                          ? 'bg-blue-600 text-white shadow-sm'
                          : 'bg-gemini-750 text-gemini-400 hover:bg-gemini-700'
                      }`}
                    >
                      Turn {idx + 1}
                    </button>
                  ))}
                </div>

                {currentTrace && (
                  <div className="space-y-3 text-xs">
                    {/* Execution Latency Card */}
                    <div className="p-3 rounded-xl bg-gemini-750 border border-gemini-700/60 flex items-center justify-between text-gemini-300">
                      <span>Turn Pipeline Latency</span>
                      <span className="font-mono font-bold text-gemini-100">
                        {currentTrace.latency_ms} ms
                      </span>
                    </div>

                    {/* Analyzer Output Accordion */}
                    <div className="rounded-xl bg-gemini-750 border border-gemini-700/60 overflow-hidden">
                      <button
                        onClick={() => toggleTraceSection('analyzer')}
                        className="w-full p-3 text-left font-semibold text-gemini-200 flex items-center justify-between hover:bg-gemini-700/50"
                      >
                        <span>1. Understanding Analyzer Output</span>
                        {traceExpandedSections.analyzer ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                      </button>
                      {traceExpandedSections.analyzer && (
                        <div className="p-3 bg-gemini-900 border-t border-gemini-700/60">
                          <pre className="font-mono text-[10px] text-emerald-300 overflow-x-auto whitespace-pre-wrap">
                            {JSON.stringify(currentTrace.analyzer_output, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>

                    {/* Retriever Output Accordion */}
                    <div className="rounded-xl bg-gemini-750 border border-gemini-700/60 overflow-hidden">
                      <button
                        onClick={() => toggleTraceSection('retriever')}
                        className="w-full p-3 text-left font-semibold text-gemini-200 flex items-center justify-between hover:bg-gemini-700/50"
                      >
                        <span>2. Course Retriever Output</span>
                        {traceExpandedSections.retriever ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                      </button>
                      {traceExpandedSections.retriever && (
                        <div className="p-3 bg-gemini-900 border-t border-gemini-700/60">
                          <pre className="font-mono text-[10px] text-amber-300 overflow-x-auto whitespace-pre-wrap">
                            {JSON.stringify(currentTrace.retriever_output, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>

                    {/* Tutor Output Accordion */}
                    <div className="rounded-xl bg-gemini-750 border border-gemini-700/60 overflow-hidden">
                      <button
                        onClick={() => toggleTraceSection('tutor')}
                        className="w-full p-3 text-left font-semibold text-gemini-200 flex items-center justify-between hover:bg-gemini-700/50"
                      >
                        <span>3. Socratic Tutor Output</span>
                        {traceExpandedSections.tutor ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                      </button>
                      {traceExpandedSections.tutor && (
                        <div className="p-3 bg-gemini-900 border-t border-gemini-700/60">
                          <pre className="font-mono text-[10px] text-blue-300 overflow-x-auto whitespace-pre-wrap">
                            {JSON.stringify(currentTrace.tutor_output, null, 2)}
                          </pre>
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
