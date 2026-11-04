/**
 * Typed API client for SAGE FastAPI backend.
 */

import {
  SessionDetail,
  SessionSummary,
  TurnResponse,
  UnitSummary,
} from '../types/sage';

const BASE_URL = '/api';

export const sageApi = {
  /** Discover available course units */
  async listUnits(): Promise<UnitSummary[]> {
    const res = await fetch(`${BASE_URL}/units`);
    if (!res.ok) throw new Error(`Failed to list units: ${res.statusText}`);
    return res.json();
  },

  /** Start a new tutoring session for a unit */
  async createSession(unitId: string): Promise<SessionDetail> {
    const res = await fetch(`${BASE_URL}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ unit_id: unitId }),
    });
    if (!res.ok) throw new Error(`Failed to create session: ${res.statusText}`);
    return res.json();
  },

  /** Fetch past session summaries for sidebar history */
  async listSessions(): Promise<SessionSummary[]> {
    const res = await fetch(`${BASE_URL}/sessions`);
    if (!res.ok) throw new Error(`Failed to list sessions: ${res.statusText}`);
    return res.json();
  },

  /** Retrieve full session details including messages, state, and traces */
  async getSession(sessionId: string): Promise<SessionDetail> {
    const res = await fetch(`${BASE_URL}/sessions/${sessionId}`);
    if (!res.ok) throw new Error(`Failed to get session: ${res.statusText}`);
    return res.json();
  },

  /** Send a student message and receive the tutor response with telemetry */
  async sendMessage(sessionId: string, content: string): Promise<TurnResponse> {
    const res = await fetch(`${BASE_URL}/sessions/${sessionId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });
    if (!res.ok) throw new Error(`Failed to send message: ${res.statusText}`);
    return res.json();
  },

  /** System health check */
  async getHealth(): Promise<Record<string, any>> {
    const res = await fetch(`${BASE_URL}/health`);
    if (!res.ok) throw new Error(`Failed health check: ${res.statusText}`);
    return res.json();
  },
};
