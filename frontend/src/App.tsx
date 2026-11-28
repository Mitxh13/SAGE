import React, { useState, useEffect } from 'react';
import { sageApi } from './api/sageClient';
import { ChatWindow } from './components/ChatWindow';
import { Sidebar } from './components/Sidebar';
import { StateInspector } from './components/StateInspector';
import { SessionDetail, SessionSummary, UnitSummary } from './types/sage';

export const App: React.FC = () => {
  const [units, setUnits] = useState<UnitSummary[]>([]);
  const [selectedUnitId, setSelectedUnitId] = useState<string>('unit_1_prompt_structure');
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [activeSession, setActiveSession] = useState<SessionDetail | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [inspectorOpen, setInspectorOpen] = useState<boolean>(false);
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(true);

  // Initial load: Fetch units and sessions
  useEffect(() => {
    const initialize = async () => {
      try {
        const [loadedUnits, loadedSessions] = await Promise.all([
          sageApi.listUnits(),
          sageApi.listSessions(),
        ]);
        setUnits(loadedUnits);
        if (loadedUnits.length > 0) {
          setSelectedUnitId(loadedUnits[0].unit_id);
        }
        setSessions(loadedSessions);

        // Default to clean home canvas on launch (like Gemini & Claude)
        setActiveSession(null);
      } catch (err) {
        console.error('Failed to initialize SAGE frontend:', err);
      }
    };

    initialize();
  }, []);

  // Handle new session: return to clean home canvas without creating dummy sessions in sidebar
  const handleNewSession = () => {
    setActiveSession(null);
  };

  // Switch active session
  const handleSelectSession = async (sessionId: string) => {
    if (activeSession?.session_id === sessionId) return;
    setIsLoading(true);
    try {
      const detail = await sageApi.getSession(sessionId);
      setActiveSession(detail);
      setSelectedUnitId(detail.unit_id);
    } catch (err) {
      console.error('Failed to switch session:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Delete a session from history
  const handleDeleteSession = async (sessionId: string) => {
    try {
      await sageApi.deleteSession(sessionId);
      const remainingSessions = sessions.filter((s) => s.session_id !== sessionId);
      setSessions(remainingSessions);

      // If deleted session was open, return to clean home canvas
      if (activeSession?.session_id === sessionId) {
        setActiveSession(null);
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  // Switch selected unit: select unit without spawning an empty session
  const handleSelectUnit = (unitId: string) => {
    setSelectedUnitId(unitId);
    setActiveSession(null);
  };

  // Send a student message (lazily creates session on first message sent)
  const handleSendMessage = async (content: string) => {
    setIsLoading(true);

    let session = activeSession;

    // If no active session exists yet (on clean home canvas), create the session now
    if (!session) {
      try {
        const newSession = await sageApi.createSession(selectedUnitId);
        session = newSession;
      } catch (err) {
        console.error('Failed to create session on first message:', err);
        setIsLoading(false);
        return;
      }
    }

    const currentSession = session;
    const currentSessionId = session.session_id;

    // Optimistically append student message
    const tempMsgId = `temp_${Date.now()}`;
    const optimisticMessages = [
      ...(currentSession.messages || []),
      {
        id: tempMsgId,
        role: 'user' as const,
        content,
        created_at: new Date().toISOString(),
      },
    ];

    setActiveSession({
      session_id: currentSessionId,
      unit_id: selectedUnitId,
      messages: optimisticMessages,
      learner_state: currentSession.learner_state,
      traces: currentSession.traces || [],
    });

    try {
      const turnResp = await sageApi.sendMessage(currentSessionId, content);
      setActiveSession((prev) => ({
        session_id: currentSessionId,
        unit_id: selectedUnitId,
        messages: [
          ...(prev ? prev.messages.filter((m) => m.id !== tempMsgId) : []),
          {
            id: `usr_${Date.now()}`,
            role: 'user',
            content,
            created_at: new Date().toISOString(),
          },
          turnResp.message,
          ...(turnResp.follow_up_message ? [turnResp.follow_up_message] : []),
        ],
        learner_state: turnResp.learner_state,
        traces: [...(prev?.traces || []), turnResp.trace],
      }));

      // Refresh sidebar sessions so the active chat now appears in Recent Dialogues
      const updatedSessions = await sageApi.listSessions();
      setSessions(updatedSessions);
    } catch (err) {
      console.error('Failed to process message turn:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const activeUnit = units.find((u) => u.unit_id === selectedUnitId);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-cream-100 text-sage-900 font-sans">
      {/* 1. Left Collapsible Sage Sidebar */}
      <Sidebar
        units={units}
        selectedUnitId={selectedUnitId}
        onSelectUnit={handleSelectUnit}
        sessions={sessions}
        activeSessionId={activeSession?.session_id || null}
        onSelectSession={handleSelectSession}
        onDeleteSession={handleDeleteSession}
        onNewSession={handleNewSession}
        isLoading={isLoading}
        isOpen={sidebarOpen}
        onToggleOpen={() => setSidebarOpen(!sidebarOpen)}
      />

      {/* 2. Center Chat Canvas */}
      <main className="flex-1 flex flex-col h-full overflow-hidden relative">
        <ChatWindow
          messages={activeSession?.messages || []}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          onToggleInspector={() => setInspectorOpen(!inspectorOpen)}
          inspectorOpen={inspectorOpen}
          activeUnitTitle={activeUnit?.title}
          units={units}
          selectedUnitId={selectedUnitId}
          onSelectUnit={handleSelectUnit}
        />
      </main>

      {/* 3. Right Slide-Over X-Ray State Inspector */}
      <StateInspector
        learnerState={activeSession?.learner_state || null}
        traces={activeSession?.traces || []}
        isOpen={inspectorOpen}
        onClose={() => setInspectorOpen(false)}
      />
    </div>
  );
};

export default App;
