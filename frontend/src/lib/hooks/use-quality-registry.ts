"use client";

import { useState, useCallback } from "react";
import { qualityRegistryApi } from "@/lib/api/quality-registry";
import type {
  QualityIssueCreate,
  QualityIssueResponse,
  CandidateLookupRequest,
  CandidateMatch,
  CandidateConfirmRequest,
} from "@/lib/api/quality-registry";

export interface QualityRegistryState {
  currentIssue: QualityIssueResponse | null;
  candidates: CandidateMatch[];
  isLoading: boolean;
  isLookingUp: boolean;
  isConfirming: boolean;
  error: string | null;
}

export interface UseQualityRegistryReturn {
  state: QualityRegistryState;
  createIssue: (data: QualityIssueCreate) => Promise<QualityIssueResponse | null>;
  lookupCandidates: (data: CandidateLookupRequest) => Promise<CandidateMatch[]>;
  confirmCandidate: (data: CandidateConfirmRequest) => Promise<QualityIssueResponse | null>;
  clear: () => void;
  clearError: () => void;
}

const initialState: QualityRegistryState = {
  currentIssue: null,
  candidates: [],
  isLoading: false,
  isLookingUp: false,
  isConfirming: false,
  error: null,
};

export function useQualityRegistry(): UseQualityRegistryReturn {
  const [state, setState] = useState<QualityRegistryState>(initialState);

  const createIssue = useCallback(
    async (data: QualityIssueCreate): Promise<QualityIssueResponse | null> => {
      setState((prev) => ({
        ...prev,
        isLoading: true,
        error: null,
      }));

      try {
        const response = await qualityRegistryApi.createIssue(data);

        if (response.error) {
          setState((prev) => ({
            ...prev,
            isLoading: false,
            error: response.error ?? "Failed to create issue",
          }));
          return null;
        }

        const issue = response.data;
        if (!issue) {
          setState((prev) => ({
            ...prev,
            isLoading: false,
            error: "No response from server",
          }));
          return null;
        }

        setState((prev) => ({
          ...prev,
          isLoading: false,
          currentIssue: issue,
        }));

        return issue;
      } catch (err) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: err instanceof Error ? err.message : "Unknown error occurred",
        }));
        return null;
      }
    },
    []
  );

  const lookupCandidates = useCallback(
    async (data: CandidateLookupRequest): Promise<CandidateMatch[]> => {
      setState((prev) => ({
        ...prev,
        isLookingUp: true,
        error: null,
        candidates: [],
      }));

      try {
        const response = await qualityRegistryApi.lookupCandidates(data);

        if (response.error) {
          setState((prev) => ({
            ...prev,
            isLookingUp: false,
            error: response.error ?? "Failed to lookup candidates",
          }));
          return [];
        }

        const candidates = response.data?.candidates ?? [];

        setState((prev) => ({
          ...prev,
          isLookingUp: false,
          candidates,
        }));

        return candidates;
      } catch (err) {
        setState((prev) => ({
          ...prev,
          isLookingUp: false,
          error: err instanceof Error ? err.message : "Unknown error occurred",
        }));
        return [];
      }
    },
    []
  );

  const confirmCandidate = useCallback(
    async (data: CandidateConfirmRequest): Promise<QualityIssueResponse | null> => {
      setState((prev) => ({
        ...prev,
        isConfirming: true,
        error: null,
      }));

      try {
        const response = await qualityRegistryApi.confirmCandidate(data);

        if (response.error) {
          setState((prev) => ({
            ...prev,
            isConfirming: false,
            error: response.error ?? "Failed to confirm candidate",
          }));
          return null;
        }

        const issue = response.data;
        if (!issue) {
          setState((prev) => ({
            ...prev,
            isConfirming: false,
            error: "No response from server",
          }));
          return null;
        }

        setState((prev) => ({
          ...prev,
          isConfirming: false,
          currentIssue: issue,
          candidates: [],
        }));

        return issue;
      } catch (err) {
        setState((prev) => ({
          ...prev,
          isConfirming: false,
          error: err instanceof Error ? err.message : "Unknown error occurred",
        }));
        return null;
      }
    },
    []
  );

  const clear = useCallback(() => {
    setState(initialState);
  }, []);

  const clearError = useCallback(() => {
    setState((prev) => ({
      ...prev,
      error: null,
    }));
  }, []);

  return {
    state,
    createIssue,
    lookupCandidates,
    confirmCandidate,
    clear,
    clearError,
  };
}
