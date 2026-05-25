// Client-side session history — persisted in localStorage

export interface SessionRecord {
  sessionId: string;
  founderId: string;
  companyName: string;
  instruction: string;
  startedAt: number;
  status: "running" | "done" | "error";
  artifacts: { label: string; value: string; href?: string; icon: string }[];
}

const KEY = "astra_sessions";

export function getSessions(): SessionRecord[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? "[]");
  } catch {
    return [];
  }
}

export function saveSession(record: SessionRecord): void {
  if (typeof window === "undefined") return;
  const sessions = getSessions().filter(s => s.sessionId !== record.sessionId);
  sessions.unshift(record);
  localStorage.setItem(KEY, JSON.stringify(sessions.slice(0, 50)));
}

export function updateSession(sessionId: string, patch: Partial<SessionRecord>): void {
  if (typeof window === "undefined") return;
  const sessions = getSessions().map(s =>
    s.sessionId === sessionId ? { ...s, ...patch } : s
  );
  localStorage.setItem(KEY, JSON.stringify(sessions));
}

export function deleteSession(sessionId: string): void {
  if (typeof window === "undefined") return;
  const sessions = getSessions().filter(s => s.sessionId !== sessionId);
  localStorage.setItem(KEY, JSON.stringify(sessions));
}
