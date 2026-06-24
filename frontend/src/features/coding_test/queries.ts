// React Query hooks. `useSubmitAndPoll` is the submit-then-poll core: it creates
// a submission, then polls until the status is terminal (graded/failed).

import { useMutation, useQuery } from "@tanstack/react-query";
import { useState } from "react";

import * as api from "./api";
import type { SubmissionStatus } from "./types";

const POLL_MS = 1500;

export function isTerminal(status?: SubmissionStatus): boolean {
  return status === "graded" || status === "failed";
}

/** Polling cadence: stop once terminal, else re-poll. Pure for easy testing. */
export function pollInterval(status?: SubmissionStatus): number | false {
  return isTerminal(status) ? false : POLL_MS;
}

export function useProblems() {
  return useQuery({ queryKey: ["problems"], queryFn: api.getProblems });
}

export function useProblem(id: string) {
  return useQuery({
    queryKey: ["problem", id],
    queryFn: () => api.getProblem(id),
    enabled: Boolean(id),
  });
}

export function useRunMutation(problemId: string) {
  return useMutation({ mutationFn: (code: string) => api.runCode(problemId, code) });
}

export function useSubmitAndPoll(problemId: string, candidateId: string) {
  const [submissionId, setSubmissionId] = useState<string | null>(null);

  const submit = useMutation({
    mutationFn: (code: string) =>
      api.createSubmission({ problem_id: problemId, candidate_id: candidateId, code }),
    onSuccess: (res) => setSubmissionId(res.submission_id),
  });

  const result = useQuery({
    queryKey: ["submission", submissionId],
    queryFn: () => api.getSubmission(submissionId as string),
    enabled: Boolean(submissionId),
    refetchInterval: (query) => pollInterval(query.state.data?.status),
  });

  return { submit, result, submissionId, reset: () => setSubmissionId(null) };
}
