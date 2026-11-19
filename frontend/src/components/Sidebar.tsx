import React, { useState } from 'react';
import {
  Sparkles,
  Plus,
  BookOpen,
  MessageSquare,
  Settings,
  ChevronLeft,
  ChevronRight,
  Compass,
  CheckCircle2,
  Trash2,
} from 'lucide-react';
import { SessionSummary, UnitSummary } from '../types/sage';

interface SidebarProps {
  units: UnitSummary[];
  selectedUnitId: string;
  onSelectUnit: (unitId: string) => void;
  sessions: SessionSummary[];
  activeSessionId: string | null;
  onSelectSession: (sessionId: string) => void;
  onDeleteSession: (sessionId: string) => void;
  onNewSession: () => void;
  isLoading: boolean;
  isOpen: boolean;
  onToggleOpen: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  units,
  selectedUnitId,
  onSelectUnit,
  sessions,
  activeSessionId,
  onSelectSession,
  onDeleteSession,
  onNewSession,
  isLoading,
  isOpen,
  onToggleOpen,
}) => {
  const [unitsExpanded, setUnitsExpanded] = useState<boolean>(true);

  if (!isOpen) {
    return (
      <aside className="w-16 bg-gemini-800 border-r border-gemini-700/50 flex flex-col items-center py-4 justify-between h-full z-20 transition-all duration-200">
        <div className="flex flex-col items-center space-y-4">
          <button
            onClick={onToggleOpen}
            className="p-2.5 rounded-full hover:bg-gemini-700 text-gemini-400 hover:text-gemini-200 transition-colors"
            title="Expand sidebar"
          >
            <ChevronRight className="w-5 h-5" />
          </button>

          <button
            onClick={onNewSession}
            disabled={isLoading}
            className="w-10 h-10 rounded-full bg-gemini-700 hover:bg-gemini-600 text-gemini-200 flex items-center justify-center transition-all hover:scale-105 shadow-sm"
            title="New Chat (Ctrl+Shift+O)"
          >
            <Plus className="w-5 h-5" />
          </button>
        </div>

        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-amber-500 to-rose-500 flex items-center justify-center text-xs font-bold text-white shadow-sm">
            M
          </div>
        </div>
      </aside>
    );
  }

  return (
    <aside className="w-72 bg-gemini-800 border-r border-gemini-700/50 flex flex-col h-full z-20 select-none transition-all duration-200">
      {/* 1. Header with Logo & Collapse button */}
      <div className="p-4 flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500 via-purple-500 to-amber-500 p-0.5 flex items-center justify-center shadow-md">
            <div className="w-full h-full bg-gemini-900 rounded-[6px] flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-amber-300" />
            </div>
          </div>
          <span className="font-semibold text-gemini-100 text-base tracking-tight flex items-center gap-1.5">
            SAGE
            <span className="text-[10px] font-medium bg-gemini-700 text-gemini-300 px-1.5 py-0.5 rounded-full border border-gemini-600/60">
              AI Tutor
            </span>
          </span>
        </div>

        <button
          onClick={onToggleOpen}
          className="p-1.5 rounded-full hover:bg-gemini-700 text-gemini-400 hover:text-gemini-200 transition-colors"
          title="Collapse sidebar"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
      </div>

      {/* 2. New Chat Pill Button (Gemini Style) */}
      <div className="px-4 py-2">
        <button
          onClick={onNewSession}
          disabled={isLoading}
          className="w-full py-2.5 px-4 rounded-full bg-gemini-700 hover:bg-gemini-600/90 text-gemini-100 text-xs font-medium flex items-center justify-between transition-all shadow-sm border border-gemini-600/40 disabled:opacity-50 group"
        >
          <div className="flex items-center space-x-2.5">
            <Plus className="w-4 h-4 text-gemini-300 group-hover:text-white transition-colors" />
            <span>New chat</span>
          </div>
          <span className="text-[10px] text-gemini-400 bg-gemini-800 px-2 py-0.5 rounded-full border border-gemini-700 font-mono">
            Ctrl+N
          </span>
        </button>
      </div>

      {/* 3. Course Units Section */}
      <div className="px-4 py-3">
        <div className="flex items-center justify-between mb-2 px-1">
          <span className="text-[11px] font-semibold text-gemini-400 uppercase tracking-wider flex items-center gap-1.5">
            <Compass className="w-3.5 h-3.5" />
            Course Units
          </span>
          <button
            onClick={() => setUnitsExpanded(!unitsExpanded)}
            className="text-[10px] text-gemini-400 hover:text-gemini-200"
          >
            {unitsExpanded ? 'Hide' : 'Show'}
          </button>
        </div>

        {unitsExpanded && (
          <div className="space-y-1">
            {units.map((unit) => {
              const isSelected = unit.unit_id === selectedUnitId;
              return (
                <button
                  key={unit.unit_id}
                  onClick={() => onSelectUnit(unit.unit_id)}
                  className={`w-full text-left px-3 py-2 rounded-xl text-xs transition-all flex items-start space-x-2.5 ${
                    isSelected
                      ? 'bg-gemini-700 text-gemini-100 font-medium shadow-sm border border-gemini-600/60'
                      : 'text-gemini-400 hover:bg-gemini-750 hover:text-gemini-200 border border-transparent'
                  }`}
                >
                  <BookOpen className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${isSelected ? 'text-amber-400' : 'text-gemini-500'}`} />
                  <span className="line-clamp-1 leading-snug">{unit.title}</span>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* 4. Recent Conversations History */}
      <div className="flex-1 overflow-y-auto px-4 py-2 space-y-1">
        <span className="text-[11px] font-semibold text-gemini-400 uppercase tracking-wider block mb-2 px-1">
          Recent Sessions
        </span>

        {sessions.length === 0 ? (
          <div className="text-center py-6 text-xs text-gemini-500">
            No previous sessions.
          </div>
        ) : (
          sessions.map((sess) => {
            const isActive = sess.session_id === activeSessionId;
            return (
              <div
                key={sess.session_id}
                onClick={() => onSelectSession(sess.session_id)}
                className={`group w-full text-left px-3 py-2 rounded-xl text-xs transition-all flex items-center space-x-2.5 cursor-pointer ${
                  isActive
                    ? 'bg-gemini-700 text-gemini-100 font-medium shadow-sm border border-gemini-600/50'
                    : 'text-gemini-400 hover:bg-gemini-750 hover:text-gemini-200 border border-transparent'
                }`}
              >
                <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-blue-400' : 'text-gemini-500'}`} />
                <span className="truncate flex-1">{sess.title}</span>
                {isActive && <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(sess.session_id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded-md text-gemini-400 hover:text-rose-400 hover:bg-gemini-800 transition-all shrink-0"
                  title="Delete chat"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* 5. User Profile Footer (Gemini Style) */}
      <div className="p-3 border-t border-gemini-700/60 flex items-center justify-between bg-gemini-800">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-amber-500 via-orange-500 to-rose-500 flex items-center justify-center text-xs font-bold text-white shadow-sm">
            M
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-semibold text-gemini-200 leading-tight">Mitesh K</span>
            <span className="text-[10px] text-emerald-400 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              SAGE Core Active
            </span>
          </div>
        </div>

        <button
          className="p-1.5 rounded-full hover:bg-gemini-700 text-gemini-400 hover:text-gemini-200 transition-colors"
          title="SAGE Configuration"
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>
    </aside>
  );
};
