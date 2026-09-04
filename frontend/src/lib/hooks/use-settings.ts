"use client";

import { useState, useCallback } from "react";
import { settingsApi, type LlmSettingsResponse } from "@/lib/api/settings";

export interface SettingsState {
  settings: LlmSettingsResponse | null;
  isLoading: boolean;
  error: string | null;
}

export interface UseSettingsReturn {
  state: SettingsState;
  loadSettings: () => Promise<void>;
  clearError: () => void;
}

const initialState: SettingsState = {
  settings: null,
  isLoading: false,
  error: null,
};

export function useSettings(): UseSettingsReturn {
  const [state, setState] = useState<SettingsState>(initialState);

  const loadSettings = useCallback(async (): Promise<void> => {
    setState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
    }));

    try {
      const response = await settingsApi.getLlmSettings();

      if (response.error) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: response.error ?? "Failed to load settings",
        }));
        return;
      }

      const settings = response.data ?? null;

      setState((prev) => ({
        ...prev,
        isLoading: false,
        settings,
      }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : "Unknown error occurred",
      }));
    }
  }, []);

  const clearError = useCallback(() => {
    setState((prev) => ({
      ...prev,
      error: null,
    }));
  }, []);

  return {
    state,
    loadSettings,
    clearError,
  };
}
