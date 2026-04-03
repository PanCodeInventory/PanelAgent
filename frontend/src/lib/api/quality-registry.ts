/**
 * TypeScript types and API client functions for the antibody quality registry.
 *
 * Mirrors the Pydantic schemas from backend/app/schemas/quality_registry.py
 * and the API endpoints from backend/app/api/v1/endpoints/quality_registry.py
 */

import { apiClient } from "@/lib/api-client";

// ---------------------------------------------------------------------------
// A. FeedbackKey — submission identity (clone optional)
// ---------------------------------------------------------------------------

export interface FeedbackKey {
  species: string;
  normalized_marker: string;
  fluorochrome: string;
  brand: string;
  clone?: string | null;
}

// ---------------------------------------------------------------------------
// B. EntityKey — canonical antibody identity (all required, lot as metadata)
// ---------------------------------------------------------------------------

export interface EntityKey {
  species: string;
  normalized_marker: string;
  clone: string;
  brand: string;
  catalog_number: string;
  lot_number?: string | null;
}

// ---------------------------------------------------------------------------
// C. Quality Issue Record
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// D. Candidate Match (lookup disambiguation)
// ---------------------------------------------------------------------------

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

// ---------------------------------------------------------------------------
// E. Manual Review Item
// ---------------------------------------------------------------------------

export interface ReviewItemResponse {
  id: string;
  feedback_key: FeedbackKey;
  entity_key: EntityKey | null;
  issue_text: string;
  reported_by: string;
  status: string;
  reviewer?: string | null;
  reviewed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ResolveReviewRequest {
  reviewer: string;
  entity_key?: EntityKey | null;
}

// ---------------------------------------------------------------------------
// F. Audit Event
// ---------------------------------------------------------------------------

export interface AuditEvent {
  event_id: string;
  issue_id: string;
  action: string;
  actor: string;
  details: Record<string, unknown>;
  timestamp: string;
}

// ---------------------------------------------------------------------------
// API Functions
// ---------------------------------------------------------------------------

export const qualityRegistryApi = {
  /**
   * POST /quality-registry/issues
   * Create a new quality issue
   */
  createIssue: (data: QualityIssueCreate) =>
    apiClient.post<QualityIssueResponse>("/quality-registry/issues", data),

  /**
   * GET /quality-registry/issues?status=...
   * List quality issues, optionally filtered by status
   */
  listIssues: (status?: string) =>
    apiClient.get<QualityIssueResponse[]>(
      `/quality-registry/issues${status ? `?status=${status}` : ""}`
    ),

  /**
   * GET /quality-registry/issues/{issue_id}
   * Get a single quality issue by ID
   */
  getIssue: (issueId: string) =>
    apiClient.get<QualityIssueResponse>(`/quality-registry/issues/${issueId}`),

  /**
   * GET /quality-registry/issues/{issue_id}/history
   * Get audit history for a quality issue
   */
  getHistory: (issueId: string) =>
    apiClient.get<AuditEvent[]>(`/quality-registry/issues/${issueId}/history`),

  /**
   * POST /quality-registry/candidates/lookup
   * Look up candidate antibody matches from inventory
   */
  lookupCandidates: (data: CandidateLookupRequest) =>
    apiClient.post<CandidateLookupResponse>(
      "/quality-registry/candidates/lookup",
      data
    ),

  /**
   * POST /quality-registry/candidates/confirm
   * Confirm a candidate entity selection for a quality issue
   */
  confirmCandidate: (data: CandidateConfirmRequest) =>
    apiClient.post<QualityIssueResponse>(
      "/quality-registry/candidates/confirm",
      data
    ),

  /**
   * GET /quality-registry/review-queue
   * List all issues in pending_review status
   */
  getReviewQueue: () =>
    apiClient.get<ReviewItemResponse[]>("/quality-registry/review-queue"),

  /**
   * POST /quality-registry/review-queue/{issue_id}/resolve
   * Resolve a manual review item
   */
  resolveReview: (issueId: string, data: ResolveReviewRequest) =>
    apiClient.post<QualityIssueResponse>(
      `/quality-registry/review-queue/${issueId}/resolve`,
      data
    ),
};