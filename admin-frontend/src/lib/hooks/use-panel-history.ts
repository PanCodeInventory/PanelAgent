"use client";

import { useState, useCallback } from "react";
import { adminFetch } from "@/lib/api/admin-client";

export interface SelectedAntibody {
  marker: string;
  fluorochrome: string;
  brightness: number;
  system_code?: string | null;
  brand?: string | null;
  clone?: string | null;
  stock?: number | null;
}

export interface HistoryListItem {
  id: string;
  created_at: string;
  species: string;
  inventory_file: string;
  requested_markers: string[];
  missing_markers: string[];
  model_name: string;
}

export interface HistoryDetail {
  id: string;
  created_at: string;
  species: string;
  inventory_file: string;
  requested_markers: string[];
  missing_markers: string[];
  selected_panel: SelectedAntibody[];
  rationale: string;
  model_name: string;
  api_base: string;
}

interface PanelHistoryListEnvelope {
  items: HistoryListItem[];
  total: number;
}

interface PanelHistoryDetailEnvelope {
  item: HistoryDetail;
}

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
      const response = await adminFetch<PanelHistoryListEnvelope>("/panel-history");

      setState((prev) => ({
        ...prev,
        isLoading: false,
        entries: response.items ?? [],
      }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : "加载历史记录失败",
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
      const response = await adminFetch<PanelHistoryDetailEnvelope>(`/panel-history/${id}`);

      if (!response.item) {
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
        currentDetail: response.item,
      }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : "加载详情失败",
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
