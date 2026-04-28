"use client";

import { useState, useCallback } from "react";
import { settingsApi, type LlmSettingsResponse, type LlmSettingsUpdate } from "@/lib/api/settings";

export interface SettingsState {
  settings: LlmSettingsResponse | null;
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
}

export interface UseSettingsReturn {
  state: SettingsState;
  loadSettings: () => Promise<void>;
  saveSettings: (data: LlmSettingsUpdate) => Promise<LlmSettingsResponse | null>;
  clearError: () => void;
}

const initialState: SettingsState = {
  settings: null,
  isLoading: false,
  isSaving: false,
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

  const saveSettings = useCallback(
    async (data: LlmSettingsUpdate): Promise<LlmSettingsResponse | null> => {
      setState((prev) => ({
        ...prev,
        isSaving: true,
        error: null,
      }));

      try {
        const response = await settingsApi.updateLlmSettings(data);

        if (response.error) {
          setState((prev) => ({
            ...prev,
            isSaving: false,
            error: response.error ?? "Failed to save settings",
          }));
          return null;
        }

        const settings = response.data;
        if (!settings) {
          setState((prev) => ({
            ...prev,
            isSaving: false,
            error: "No response from server",
          }));
          return null;
        }

        setState((prev) => ({
          ...prev,
          isSaving: false,
          settings,
        }));

        return settings;
      } catch (err) {
        setState((prev) => ({
          ...prev,
          isSaving: false,
          error: err instanceof Error ? err.message : "Unknown error occurred",
        }));
        return null;
      }
    },
    []
  );

  const clearError = useCallback(() => {
    setState((prev) => ({
      ...prev,
      error: null,
    }));
  }, []);

  return {
    state,
    loadSettings,
    saveSettings,
    clearError,
  };
}
