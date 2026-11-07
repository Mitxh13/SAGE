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
    { key: 'QUESTION', label: '1. Question', icon: HelpCircle, color: 'text-sky-400 border-sky-500/40 bg-sky-500/10' },
    { key: 'HINT', label: '2. Hint', icon: Lightbulb, color: 'text-amber-400 border-amber-500/40 bg-amber-500/10' },
    { key: 'EXPLANATION', label: '3. Explanation', icon: BookOpen, color: 'text-purple-400 border-purple-500/40 bg-purple-500/10' },
    { key: 'WRAP_UP', label: '4. Wrap-up', icon: CheckCircle, color: 'text-emerald-400 border-emerald-500/40 bg-emerald-500/10' },
  ];

  return (
    <aside className="w-96 bg-slate-950 border-l border-slate-800 flex flex-col h-full z-20 select-none shadow-2xl">
      {/* Drawer Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950">
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-emerald-400" />
          <h2 className="font-semibold text-sm text-slate-100 tracking-tight">
            X-Ray State Inspector
          </h2>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800 text-xs font-medium">
        <button
          onClick={() => setActiveTab('metrics')}
          className={`flex-1 py-2.5 text-center border-b-2 transition-all flex items-center justify-center gap-1.5 ${
            activeTab === 'metrics'
              ? 'border-emerald-500 text-emerald-300 bg-emerald-950/20'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Gauge className="w-3.5 h-3.5" />
          <span>Learner Telemetry</span>
        </button>
        <button
          onClick={() => setActiveTab('trace')}
          className={`flex-1 py-2.5 text-center border-b-2 transition-all flex items-center justify-center gap-1.5 ${
            activeTab === 'trace'
              ? 'border-emerald-500 text-emerald-300 bg-emerald-950/20'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Code2 className="w-3.5 h-3.5" />
          <span>Pipeline Trace ({traces.length})</span>
        </button>
      </div>

      {/* Drawer Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {activeTab === 'metrics' ? (
          <>
            {/* Scaffolding Stage Stepper */}
            <div>
              <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2.5">
                Current Scaffolding Stage
              </span>
              <div className="grid grid-cols-2 gap-2">
                {stages.map((st) => {
                  const isActive = learnerState?.scaffolding_stage === st.key;
                  const Icon = st.icon;
                  return (
                    <div
                      key={st.key}
                      className={`p-2.5 rounded-lg border text-xs flex items-center space-x-2 transition-all ${
                        isActive
                          ? `${st.color} shadow-sm font-semibold`
                          : 'border-slate-800/80 bg-slate-900/40 text-slate-500'
                      }`}
                    >
                      <Icon className="w-4 h-4 shrink-0" />
                      <span className="truncate">{st.label}</span>
                    </div>
                  );
                })}
              </div>

              {/* Struggle Counter */}
              <div className="mt-3 p-2.5 rounded-lg bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs">
                <span className="text-slate-400">Consecutive Struggle Turns:</span>
                <span className={`font-mono font-bold px-2 py-0.5 rounded ${
                  (learnerState?.struggle_turn_count || 0) >= 4
                    ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30'
                    : (learnerState?.struggle_turn_count || 0) >= 2
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                    : 'bg-slate-800 text-slate-300'
                }`}>
                  {learnerState?.struggle_turn_count ?? 0}
                </span>
              </div>
            </div>

            {/* Active Misconceptions */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Active Misconceptions
                </span>
                <span className="text-[10px] text-slate-500">Threshold: &lt; 0.18</span>
              </div>

              {!learnerState || Object.keys(learnerState.active_misconceptions || {}).length === 0 ? (
                <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/30 text-emerald-400 text-xs flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 shrink-0" />
                  <span>No unresolved misconceptions.</span>
                </div>
              ) : (
                <div className="space-y-3">
                  {Object.entries(learnerState.active_misconceptions).map(([id, conf]) => {
                    const pct = Math.min(100, Math.round(conf * 100));
                    const isHigh = conf >= 0.65;
                    const isLow = conf < 0.30;
                    return (
                      <div key={id} className="p-2.5 rounded-lg bg-slate-900 border border-slate-800 text-xs space-y-1.5">
                        <div className="flex items-center justify-between font-mono">
                          <span className="text-slate-300 text-[11px] truncate max-w-[200px]" title={id}>
                            {id}
                          </span>
                          <span className={`font-bold ${isHigh ? 'text-amber-400' : isLow ? 'text-emerald-400' : 'text-slate-300'}`}>
                            {conf.toFixed(2)}
                          </span>
                        </div>
                        {/* Progress Bar with 0.18 threshold marker */}
                        <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden relative">
                          <div
                            className={`h-full transition-all duration-500 ${
                              isHigh ? 'bg-amber-500' : isLow ? 'bg-emerald-500' : 'bg-sky-500'
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

            {/* LCC Score Mastery Progress */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Award className="w-3.5 h-3.5 text-emerald-400" /> LCC Mastery Score
                </span>
                <span className="text-[10px] text-slate-500">Done at &gt; 0.80</span>
              </div>

              <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-2.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Overall Score:</span>
                  <span className={`font-mono font-bold text-sm ${
                    (learnerState?.overall_lcc_score || 0) >= 0.8
                      ? 'text-emerald-400'
                      : (learnerState?.overall_lcc_score || 0) < 0
                      ? 'text-rose-400'
                      : 'text-slate-200'
                  }`}>
                    {learnerState?.overall_lcc_score?.toFixed(2) ?? '0.00'}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px] pt-2 border-t border-slate-800">
                  <div className="bg-slate-950 p-2 rounded border border-slate-800/80">
                    <span className="text-slate-500 block text-[10px]">Accum. Correct (RN+RO)</span>
                    <span className="text-emerald-400 font-mono font-bold">
                      +{learnerState?.accumulated_correct_score?.toFixed(2) ?? '0.00'}
                    </span>
                  </div>
                  <div className="bg-slate-950 p-2 rounded border border-slate-800/80">
                    <span className="text-slate-500 block text-[10px]">Accum. Wrong (IN+IO)</span>
                    <span className="text-rose-400 font-mono font-bold">
                      -{learnerState?.accumulated_wrong_score?.toFixed(2) ?? '0.00'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </>
        ) : (
          /* Pipeline Trace JSON Inspector */
          <div className="space-y-4">
            {/* Trace Selector */}
            {traces.length > 1 && (
              <div className="flex items-center gap-1 overflow-x-auto pb-1 text-xs">
                {traces.map((_, i) => (
                  <button
                    key={i}
                    onClick={() => setSelectedTraceIndex(i)}
                    className={`px-2.5 py-1 rounded text-[11px] font-mono transition-colors shrink-0 ${
                      selectedTraceIndex === i
                        ? 'bg-emerald-600 text-white font-bold'
                        : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
                    }`}
                  >
                    Turn {i + 1}
                  </button>
                ))}
              </div>
            )}

            {!currentTrace ? (
              <div className="text-center py-10 text-xs text-slate-500">
                No telemetry traces recorded yet.
              </div>
            ) : (
              <div className="space-y-3">
                <div className="text-[11px] text-slate-400 flex items-center justify-between pb-1 border-b border-slate-800">
                  <span>Turn {currentTrace.turn_index} Execution Trace</span>
                  <span className="font-mono text-emerald-400">{currentTrace.latency_ms} ms</span>
                </div>

                {/* Analyzer Payload */}
                <div className="rounded-lg bg-slate-900 border border-slate-800 overflow-hidden text-xs">
                  <button
                    onClick={() => toggleTraceSection('analyzer')}
                    className="w-full p-2.5 bg-slate-800/50 flex items-center justify-between font-medium text-slate-300 hover:bg-slate-800 transition-colors"
                  >
                    <span>1. Understanding Analyzer (Nidhi)</span>
                    {traceExpandedSections.analyzer ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                  </button>
                  {traceExpandedSections.analyzer && (
                    <pre className="p-3 text-[10px] text-slate-300 font-mono overflow-x-auto bg-slate-950">
                      {JSON.stringify(currentTrace.analyzer_output, null, 2)}
                    </pre>
                  )}
                </div>

                {/* Retriever Payload */}
                <div className="rounded-lg bg-slate-900 border border-slate-800 overflow-hidden text-xs">
                  <button
                    onClick={() => toggleTraceSection('retriever')}
                    className="w-full p-2.5 bg-slate-800/50 flex items-center justify-between font-medium text-slate-300 hover:bg-slate-800 transition-colors"
                  >
                    <span>2. Course Retriever (Jignas)</span>
                    {traceExpandedSections.retriever ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                  </button>
                  {traceExpandedSections.retriever && (
                    <pre className="p-3 text-[10px] text-slate-300 font-mono overflow-x-auto bg-slate-950">
                      {JSON.stringify(currentTrace.retriever_output, null, 2)}
                    </pre>
                  )}
                </div>

                {/* Tutor Payload */}
                <div className="rounded-lg bg-slate-900 border border-slate-800 overflow-hidden text-xs">
                  <button
                    onClick={() => toggleTraceSection('tutor')}
                    className="w-full p-2.5 bg-slate-800/50 flex items-center justify-between font-medium text-slate-300 hover:bg-slate-800 transition-colors"
                  >
                    <span>3. Socratic Tutor Reasoning (Tahir)</span>
                    {traceExpandedSections.tutor ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
                  </button>
                  {traceExpandedSections.tutor && (
                    <pre className="p-3 text-[10px] text-slate-300 font-mono overflow-x-auto bg-slate-950">
                      {JSON.stringify(currentTrace.tutor_output, null, 2)}
                    </pre>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </aside>
  );
};
