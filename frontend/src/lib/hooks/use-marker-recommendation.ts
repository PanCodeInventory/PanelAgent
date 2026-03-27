"use client";

import { useState, useCallback } from "react";
import { apiClient } from "@/lib/api-client";
import type { components } from "@/lib/api/generated";

type MarkerRecommendationRequest = components["schemas"]["MarkerRecommendationRequest"];
type MarkerRecommendationResponse = components["schemas"]["MarkerRecommendationResponse"];
type MarkerDetail = components["schemas"]["MarkerDetail"];

export interface MarkerRecommendationState {
  markers: string[];
  markersDetail: MarkerDetail[];
  isLoading: boolean;
  error: string | null;
}

export interface UseMarkerRecommendationReturn {
  state: MarkerRecommendationState;
  recommend: (experimentalGoal: string, numColors: number, species: string) => Promise<void>;
  clear: () => void;
}

// Map display species to API params
function mapSpeciesToParams(species: string): { species: string; inventoryFile?: string } {
  if (species.includes("Mouse")) {
    return { species: "Mouse", inventoryFile: "Mouse_20250625_ZhengLab.csv" };
  } else if (species.includes("Human")) {
    return { species: "Human", inventoryFile: "Human_Inventory.csv" };
  }
  return { species };
}

export function useMarkerRecommendation(): UseMarkerRecommendationReturn {
  const [state, setState] = useState<MarkerRecommendationState>({
    markers: [],
    markersDetail: [],
    isLoading: false,
    error: null,
  });

  const recommend = useCallback(async (experimentalGoal: string, numColors: number, species: string) => {
    setState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
      markers: [],
      markersDetail: [],
    }));

    try {
      const { species: speciesParam, inventoryFile } = mapSpeciesToParams(species);

      const requestBody: MarkerRecommendationRequest = {
        experimental_goal: experimentalGoal.trim(),
        num_colors: numColors,
        species: speciesParam,
        inventory_file: inventoryFile ?? null,
      };

      const response = await apiClient.post<MarkerRecommendationResponse>(
        "/recommendations/markers",
        requestBody
      );

      if (response.error) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: response.error ?? "Failed to get marker recommendations",
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
          markers: [],
          markersDetail: [],
          error: data.message ?? "Marker recommendation failed",
        }));
        return;
      }

      setState((prev) => ({
        ...prev,
        isLoading: false,
        markers: data.selected_markers ?? [],
        markersDetail: data.markers_detail ?? [],
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
      markers: [],
      markersDetail: [],
      isLoading: false,
      error: null,
    });
  }, []);

  return { state, recommend, clear };
}
