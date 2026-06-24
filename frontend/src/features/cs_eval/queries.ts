// React Query hooks for cs-eval. Submit creates a session (one answer per
// question); the result page polls that session until the status is terminal.

import { useMutation, useQuery } from "@tanstack/react-query";

import * as api from "./api";
import type { AnswerInput, SessionStatus } from "./types";

const POLL_MS = 1500;

export function isTerminal(status?: SessionStatus): boolean {
  return status === "graded" || status === "failed";
}

/** Polling cadence: stop once terminal, else re-poll. Pure for easy testing. */
export function pollInterval(status?: SessionStatus): number | false {
  return isTerminal(status) ? false : POLL_MS;
}

export function useQuestions() {
  return useQuery({ queryKey: ["cs-questions"], queryFn: api.getQuestions });
}

export function useCreateSession(candidateId: string) {
  return useMutation({
    mutationFn: (answers: AnswerInput[]) =>
      api.createSession({ candidate_id: candidateId, answers }),
  });
}

export function useSessionResult(sessionId: string) {
  return useQuery({
    queryKey: ["cs-session", sessionId],
    queryFn: () => api.getSession(sessionId),
    enabled: Boolean(sessionId),
    refetchInterval: (query) => pollInterval(query.state.data?.status),
  });
}
