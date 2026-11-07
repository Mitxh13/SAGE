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
  const [inspectorOpen, setInspectorOpen] = useState<boolean>(true);

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

        // Resume most recent session or create one
        if (loadedSessions.length > 0) {
          const detail = await sageApi.getSession(loadedSessions[0].session_id);
          setActiveSession(detail);
          setSelectedUnitId(detail.unit_id);
        } else if (loadedUnits.length > 0) {
          const newSession = await sageApi.createSession(loadedUnits[0].unit_id);
          setActiveSession(newSession);
          setSessions([
            {
              session_id: newSession.session_id,
              unit_id: newSession.unit_id,
              title: `Session on ${newSession.unit_id}`,
              created_at: new Date().toISOString(),
            },
          ]);
        }
      } catch (err) {
        console.error('Failed to initialize SAGE frontend:', err);
      }
    };

    initialize();
  }, []);

  // Handle new session creation
  const handleNewSession = async () => {
    setIsLoading(true);
    try {
      const newSession = await sageApi.createSession(selectedUnitId);
      setActiveSession(newSession);
      const updatedSessions = await sageApi.listSessions();
      setSessions(updatedSessions);
    } catch (err) {
      console.error('Failed to create new session:', err);
    } finally {
      setIsLoading(false);
    }
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

  // Switch selected unit (creates new session on that unit)
  const handleSelectUnit = async (unitId: string) => {
    setSelectedUnitId(unitId);
    setIsLoading(true);
    try {
      const newSession = await sageApi.createSession(unitId);
      setActiveSession(newSession);
      const updatedSessions = await sageApi.listSessions();
      setSessions(updatedSessions);
    } catch (err) {
      console.error('Failed to start session on unit:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Send a student message in the active session
  const handleSendMessage = async (content: string) => {
    if (!activeSession) return;
    setIsLoading(true);

    // Optimistically append student message
    const tempMsgId = `temp_${Date.now()}`;
    const optimisticMessages = [
      ...activeSession.messages,
      {
        id: tempMsgId,
        role: 'user' as const,
        content,
        created_at: new Date().toISOString(),
      },
    ];

    setActiveSession({
      ...activeSession,
      messages: optimisticMessages,
    });

    try {
      const turnResp = await sageApi.sendMessage(activeSession.session_id, content);
      setActiveSession((prev) => {
        if (!prev) return null;
        return {
          ...prev,
          messages: [...prev.messages.filter((m) => m.id !== tempMsgId), {
            id: `usr_${Date.now()}`,
            role: 'user',
            content,
            created_at: new Date().toISOString(),
          }, turnResp.message, ...(turnResp.follow_up_message ? [turnResp.follow_up_message] : [])],
          learner_state: turnResp.learner_state,
          traces: [...prev.traces, turnResp.trace],
        };
      });
    } catch (err) {
      console.error('Failed to process message turn:', err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-900 font-sans">
      {/* 1. Left Sidebar */}
      <Sidebar
        units={units}
        selectedUnitId={selectedUnitId}
        onSelectUnit={handleSelectUnit}
        sessions={sessions}
        activeSessionId={activeSession?.session_id || null}
        onSelectSession={handleSelectSession}
        onNewSession={handleNewSession}
        isLoading={isLoading}
      />

      {/* 2. Center Chat Window */}
      <main className="flex-1 flex flex-col h-full overflow-hidden">
        <ChatWindow
          messages={activeSession?.messages || []}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          onToggleInspector={() => setInspectorOpen(!inspectorOpen)}
          inspectorOpen={inspectorOpen}
        />
      </main>

      {/* 3. Right Evaluator X-Ray State Inspector */}
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
