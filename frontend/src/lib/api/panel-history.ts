import { apiClient } from "@/lib/api-client";

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

export const panelHistoryApi = {
  listHistory: async () => {
    const response = await apiClient.get<PanelHistoryListEnvelope>("/panel-history");
    if (response.error) return { error: response.error, data: undefined };
    return { error: undefined as string | null | undefined, data: response.data?.items as HistoryListItem[] | undefined };
  },

  getHistoryDetail: async (id: string) => {
    const response = await apiClient.get<PanelHistoryDetailEnvelope>(`/panel-history/${id}`);
    if (response.error) return { error: response.error, data: undefined };
    return { error: undefined as string | null | undefined, data: response.data?.item as HistoryDetail | undefined };
  },
};
