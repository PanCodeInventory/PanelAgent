"use client";

import { useState, useCallback } from "react";
import { apiClient } from "@/lib/api-client";
import type { components } from "@/lib/api/generated";

type PanelEvaluateRequest = components["schemas"]["PanelEvaluateRequest"];
type PanelEvaluateResponse = components["schemas"]["PanelEvaluateResponse"];
type PanelCandidate = components["schemas"]["PanelCandidate"];

export interface PanelEvaluationResult {
  selectedPanel: PanelCandidate | null;
  rationale: string;
  gatingDetail: Record<string, unknown>[];
  message?: string | null;
}

export interface PanelEvaluationState {
  result: PanelEvaluationResult | null;
  isLoading: boolean;
  error: string | null;
}

export interface UsePanelEvaluationReturn {
  state: PanelEvaluationState;
  evaluate: (candidates: PanelCandidate[], missingMarkers?: string[]) => Promise<void>;
  clear: () => void;
}

export function usePanelEvaluation(): UsePanelEvaluationReturn {
  const [state, setState] = useState<PanelEvaluationState>({
    result: null,
    isLoading: false,
    error: null,
  });

  const evaluate = useCallback(async (candidates: PanelCandidate[], missingMarkers?: string[]) => {
    if (candidates.length === 0) {
      setState((prev) => ({
        ...prev,
        error: "No candidates to evaluate",
      }));
      return;
    }

    setState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
      result: null,
    }));

    try {
      const requestBody: PanelEvaluateRequest = {
        candidates: candidates as Record<string, Record<string, unknown>>[],
        missing_markers: missingMarkers ?? [],
      };

      const response = await apiClient.post<PanelEvaluateResponse>(
        "/panels/evaluate",
        requestBody
      );

      if (response.error) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: response.error ?? "Failed to evaluate panels",
        }));
        return;
      }

      const data = response.data;

      if (!data) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: "No response from server",
        }));
        return;
      }

      if (data.status === "error") {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: data.message ?? "Panel evaluation failed",
        }));
        return;
      }

      setState((prev) => ({
        ...prev,
        isLoading: false,
        result: {
          selectedPanel: (data.selected_panel as PanelCandidate) ?? null,
          rationale: data.rationale ?? "",
          gatingDetail: (data.gating_detail as Record<string, unknown>[]) ?? [],
          message: data.message,
        },
      }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : "Unknown error occurred",
      }));
    }
  }, []);

  const clear = useCallback(() => {
    setState({
      result: null,
      isLoading: false,
      error: null,
    });
  }, []);

  return { state, evaluate, clear };
}
