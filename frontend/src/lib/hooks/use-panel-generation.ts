"use client";

import { useState, useCallback } from "react";
import { apiClient } from "@/lib/api-client";
import type { components } from "@/lib/api/generated";

type PanelGenerateRequest = components["schemas"]["PanelGenerateRequest"];
type PanelGenerateResponse = components["schemas"]["PanelGenerateResponse"];
type DiagnoseRequest = components["schemas"]["DiagnoseRequest"];
type DiagnoseResponse = components["schemas"]["DiagnoseResponse"];
type PanelCandidate = components["schemas"]["PanelCandidate"];

export interface PanelGenerationState {
  candidates: PanelCandidate[];
  missingMarkers: string[];
  diagnosis: string | null;
  isLoading: boolean;
  isDiagnosing: boolean;
  error: string | null;
}

export interface UsePanelGenerationReturn {
  state: PanelGenerationState;
  generate: (markers: string[], species: string) => Promise<void>;
  clear: () => void;
}

const MAX_SOLUTIONS = 10;

function mapSpeciesToParams(species: string): { species: string } {
  if (species.includes("Mouse")) {
    return { species: "Mouse" };
  } else if (species.includes("Human")) {
    return { species: "Human" };
  }
  return { species };
}

export function usePanelGeneration(): UsePanelGenerationReturn {
  const [state, setState] = useState<PanelGenerationState>({
    candidates: [],
    missingMarkers: [],
    diagnosis: null,
    isLoading: false,
    isDiagnosing: false,
    error: null,
  });

  const generate = useCallback(async (markers: string[], species: string) => {
    const trimmedMarkers = markers.map((m) => m.trim()).filter(Boolean);

    setState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
      diagnosis: null,
      candidates: [],
      missingMarkers: [],
    }));

    try {
      const { species: speciesParam } = mapSpeciesToParams(species);

      const requestBody: PanelGenerateRequest = {
        markers: trimmedMarkers,
        species: speciesParam,
        max_solutions: MAX_SOLUTIONS,
        inventory_file: null,
      };

      const response = await apiClient.post<PanelGenerateResponse>(
        "/panels/generate",
        requestBody
      );

      if (response.error) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: response.error ?? "Failed to generate panels",
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

      // If no candidates or status is error, run diagnosis
      if ((data.candidates?.length === 0 || data.status === "error") && trimmedMarkers.length > 0) {
        setState((prev) => ({ ...prev, isDiagnosing: true }));

        const diagnoseBody: DiagnoseRequest = {
          markers: trimmedMarkers,
          inventory_file: null,
        };

        const diagnoseResponse = await apiClient.post<DiagnoseResponse>(
          "/panels/diagnose",
          diagnoseBody
        );

        setState((prev) => ({
          ...prev,
          isLoading: false,
          isDiagnosing: false,
          diagnosis: diagnoseResponse.data?.diagnosis ?? null,
          missingMarkers: data.missing_markers ?? [],
          candidates: data.candidates ?? [],
        }));
        return;
      }

      if (data.status === "error") {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: data.message ?? "Failed to generate panels",
        }));
        return;
      }

      setState((prev) => ({
        ...prev,
        isLoading: false,
        candidates: data.candidates ?? [],
        missingMarkers: data.missing_markers ?? [],
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
      candidates: [],
      missingMarkers: [],
      diagnosis: null,
      isLoading: false,
      isDiagnosing: false,
      error: null,
    });
  }, []);

  return { state, generate, clear };
}
