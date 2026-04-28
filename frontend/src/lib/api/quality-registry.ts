import { apiClient } from "@/lib/api-client";

export interface FeedbackKey {
  species: string;
  normalized_marker: string;
  fluorochrome: string;
  brand: string;
  clone?: string | null;
}

export interface EntityKey {
  species: string;
  normalized_marker: string;
  clone: string;
  brand: string;
  catalog_number: string;
  lot_number?: string | null;
}

export interface QualityIssueCreate {
  issue_text: string;
  reported_by: string;
  species: string;
  marker: string;
  fluorochrome: string;
  brand: string;
  clone?: string | null;
}

export interface QualityIssueResponse {
  id: string;
  feedback_key: FeedbackKey;
  entity_key: EntityKey | null;
  issue_text: string;
  reported_by: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface CandidateLookupRequest {
  text: string;
  species?: string | null;
  marker?: string | null;
  fluorochrome?: string | null;
  brand?: string | null;
}

export interface CandidateMatch {
  entity_key: EntityKey;
  confidence: number;
  source: string;
  matched_marker?: string | null;
}

export interface CandidateLookupResponse {
  candidates: CandidateMatch[];
}

export interface CandidateConfirmRequest {
  issue_id: string;
  entity_key: EntityKey;
}

export const qualityRegistryApi = {
  createIssue: (data: QualityIssueCreate) =>
    apiClient.post<QualityIssueResponse>("/quality-registry/issues", data),

  lookupCandidates: (data: CandidateLookupRequest) =>
    apiClient.post<CandidateLookupResponse>(
      "/quality-registry/candidates/lookup",
      data
    ),

  confirmCandidate: (data: CandidateConfirmRequest) =>
    apiClient.post<QualityIssueResponse>(
      "/quality-registry/candidates/confirm",
      data
    ),
};
