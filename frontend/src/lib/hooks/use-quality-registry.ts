"use client";

import { useState, useCallback } from "react";
import { qualityRegistryApi } from "@/lib/api/quality-registry";
import type {
  QualityIssueCreate,
  QualityIssueResponse,
  CandidateLookupRequest,
  CandidateMatch,
  CandidateConfirmRequest,
  ReviewItemResponse,
  AuditEvent,
  ResolveReviewRequest,
} from "@/lib/api/quality-registry";

export interface QualityRegistryState {
  issues: QualityIssueResponse[];
  currentIssue: QualityIssueResponse | null;
  history: AuditEvent[];
  reviewQueue: ReviewItemResponse[];
  candidates: CandidateMatch[];
  isLoading: boolean;
  isLookingUp: boolean;
  isConfirming: boolean;
  error: string | null;
}

export interface UseQualityRegistryReturn {
  state: QualityRegistryState;
  // Issue CRUD
  createIssue: (data: QualityIssueCreate) => Promise<QualityIssueResponse | null>;
  listIssues: (status?: string) => Promise<void>;
  getIssue: (issueId: string) => Promise<void>;
  getHistory: (issueId: string) => Promise<void>;
  // Candidate operations
  lookupCandidates: (data: CandidateLookupRequest) => Promise<CandidateMatch[]>;
  confirmCandidate: (data: CandidateConfirmRequest) => Promise<QualityIssueResponse | null>;
  // Review queue
  loadReviewQueue: () => Promise<void>;
  resolveReview: (issueId: string, data: ResolveReviewRequest) => Promise<QualityIssueResponse | null>;
  // Utility
  clear: () => void;
  clearError: () => void;
}

const initialState: QualityRegistryState = {
  issues: [],
  currentIssue: null,
  history: [],
  reviewQueue: [],
  candidates: [],
  isLoading: false,
  isLookingUp: false,
  isConfirming: false,
  error: null,
};

export function useQualityRegistry(): UseQualityRegistryReturn {
  const [state, setState] = useState<QualityRegistryState>(initialState);

  // Issue CRUD operations

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
          issues: [issue, ...prev.issues],
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

  const listIssues = useCallback(async (status?: string): Promise<void> => {
    setState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
    }));

    try {
      const response = await qualityRegistryApi.listIssues(status);

      if (response.error) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: response.error ?? "Failed to list issues",
        }));
        return;
      }

      const issues = response.data ?? [];

      setState((prev) => ({
        ...prev,
        isLoading: false,
        issues,
      }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : "Unknown error occurred",
      }));
    }
  }, []);

  const getIssue = useCallback(async (issueId: string): Promise<void> => {
    setState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
    }));

    try {
      const response = await qualityRegistryApi.getIssue(issueId);

      if (response.error) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: response.error ?? "Failed to get issue",
        }));
        return;
      }

      const issue = response.data;
      if (!issue) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: "Issue not found",
        }));
        return;
      }

      setState((prev) => ({
        ...prev,
        isLoading: false,
        currentIssue: issue,
      }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : "Unknown error occurred",
      }));
    }
  }, []);

  const getHistory = useCallback(async (issueId: string): Promise<void> => {
    setState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
    }));

    try {
      const response = await qualityRegistryApi.getHistory(issueId);

      if (response.error) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: response.error ?? "Failed to get history",
        }));
        return;
      }

      const history = response.data ?? [];

      setState((prev) => ({
        ...prev,
        isLoading: false,
        history,
      }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : "Unknown error occurred",
      }));
    }
  }, []);

  // Candidate operations

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

  // Review queue operations

  const loadReviewQueue = useCallback(async (): Promise<void> => {
    setState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
    }));

    try {
      const response = await qualityRegistryApi.getReviewQueue();

      if (response.error) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: response.error ?? "Failed to load review queue",
        }));
        return;
      }

      const reviewQueue = response.data ?? [];

      setState((prev) => ({
        ...prev,
        isLoading: false,
        reviewQueue,
      }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : "Unknown error occurred",
      }));
    }
  }, []);

  const resolveReview = useCallback(
    async (
      issueId: string,
      data: ResolveReviewRequest
    ): Promise<QualityIssueResponse | null> => {
      setState((prev) => ({
        ...prev,
        isLoading: true,
        error: null,
      }));

      try {
        const response = await qualityRegistryApi.resolveReview(issueId, data);

        if (response.error) {
          setState((prev) => ({
            ...prev,
            isLoading: false,
            error: response.error ?? "Failed to resolve review",
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
          reviewQueue: prev.reviewQueue.filter((item) => item.id !== issueId),
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

  // Utility methods

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
    listIssues,
    getIssue,
    getHistory,
    lookupCandidates,
    confirmCandidate,
    loadReviewQueue,
    resolveReview,
    clear,
    clearError,
  };
}