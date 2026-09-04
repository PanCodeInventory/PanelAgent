import { apiClient } from "@/lib/api-client";
import type { components } from "@/lib/api/generated";

export type LlmSettingsResponse = components["schemas"]["LlmSettingsResponse"];
export type ProviderPreset = components["schemas"]["ProviderPreset"];

export const settingsApi = {
  getLlmSettings: () =>
    apiClient.get<LlmSettingsResponse>("/settings/llm"),

  getProviders: () =>
    apiClient.get<ProviderPreset[]>("/settings/providers"),
};
