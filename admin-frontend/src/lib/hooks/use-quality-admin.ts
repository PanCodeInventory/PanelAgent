"use client";

import { useState, useCallback } from "react";
import { adminFetch, adminPost, adminPut } from "@/lib/api/admin-client";

export interface FeedbackKey {
  species: string;
  normalized_marker: string;
  fluorochrome: string;
  brand: string;
  clone?: string | null;
}

export interface EntityKey {
  species: string;
  normalized_marker: string;
  clone: string;
  brand: string;
  catalog_number: string;
  lot_number?: string | null;
}

export interface QualityIssue {
  id: string;
  feedback_key: FeedbackKey;
  entity_key: EntityKey | null;
  issue_text: string;
  reported_by: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface QualityIssueUpdate {
  issue_text: string;
  reported_by: string;
}

export interface ReviewItem {
  id: string;
  feedback_key: FeedbackKey;
  entity_key: EntityKey | null;
  issue_text: string;
  reported_by: string;
  status: string;
  reviewer?: string | null;
  reviewed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AuditEvent {
  event_id: string;
  issue_id: string;
  action: string;
  actor: string;
  details: Record<string, unknown>;
  timestamp: string;
}

export interface ResolveReviewRequest {
  reviewer: string;
  entity_key?: EntityKey | null;
}

export interface QualityAdminState {
  issues: QualityIssue[];
  currentIssue: QualityIssue | null;
  history: AuditEvent[];
  reviewQueue: ReviewItem[];
  isLoading: boolean;
  error: string | null;
}

export interface UseQualityAdminReturn {
  state: QualityAdminState;
  listIssues: (status?: string) => Promise<void>;
  getIssue: (issueId: string) => Promise<void>;
  updateIssue: (issueId: string, data: QualityIssueUpdate) => Promise<QualityIssue | null>;
  getHistory: (issueId: string) => Promise<void>;
  loadReviewQueue: () => Promise<void>;
  resolveReview: (issueId: string, data: ResolveReviewRequest) => Promise<QualityIssue | null>;
  clear: () => void;
  clearError: () => void;
}

const initialState: QualityAdminState = {
  issues: [],
  currentIssue: null,
  history: [],
  reviewQueue: [],
  isLoading: false,
  error: null,
};

export function useQualityAdmin(): UseQualityAdminReturn {
  const [state, setState] = useState<QualityAdminState>(initialState);

  const listIssues = useCallback(async (status?: string): Promise<void> => {
    setState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
    }));

    try {
      const path = status
        ? `/quality-registry/issues?status=${status}`
        : "/quality-registry/issues";
      const issues = await adminFetch<QualityIssue[]>(path);

      setState((prev) => ({
        ...prev,
        isLoading: false,
        issues,
      }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : "Failed to list issues",
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
      const issue = await adminFetch<QualityIssue>(`/quality-registry/issues/${issueId}`);

      setState((prev) => ({
        ...prev,
        isLoading: false,
        currentIssue: issue,
      }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : "Failed to get issue",
      }));
    }
  }, []);

  const updateIssue = useCallback(
    async (issueId: string, data: QualityIssueUpdate): Promise<QualityIssue | null> => {
      setState((prev) => ({
        ...prev,
        isLoading: true,
        error: null,
      }));

      try {
        const issue = await adminPut<QualityIssue>(
          `/quality-registry/issues/${issueId}`,
          data
        );

        setState((prev) => ({
          ...prev,
          isLoading: false,
          issues: prev.issues.map((i) => (i.id === issueId ? issue : i)),
          currentIssue: prev.currentIssue?.id === issueId ? issue : prev.currentIssue,
        }));

        return issue;
      } catch (err) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: err instanceof Error ? err.message : "Failed to update issue",
        }));
        return null;
      }
    },
    []
  );

  const getHistory = useCallback(async (issueId: string): Promise<void> => {
    setState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
    }));

    try {
      const history = await adminFetch<AuditEvent[]>(
        `/quality-registry/issues/${issueId}/history`
      );

      setState((prev) => ({
        ...prev,
        isLoading: false,
        history,
      }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : "Failed to get history",
      }));
    }
  }, []);

  const loadReviewQueue = useCallback(async (): Promise<void> => {
    setState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
    }));

    try {
      const reviewQueue = await adminFetch<ReviewItem[]>(
        "/quality-registry/review-queue"
      );

      setState((prev) => ({
        ...prev,
        isLoading: false,
        reviewQueue,
      }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : "Failed to load review queue",
      }));
    }
  }, []);

  const resolveReview = useCallback(
    async (issueId: string, data: ResolveReviewRequest): Promise<QualityIssue | null> => {
      setState((prev) => ({
        ...prev,
        isLoading: true,
        error: null,
      }));

      try {
        const issue = await adminPost<QualityIssue>(
          `/quality-registry/review-queue/${issueId}/resolve`,
          data
        );

        setState((prev) => ({
          ...prev,
          isLoading: false,
          reviewQueue: prev.reviewQueue.filter((item) => item.id !== issueId),
          issues: prev.issues.map((i) => (i.id === issueId ? issue : i)),
        }));

        return issue;
      } catch (err) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: err instanceof Error ? err.message : "Failed to resolve review",
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
    listIssues,
    getIssue,
    updateIssue,
    getHistory,
    loadReviewQueue,
    resolveReview,
    clear,
    clearError,
  };
}
