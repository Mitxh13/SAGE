import React from 'react';
import { BookOpen, Plus, MessageSquare, Sparkles, Clock } from 'lucide-react';
import { SessionSummary, UnitSummary } from '../types/sage';

interface SidebarProps {
  units: UnitSummary[];
  selectedUnitId: string;
  onSelectUnit: (unitId: string) => void;
  sessions: SessionSummary[];
  activeSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onNewSession: () => void;
  isLoading: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  units,
  selectedUnitId,
  onSelectUnit,
  sessions,
  activeSessionId,
  onSelectSession,
  onNewSession,
  isLoading,
}) => {
  return (
    <aside className="w-80 bg-slate-950 border-r border-slate-800 flex flex-col h-full select-none">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h1 className="font-bold text-slate-100 tracking-tight text-base flex items-center gap-1.5">
              SAGE <span className="text-[10px] font-medium bg-emerald-500/20 text-emerald-300 px-1.5 py-0.5 rounded border border-emerald-500/30">Tutor</span>
            </h1>
            <p className="text-[11px] text-slate-400">Prompt Engineering & GenAI</p>
          </div>
        </div>

        <button
          onClick={onNewSession}
          disabled={isLoading}
          className="p-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition-colors disabled:opacity-50"
          title="New Tutoring Session"
        >
          <Plus className="w-4 h-4" />
        </button>
      </div>

      {/* Unit Selector */}
      <div className="p-3 border-b border-slate-800">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2 px-1">
          Course Units
        </span>
        <div className="space-y-1">
          {units.map((unit) => {
            const isSelected = unit.unit_id === selectedUnitId;
            return (
              <button
                key={unit.unit_id}
                onClick={() => onSelectUnit(unit.unit_id)}
                className={`w-full text-left p-2 rounded-lg text-xs transition-all flex items-start space-x-2 ${
                  isSelected
                    ? 'bg-emerald-950/70 border border-emerald-500/40 text-emerald-200'
                    : 'text-slate-300 hover:bg-slate-900 border border-transparent'
                }`}
              >
                <BookOpen className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${isSelected ? 'text-emerald-400' : 'text-slate-500'}`} />
                <span className="line-clamp-2 leading-relaxed">{unit.title}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Session History */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2 px-1">
          Past Sessions
        </span>
        {sessions.length === 0 ? (
          <div className="text-center py-8 text-xs text-slate-500">
            No past sessions yet.
          </div>
        ) : (
          sessions.map((sess) => {
            const isActive = sess.session_id === activeSessionId;
            return (
              <button
                key={sess.session_id}
                onClick={() => onSelectSession(sess.session_id)}
                className={`w-full text-left p-2.5 rounded-lg text-xs transition-all flex items-start space-x-2.5 ${
                  isActive
                    ? 'bg-slate-800 border border-slate-700 text-slate-100 shadow-sm'
                    : 'text-slate-400 hover:bg-slate-900/60 hover:text-slate-200 border border-transparent'
                }`}
              >
                <MessageSquare className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${isActive ? 'text-emerald-400' : 'text-slate-500'}`} />
                <div className="flex-1 min-w-0">
                  <p className="truncate font-medium">{sess.title}</p>
                  <p className="text-[10px] text-slate-500 flex items-center gap-1 mt-0.5">
                    <Clock className="w-2.5 h-2.5" />
                    {new Date(sess.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </p>
                </div>
              </button>
            );
          })
        )}
      </div>

      {/* Footer Info */}
      <div className="p-3 border-t border-slate-800 bg-slate-950/60 text-[11px] text-slate-500 flex items-center justify-between">
        <span>Team 08 • SAGE</span>
        <span className="text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-slate-400">Mock AI Mode</span>
      </div>
    </aside>
  );
};
