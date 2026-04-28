"use client";

import { useState, useCallback } from "react";
import { adminFetch, adminPut } from "@/lib/api/admin-client";

export interface LlmSettingsResponse {
  api_base: string;
  model_name: string;
  has_api_key: boolean;
}

export interface LlmSettingsUpdate {
  api_base?: string;
  model_name?: string;
  api_key?: string;
}

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
      const settings = await adminFetch<LlmSettingsResponse>("/settings/llm");

      setState((prev) => ({
        ...prev,
        isLoading: false,
        settings,
      }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : "加载设置失败",
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
        const settings = await adminPut<LlmSettingsResponse>("/settings/llm", data);

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
          error: err instanceof Error ? err.message : "保存设置失败",
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
