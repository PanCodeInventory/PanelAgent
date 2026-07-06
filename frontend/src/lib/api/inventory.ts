import { apiClient } from "@/lib/api-client";
import type { components } from "@/lib/api/generated";

export type InventoryFile = components["schemas"]["InventoryFile"];
export type InventoryUploadResponse =
  components["schemas"]["InventoryUploadResponse"];

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.trim() || "http://127.0.0.1:8000";

export const inventoryApi = {
  listFiles: () => apiClient.get<InventoryFile[]>("/inventory/files"),

  deleteFile: (filename: string) =>
    apiClient.delete<{ ok: boolean }>(
      `/inventory/files/${encodeURIComponent(filename)}`
    ),

  /**
   * Upload an antibody inventory file (.csv / .xlsx). Uses a raw fetch instead
   * of apiClient because multipart/form-data cannot set Content-Type
   * manually (the browser must define the boundary).
   */
  uploadFile: async (
    file: File
  ): Promise<{ data?: InventoryUploadResponse; error?: string }> => {
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        `${API_BASE_URL}/api/v1/inventory/upload`,
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        const text = await response.text();
        return {
          error: `HTTP ${response.status}: ${text || response.statusText}`,
        };
      }

      const data = (await response.json()) as InventoryUploadResponse;
      return { data };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : "Upload failed",
      };
    }
  },
};
