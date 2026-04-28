"use client";

import { useState, useCallback } from "react";
import { panelHistoryApi } from "@/lib/api/panel-history";
import type { HistoryListItem, HistoryDetail } from "@/lib/api/panel-history";

export interface PanelHistoryState {
  entries: HistoryListItem[];
  currentDetail: HistoryDetail | null;
  isLoading: boolean;
  error: string | null;
}

export interface UsePanelHistoryReturn {
  state: PanelHistoryState;
  loadHistory: () => Promise<void>;
  loadDetail: (id: string) => Promise<void>;
  clearError: () => void;
}

const initialState: PanelHistoryState = {
  entries: [],
  currentDetail: null,
  isLoading: false,
  error: null,
};

export function usePanelHistory(): UsePanelHistoryReturn {
  const [state, setState] = useState<PanelHistoryState>(initialState);

  const loadHistory = useCallback(async (): Promise<void> => {
    setState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
    }));

    try {
      const response = await panelHistoryApi.listHistory();

      if (response.error) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: response.error ?? "加载历史记录失败",
        }));
        return;
      }

      const entries = response.data ?? [];

      setState((prev) => ({
        ...prev,
        isLoading: false,
        entries,
      }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : "发生未知错误",
      }));
    }
  }, []);

  const loadDetail = useCallback(async (id: string): Promise<void> => {
    setState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
    }));

    try {
      const response = await panelHistoryApi.getHistoryDetail(id);

      if (response.error) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: response.error ?? "加载详情失败",
        }));
        return;
      }

      const detail = response.data;
      if (!detail) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: "未找到记录",
        }));
        return;
      }

      setState((prev) => ({
        ...prev,
        isLoading: false,
        currentDetail: detail,
      }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : "发生未知错误",
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
    loadHistory,
    loadDetail,
    clearError,
  };
}
