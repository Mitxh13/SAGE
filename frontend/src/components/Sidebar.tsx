import React, { useState } from 'react';
import {
  Plus,
  BookOpen,
  MessageSquare,
  ChevronLeft,
  ChevronRight,
  Compass,
  Check,
  Trash2,
} from 'lucide-react';
import { SessionSummary, UnitSummary } from '../types/sage';
import { SageLogo } from './SageLogo';

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
      <aside className="w-16 bg-[#EFE9DE] border-r border-[#DDD5C7] flex flex-col items-center py-4 justify-between h-full z-20 transition-all duration-200">
        <div className="flex flex-col items-center space-y-4">
          <button
            onClick={onToggleOpen}
            className="p-2.5 rounded-full hover:bg-[#E2D9CA] text-[#244333] transition-colors"
            title="Expand sidebar"
          >
            <ChevronRight className="w-5 h-5" />
          </button>

          <button
            onClick={onNewSession}
            disabled={isLoading}
            className="w-10 h-10 rounded-full bg-[#E2ECE5] hover:bg-[#D5E4D9] border-2 border-[#8EB39D] text-[#1B3024] flex items-center justify-center transition-all hover:scale-105 shadow-sm"
            title="New Chat"
          >
            <Plus className="w-5 h-5 text-[#244333]" />
          </button>
        </div>

        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 rounded-full bg-[#E2ECE5] border border-[#8EB39D] text-[#1B3024] flex items-center justify-center text-xs font-bold shadow-sm">
            M
          </div>
        </div>
      </aside>
    );
  }

  return (
    <aside className="w-72 bg-[#EFE9DE] border-r border-[#DDD5C7] flex flex-col h-full z-20 select-none transition-all duration-200">
      {/* 1. Header with Logo & Collapse button */}
      <div className="p-4 flex items-center justify-between border-b border-[#DDD5C7]">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-[#E2ECE5] border border-[#8EB39D] flex items-center justify-center shadow-sm">
            <SageLogo size={20} />
          </div>
          <div className="flex flex-col">
            <span className="font-extrabold text-[#1B3024] text-sm tracking-tight flex items-center gap-1.5">
              SAGE
              <span className="text-[10px] font-bold bg-[#E2ECE5] text-[#244333] px-2 py-0.5 rounded-full border border-[#ADC5B7]">
                Socratic AI
              </span>
            </span>
          </div>
        </div>

        <button
          onClick={onToggleOpen}
          className="p-1.5 rounded-lg hover:bg-[#E2D9CA] text-[#244333] transition-colors"
          title="Collapse sidebar"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
      </div>

      {/* 2. New Chat Pill Button (Light Sage with Bold Crisp Dark Text) */}
      <div className="px-3.5 py-3">
        <button
          onClick={onNewSession}
          disabled={isLoading}
          className="w-full py-2.5 px-4 rounded-full bg-[#E2ECE5] hover:bg-[#D5E4D9] border-2 border-[#8EB39D] text-[#1B3024] text-xs font-bold flex items-center justify-between transition-all shadow-sm group"
        >
          <div className="flex items-center space-x-2">
            <Plus className="w-4 h-4 text-[#244333] group-hover:scale-110 transition-transform" />
            <span className="text-[#1B3024] font-bold text-xs">New chat</span>
          </div>
          <span className="text-[10px] text-[#244333] bg-[#D0E0D4] px-2 py-0.5 rounded-full font-mono font-bold border border-[#ADC5B7]">
            Ctrl+N
          </span>
        </button>
      </div>

      {/* 3. Course Units Section */}
      <div className="px-3.5 py-2">
        <div className="flex items-center justify-between mb-1.5 px-1">
          <span className="text-[11px] font-extrabold text-[#244333] uppercase tracking-wider flex items-center gap-1.5">
            <Compass className="w-3.5 h-3.5 text-[#244333]" />
            Curriculum Units
          </span>
          <button
            onClick={() => setUnitsExpanded(!unitsExpanded)}
            className="text-[10px] text-[#244333] hover:text-[#1B3024] font-bold"
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
                      ? 'bg-[#D6E6DC] text-[#1B3024] font-extrabold border-2 border-[#8EB39D] shadow-sm'
                      : 'text-[#244333] hover:bg-[#E5DDCF] hover:text-[#1B3024] border border-transparent font-semibold'
                  }`}
                >
                  <BookOpen className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${isSelected ? 'text-[#1B3024]' : 'text-[#3A604B]'}`} />
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
          <span className="text-[11px] font-extrabold text-[#244333] uppercase tracking-wider block">
            Recent Dialogues
          </span>
          <span className="text-[10px] text-[#244333] font-mono font-bold">
            {sessions.length}
          </span>
        </div>

        {sessions.length === 0 ? (
          <div className="text-center py-8 text-[#3A604B] text-xs px-2 font-medium">
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
                    ? 'bg-[#D6E6DC] text-[#1B3024] font-extrabold border-2 border-[#8EB39D] shadow-sm'
                    : 'text-[#244333] hover:bg-[#E5DDCF] hover:text-[#1B3024] border-transparent font-semibold'
                }`}
              >
                <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isActive ? 'text-[#1B3024]' : 'text-[#3A604B]'}`} />
                <span className="truncate flex-1">{sess.title}</span>
                {isActive && <Check className="w-3.5 h-3.5 text-[#244333] shrink-0 font-extrabold" />}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteSession(sess.session_id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded-md text-[#3A604B] hover:text-rose-700 hover:bg-rose-100/60 transition-all shrink-0"
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
      <div className="p-3.5 border-t border-[#DDD5C7] flex items-center justify-between bg-[#E8E1D4]">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-full bg-[#E2ECE5] border border-[#8EB39D] text-[#1B3024] flex items-center justify-center text-xs font-extrabold shadow-sm">
            PS
          </div>
          <div className="flex flex-col">
            <span className="text-xs font-extrabold text-[#1B3024] leading-tight">PES Student</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
