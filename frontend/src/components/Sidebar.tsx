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
  Check,
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
      <aside className="w-16 bg-cream-150 border-r border-cream-300 flex flex-col items-center py-4 justify-between h-full z-20 transition-all duration-200">
        <div className="flex flex-col items-center space-y-4">
          <button
            onClick={onToggleOpen}
            className="p-2.5 rounded-full hover:bg-cream-200 text-charcoal-500 hover:text-charcoal-800 transition-colors"
            title="Expand sidebar"
          >
            <ChevronRight className="w-5 h-5" />
          </button>

          <button
            onClick={onNewSession}
            disabled={isLoading}
            className="w-10 h-10 rounded-full bg-sage-700 hover:bg-sage-800 text-white flex items-center justify-center transition-all hover:scale-105 shadow-sm"
            title="New Chat"
          >
            <Plus className="w-5 h-5" />
          </button>
        </div>

        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 rounded-full bg-sage-700 text-cream-50 flex items-center justify-center text-xs font-semibold shadow-sm">
            M
          </div>
        </div>
      </aside>
    );
  }

  return (
    <aside className="w-72 bg-cream-150 border-r border-cream-300 flex flex-col h-full z-20 select-none transition-all duration-200">
      {/* 1. Header with Logo & Collapse button */}
      <div className="p-4 flex items-center justify-between border-b border-cream-200">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-sage-700 text-white flex items-center justify-center shadow-sage-soft">
            <Sparkles className="w-4 h-4 text-cream-100" />
          </div>
          <div className="flex flex-col">
            <span className="font-semibold text-charcoal-900 text-sm tracking-tight flex items-center gap-1.5">
              SAGE
              <span className="text-[10px] font-medium bg-sage-100 text-sage-800 px-1.5 py-0.5 rounded-full border border-sage-200">
                Socratic AI
              </span>
            </span>
            <span className="text-[11px] text-charcoal-500">Curriculum Tutor</span>
          </div>
        </div>

        <button
          onClick={onToggleOpen}
          className="p-1.5 rounded-lg hover:bg-cream-200 text-charcoal-400 hover:text-charcoal-700 transition-colors"
          title="Collapse sidebar"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
      </div>

      {/* 2. New Chat Pill Button */}
      <div className="px-3.5 py-3">
        <button
          onClick={onNewSession}
          disabled={isLoading}
          className="w-full py-2.5 px-4 rounded-full bg-sage-700 hover:bg-sage-800 text-white text-xs font-medium flex items-center justify-between transition-all shadow-sm disabled:opacity-50 group"
        >
          <div className="flex items-center space-x-2">
            <Plus className="w-4 h-4 text-sage-200 group-hover:text-white transition-colors" />
            <span>New chat</span>
          </div>
          <span className="text-[10px] text-sage-200 bg-sage-800/60 px-2 py-0.5 rounded-full font-mono">
            Ctrl+N
          </span>
        </button>
      </div>

      {/* 3. Course Units Section */}
      <div className="px-3.5 py-2">
        <div className="flex items-center justify-between mb-1.5 px-1">
          <span className="text-[11px] font-semibold text-charcoal-500 uppercase tracking-wider flex items-center gap-1.5">
            <Compass className="w-3.5 h-3.5 text-sage-600" />
            Curriculum Units
          </span>
          <button
            onClick={() => setUnitsExpanded(!unitsExpanded)}
            className="text-[10px] text-charcoal-400 hover:text-charcoal-700 font-medium"
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
                      ? 'bg-sage-100 text-sage-900 font-medium border border-sage-300 shadow-sage-soft'
                      : 'text-charcoal-600 hover:bg-cream-200 hover:text-charcoal-900 border border-transparent'
                  }`}
                >
                  <BookOpen className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${isSelected ? 'text-sage-700' : 'text-charcoal-400'}`} />
                  <span className="line-clamp-1 leading-snug">{unit.title}</span>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* 4. Recent Conversations History */}
      <div className="flex-1 overflow-y-auto px-3.5 py-2 space-y-1">
        <div className="flex items-center justify-between mb-1.5 px-1">
          <span className="text-[11px] font-semibold text-charcoal-500 uppercase tracking-wider block">
            Recent Dialogues
          </span>
          <span className="text-[10px] text-charcoal-400 font-mono">
            {sessions.length}
          </span>
        </div>

        {sessions.length === 0 ? (
          <div className="text-center py-8 text-charcoal-400 text-xs px-2">
            No previous sessions yet. Start a new dialogue above.
          </div>
        ) : (
          sessions.map((sess) => {
            const isActive = sess.session_id === activeSessionId;
            return (
              <div
                key={sess.session_id}
                onClick={() => onSelectSession(sess.session_id)}
                className={`group w-full text-left px-3 py-2 rounded-xl text-xs transition-all flex items-center space-x-2 cursor-pointer border ${
                  isActive
                    ? 'bg-sage-100 text-sage-900 font-medium border-sage-300 shadow-sage-soft'
                    : 'text-charcoal-600 hover:bg-cream-200 hover:text-charcoal-900 border-transparent'
                }`}
              >
                <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-sage-700' : 'text-charcoal-400'}`} />
                <span className="truncate flex-1">{sess.title}</span>
                {isActive && <Check className="w-3 h-3 text-sage-600 shrink-0" />}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(sess.session_id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded-md text-charcoal-400 hover:text-rose-600 hover:bg-rose-50 transition-all shrink-0"
                  title="Delete chat session"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* 5. User Profile Footer */}
      <div className="p-3.5 border-t border-cream-300 flex items-center justify-between bg-cream-200/60">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-full bg-sage-700 text-white flex items-center justify-center text-xs font-semibold shadow-sm">
            M
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-semibold text-charcoal-900 leading-tight">Mitesh K</span>
            <span className="text-[10px] text-sage-700 flex items-center gap-1 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-sage-600"></span>
              SAGE Core Active
            </span>
          </div>
        </div>

        <button
          className="p-1.5 rounded-lg hover:bg-cream-300 text-charcoal-500 hover:text-charcoal-800 transition-colors"
          title="SAGE Configuration"
        >
          <Settings className="w-4 h-4" />
        </button>
      </div>
    </aside>
  );
};
