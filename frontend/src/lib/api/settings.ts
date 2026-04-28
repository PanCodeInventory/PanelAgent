import { apiClient } from "@/lib/api-client";
import type { components } from "@/lib/api/generated";

export type LlmSettingsResponse = components["schemas"]["LlmSettingsResponse"];
export type LlmSettingsUpdate = components["schemas"]["LlmSettingsUpdate"];

export const settingsApi = {
  getLlmSettings: () =>
    apiClient.get<LlmSettingsResponse>("/settings/llm"),

  updateLlmSettings: (data: LlmSettingsUpdate) =>
    apiClient.put<LlmSettingsResponse>("/settings/llm", data),
};
