"use client";

import { useEffect, useMemo, useState, type FormEvent, type KeyboardEvent } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { CardSkeleton, TableSkeleton } from "@/components/ui/loading-skeleton";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import { useQualityRegistry } from "@/lib/hooks/use-quality-registry";
import type {
  CandidateMatch,
  EntityKey,
  QualityIssueCreate,
  ReviewItemResponse,
} from "@/lib/api/quality-registry";
import {
  CheckCircle2,
  ClipboardList,
  FlaskConical,
  History,
  Microscope,
  Search,
  ShieldAlert,
} from "lucide-react";

type TabValue = "register" | "history" | "review";
type BadgeVariant = "default" | "secondary" | "destructive" | "outline" | "ghost" | "link";

interface FormState {
  issue_text: string;
  reported_by: string;
  species: string;
  marker: string;
  fluorochrome: string;
  brand: string;
}

interface FormErrors {
  issue_text?: string;
  reported_by?: string;
}

interface ReviewDraft {
  reviewer: string;
  clone: string;
  catalog_number: string;
  lot_number: string;
}

const initialFormState: FormState = {
  issue_text: "",
  reported_by: "",
  species: "Mouse (小鼠)",
  marker: "",
  fluorochrome: "",
  brand: "",
};

function serializeEntityKey(entityKey: EntityKey): string {
  return JSON.stringify(entityKey);
}

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString();
}

function getStatusVariant(status: string): BadgeVariant {
  if (status === "confirmed" || status === "resolved") return "default";
  if (status === "pending_review") return "destructive";
  return "secondary";
}

function buildReviewEntityKey(item: ReviewItemResponse, draft: ReviewDraft): EntityKey | null {
  const clone = draft.clone.trim();
  const catalogNumber = draft.catalog_number.trim();

  if (!clone || !catalogNumber) {
    return null;
  }

  return {
    species: item.feedback_key.species,
    normalized_marker: item.feedback_key.normalized_marker,
    clone,
    brand: item.feedback_key.brand,
    catalog_number: catalogNumber,
    lot_number: draft.lot_number.trim() || undefined,
  };
}

export default function QualityRegistryPage() {
  const {
    state,
    clearError,
    confirmCandidate,
    createIssue,
    getHistory,
    listIssues,
    loadReviewQueue,
    lookupCandidates,
    resolveReview,
  } = useQualityRegistry();

  const [activeTab, setActiveTab] = useState<TabValue>("register");
  const [form, setForm] = useState<FormState>(initialFormState);
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [selectedIssueId, setSelectedIssueId] = useState<string | null>(null);
  const [candidateModalOpen, setCandidateModalOpen] = useState(false);
  const [selectedCandidateKey, setSelectedCandidateKey] = useState("");
  const [confirmedCandidate, setConfirmedCandidate] = useState<CandidateMatch | null>(null);
  const [confirmedLookupKey, setConfirmedLookupKey] = useState("");
  const [dismissedLookupKey, setDismissedLookupKey] = useState("");
  const [reviewDrafts, setReviewDrafts] = useState<Record<string, ReviewDraft>>({});
  const [reviewErrors, setReviewErrors] = useState<Record<string, string>>({});

  const currentLookupKey = useMemo(
    () => [form.species, form.marker.trim(), form.fluorochrome.trim(), form.brand.trim()].join("::"),
    [form.brand, form.fluorochrome, form.marker, form.species]
  );

  const lookupReady = Boolean(
    form.marker.trim() && form.fluorochrome.trim() && form.brand.trim()
  );

  const historyEvents = useMemo(
    () => [...state.history].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()),
    [state.history]
  );

  useEffect(() => {
    void listIssues();
  }, [listIssues]);

  useEffect(() => {
    if (activeTab === "review") {
      void loadReviewQueue();
    }
  }, [activeTab, loadReviewQueue]);

  useEffect(() => {
    if (!lookupReady) {
      return;
    }

    let cancelled = false;
    const timeoutId = window.setTimeout(async () => {
      const candidates = await lookupCandidates({
        text: [form.marker, form.fluorochrome, form.brand, form.issue_text]
          .map((value) => value.trim())
          .filter(Boolean)
          .join(" "),
        species: form.species,
        marker: form.marker.trim(),
        fluorochrome: form.fluorochrome.trim(),
        brand: form.brand.trim() || undefined,
      });

      if (cancelled) {
        return;
      }

      if (candidates.length === 0) {
        setCandidateModalOpen(false);
        setSelectedCandidateKey("");
        setConfirmedCandidate(null);
        setConfirmedLookupKey("");
        return;
      }

      const availableKeys = candidates.map((candidate) => serializeEntityKey(candidate.entity_key));
      setSelectedCandidateKey((prev) => (availableKeys.includes(prev) ? prev : availableKeys[0]));

      if (currentLookupKey === confirmedLookupKey || currentLookupKey === dismissedLookupKey) {
        return;
      }

      setCandidateModalOpen(true);
    }, 500);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [
    confirmedLookupKey,
    currentLookupKey,
    dismissedLookupKey,
    form.brand,
    form.fluorochrome,
    form.issue_text,
    form.marker,
    form.species,
    lookupCandidates,
    lookupReady,
  ]);

  const handleTabChange = (value: string) => {
    setActiveTab(value as TabValue);
    clearError();
  };

  const handleFormChange = (field: keyof FormState, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setFormErrors((prev) => ({ ...prev, [field]: undefined }));

    if (field === "marker" || field === "fluorochrome" || field === "brand" || field === "species") {
      setCandidateModalOpen(false);
      setSelectedCandidateKey("");
      setConfirmedCandidate(null);
      setConfirmedLookupKey("");
      setDismissedLookupKey("");
    }

    if (state.error) {
      clearError();
    }
  };

  const resetForm = () => {
    setForm(initialFormState);
    setFormErrors({});
    setCandidateModalOpen(false);
    setSelectedCandidateKey("");
    setConfirmedCandidate(null);
    setConfirmedLookupKey("");
    setDismissedLookupKey("");
  };

  const handleCandidateModalChange = (open: boolean) => {
    setCandidateModalOpen(open);
    if (!open && currentLookupKey !== confirmedLookupKey) {
      setDismissedLookupKey(currentLookupKey);
    }
  };

  const handleCandidateDismiss = () => {
    setCandidateModalOpen(false);
    setSelectedCandidateKey("");
    setConfirmedCandidate(null);
    setConfirmedLookupKey("");
    setDismissedLookupKey(currentLookupKey);
  };

  const handleCandidateConfirm = () => {
    const candidate = state.candidates.find(
      (item) => serializeEntityKey(item.entity_key) === selectedCandidateKey
    );

    if (!candidate) {
      return;
    }

    setConfirmedCandidate(candidate);
    setConfirmedLookupKey(currentLookupKey);
    setDismissedLookupKey("");
    setCandidateModalOpen(false);
  };

  const handleIssueRowSelect = async (issueId: string) => {
    setSelectedIssueId(issueId);
    await getHistory(issueId);
  };

  const handleIssueRowKeyDown = (event: KeyboardEvent<HTMLTableRowElement>, issueId: string) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      void handleIssueRowSelect(issueId);
    }
  };

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const nextErrors: FormErrors = {};
    if (!form.issue_text.trim()) {
      nextErrors.issue_text = "Please describe the observed quality issue.";
    }
    if (!form.reported_by.trim()) {
      nextErrors.reported_by = "Reporter name is required.";
    }

    setFormErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) {
      return;
    }

    const payload: QualityIssueCreate = {
      issue_text: form.issue_text.trim(),
      reported_by: form.reported_by.trim(),
      species: form.species,
      marker: form.marker.trim(),
      fluorochrome: form.fluorochrome.trim(),
      brand: form.brand.trim(),
      clone: confirmedCandidate?.entity_key.clone,
    };

    const createdIssue = await createIssue(payload);
    if (!createdIssue) {
      return;
    }

    let finalIssueId = createdIssue.id;

    if (confirmedCandidate && currentLookupKey === confirmedLookupKey) {
      const confirmedIssue = await confirmCandidate({
        issue_id: createdIssue.id,
        entity_key: confirmedCandidate.entity_key,
      });

      if (confirmedIssue) {
        finalIssueId = confirmedIssue.id;
      }
    }

    await listIssues();
    await getHistory(finalIssueId);
    setSelectedIssueId(finalIssueId);
    resetForm();
    setActiveTab("history");
  };

  const handleReviewDraftChange = (
    issueId: string,
    field: keyof ReviewDraft,
    value: string
  ) => {
    setReviewDrafts((prev) => ({
      ...prev,
      [issueId]: {
        reviewer: prev[issueId]?.reviewer ?? "",
        clone: prev[issueId]?.clone ?? "",
        catalog_number: prev[issueId]?.catalog_number ?? "",
        lot_number: prev[issueId]?.lot_number ?? "",
        [field]: value,
      },
    }));
    setReviewErrors((prev) => ({ ...prev, [issueId]: "" }));
  };

  const handleResolveReview = async (item: ReviewItemResponse) => {
    const draft = reviewDrafts[item.id] ?? {
      reviewer: "",
      clone: "",
      catalog_number: "",
      lot_number: "",
    };

    if (!draft.reviewer.trim()) {
      setReviewErrors((prev) => ({ ...prev, [item.id]: "Reviewer name is required." }));
      return;
    }

    const hasPartialBinding = Boolean(
      (draft.clone.trim() && !draft.catalog_number.trim()) ||
        (!draft.clone.trim() && draft.catalog_number.trim())
    );

    if (hasPartialBinding) {
      setReviewErrors((prev) => ({
        ...prev,
        [item.id]: "Provide both clone and catalog number to attach an entity binding.",
      }));
      return;
    }

    const entityKey = buildReviewEntityKey(item, draft);
    const resolved = await resolveReview(item.id, {
      reviewer: draft.reviewer.trim(),
      entity_key: entityKey,
    });

    if (!resolved) {
      return;
    }

    setReviewDrafts((prev) => {
      const next = { ...prev };
      delete next[item.id];
      return next;
    });
    setReviewErrors((prev) => ({ ...prev, [item.id]: "" }));
    await listIssues();
    await loadReviewQueue();
    if (selectedIssueId === item.id) {
      await getHistory(item.id);
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          Antibody Quality Registry
        </h1>
        <p className="mt-2 text-muted-foreground">
          Capture reagent issues, confirm likely inventory matches, and keep a transparent audit trail for review.
        </p>
      </div>

      {state.error && (
        <div className="mb-6">
          <ErrorState message={state.error} />
        </div>
      )}

      <Tabs value={activeTab} onValueChange={handleTabChange} className="w-full">
        <TabsList className="mb-6 bg-secondary/30">
          <TabsTrigger
            value="register"
            className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary"
            data-testid="quality-register-tab"
          >
            Register
          </TabsTrigger>
          <TabsTrigger
            value="history"
            className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary"
            data-testid="quality-history-tab"
          >
            Issue History
          </TabsTrigger>
          <TabsTrigger
            value="review"
            className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary"
            data-testid="quality-review-tab"
          >
            Review Queue
          </TabsTrigger>
        </TabsList>

        <TabsContent value="register" className="flex flex-col gap-6">
          <Card className="bg-card border border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg font-semibold text-foreground">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
                  <ShieldAlert className="h-4 w-4 text-primary" />
                </div>
                Issue Registration
              </CardTitle>
              <CardDescription>
                Describe the antibody problem in plain language and let the registry search for likely inventory matches.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form className="flex flex-col gap-6" onSubmit={handleSubmit}>
                <div className="flex flex-col gap-2">
                  <label className="text-sm font-medium text-foreground" htmlFor="quality-issue-text">
                    Issue description
                  </label>
                  <textarea
                    id="quality-issue-text"
                    value={form.issue_text}
                    onChange={(event) => handleFormChange("issue_text", event.target.value)}
                    rows={5}
                    aria-invalid={Boolean(formErrors.issue_text)}
                    data-testid="quality-issue-textarea"
                    placeholder="e.g., CD8 APC lot shows weak staining and increased background in activated mouse splenocytes"
                    className="w-full resize-none rounded-lg border border-border bg-secondary/50 px-3 py-2.5 text-sm text-foreground ring-offset-background transition-colors placeholder:text-muted-foreground focus-visible:border-primary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary/50"
                  />
                  {formErrors.issue_text && (
                    <p className="text-sm text-destructive">{formErrors.issue_text}</p>
                  )}
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="flex flex-col gap-2">
                    <label className="text-sm font-medium text-foreground" htmlFor="quality-reporter">
                      Reporter
                    </label>
                    <Input
                      id="quality-reporter"
                      value={form.reported_by}
                      onChange={(event) => handleFormChange("reported_by", event.target.value)}
                      aria-invalid={Boolean(formErrors.reported_by)}
                      data-testid="quality-reporter-input"
                      placeholder="Your name or team"
                      className="bg-secondary/50 border-border"
                    />
                    {formErrors.reported_by && (
                      <p className="text-sm text-destructive">{formErrors.reported_by}</p>
                    )}
                  </div>

                  <div className="flex flex-col gap-2">
                    <label className="text-sm font-medium text-foreground" htmlFor="quality-species">
                      Species
                    </label>
                    <select
                      id="quality-species"
                      value={form.species}
                      onChange={(event) => handleFormChange("species", event.target.value)}
                      data-testid="quality-species-select"
                      className="w-full rounded-lg border border-border bg-secondary/50 px-3 py-2.5 text-sm font-mono text-foreground ring-offset-background transition-colors focus-visible:border-primary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary/50"
                    >
                      <option>Mouse (小鼠)</option>
                      <option>Human (人)</option>
                    </select>
                  </div>
                </div>

                <div className="grid gap-4 md:grid-cols-3">
                  <div className="flex flex-col gap-2">
                    <label className="text-sm font-medium text-foreground" htmlFor="quality-marker">
                      Marker
                    </label>
                    <Input
                      id="quality-marker"
                      value={form.marker}
                      onChange={(event) => handleFormChange("marker", event.target.value)}
                      data-testid="quality-marker-input"
                      placeholder="CD8"
                      className="bg-secondary/50 border-border"
                    />
                  </div>

                  <div className="flex flex-col gap-2">
                    <label className="text-sm font-medium text-foreground" htmlFor="quality-fluorochrome">
                      Fluorochrome
                    </label>
                    <Input
                      id="quality-fluorochrome"
                      value={form.fluorochrome}
                      onChange={(event) => handleFormChange("fluorochrome", event.target.value)}
                      data-testid="quality-fluorochrome-input"
                      placeholder="APC"
                      className="bg-secondary/50 border-border"
                    />
                  </div>

                  <div className="flex flex-col gap-2">
                    <label className="text-sm font-medium text-foreground" htmlFor="quality-brand">
                      Brand
                    </label>
                    <Input
                      id="quality-brand"
                      value={form.brand}
                      onChange={(event) => handleFormChange("brand", event.target.value)}
                      data-testid="quality-brand-input"
                      placeholder="BioLegend"
                      className="bg-secondary/50 border-border"
                    />
                  </div>
                </div>

                <div className="rounded-lg border border-border bg-secondary/10 p-4">
                  <div className="flex items-center gap-2 text-sm font-medium text-foreground">
                    <Search className="h-4 w-4 text-primary" />
                    Candidate lookup
                  </div>
                  <p className="mt-2 text-sm text-muted-foreground">
                    Inventory lookup runs automatically 500ms after marker, fluorochrome, and brand are filled.
                  </p>
                  {state.isLookingUp && (
                    <p className="mt-3 text-sm text-muted-foreground">
                      Searching inventory for candidate antibodies...
                    </p>
                  )}
                  {confirmedCandidate && (
                    <div className="mt-4 rounded-lg border border-border bg-card/70 p-4">
                      <div className="flex items-center gap-2 text-sm font-medium text-foreground">
                        <CheckCircle2 className="h-4 w-4 text-primary" />
                        Confirmed candidate
                      </div>
                      <div className="mt-3 flex flex-wrap gap-2 text-sm text-muted-foreground">
                        <Badge variant="secondary">{confirmedCandidate.matched_marker ?? confirmedCandidate.entity_key.normalized_marker}</Badge>
                        <Badge variant="outline">{confirmedCandidate.entity_key.clone}</Badge>
                        <Badge variant="outline">{confirmedCandidate.entity_key.brand}</Badge>
                        <Badge variant="outline">{confirmedCandidate.entity_key.catalog_number}</Badge>
                        <Badge variant="outline">{form.fluorochrome.trim() || "Fluorochrome pending"}</Badge>
                      </div>
                    </div>
                  )}
                </div>

                <div className="flex justify-end">
                  <Button
                    type="submit"
                    disabled={state.isLoading || state.isConfirming}
                    data-testid="quality-submit-btn"
                  >
                    <ShieldAlert data-icon="inline-start" />
                    {state.isLoading || state.isConfirming ? "Submitting..." : "Register Issue"}
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history" className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <Card className="bg-card border border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg font-semibold text-foreground">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
                  <History className="h-4 w-4 text-primary" />
                </div>
                Reported Issues
              </CardTitle>
              <CardDescription>
                Review submissions, status changes, and select an issue to inspect its audit timeline.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {state.isLoading && state.issues.length === 0 ? (
                <TableSkeleton rows={6} columns={6} />
              ) : state.issues.length === 0 ? (
                <EmptyState
                  title="No quality issues yet"
                  description="Submitted antibody quality records will appear here once the first report is registered."
                />
              ) : (
                <div
                  className="overflow-hidden rounded-md border border-border"
                  data-testid="quality-issues-list"
                >
                  <table className="w-full text-sm">
                    <thead className="border-b border-border bg-secondary/30">
                      <tr>
                        <th className="px-4 py-3 text-left font-medium text-foreground">Marker</th>
                        <th className="px-4 py-3 text-left font-medium text-foreground">Fluorochrome</th>
                        <th className="px-4 py-3 text-left font-medium text-foreground">Brand</th>
                        <th className="px-4 py-3 text-left font-medium text-foreground">Status</th>
                        <th className="px-4 py-3 text-left font-medium text-foreground">Reporter</th>
                        <th className="px-4 py-3 text-left font-medium text-foreground">Created</th>
                      </tr>
                    </thead>
                    <tbody>
                      {state.issues.map((issue, idx) => (
                        <tr
                          key={issue.id}
                          tabIndex={0}
                          role="button"
                          data-testid={`quality-issue-row-${issue.id}`}
                          onClick={() => void handleIssueRowSelect(issue.id)}
                          onKeyDown={(event) => handleIssueRowKeyDown(event, issue.id)}
                          className={cn(
                            "border-b border-border last:border-b-0 focus-visible:outline-none",
                            idx % 2 === 0 ? "bg-secondary/10" : "",
                            selectedIssueId === issue.id && "bg-primary/5"
                          )}
                        >
                          <td className="px-4 py-3 font-medium text-foreground">
                            {issue.feedback_key.normalized_marker}
                          </td>
                          <td className="px-4 py-3 text-foreground">{issue.feedback_key.fluorochrome}</td>
                          <td className="px-4 py-3 text-foreground">{issue.feedback_key.brand}</td>
                          <td className="px-4 py-3">
                            <Badge variant={getStatusVariant(issue.status)}>{issue.status}</Badge>
                          </td>
                          <td className="px-4 py-3 text-muted-foreground">{issue.reported_by}</td>
                          <td className="px-4 py-3 text-muted-foreground">{formatDateTime(issue.created_at)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="bg-card border border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg font-semibold text-foreground">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
                  <ClipboardList className="h-4 w-4 text-primary" />
                </div>
                Audit Timeline
              </CardTitle>
              <CardDescription>
                Audit events are shown in chronological order for the currently selected issue.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="min-h-[320px]" data-testid="quality-history-panel">
                {state.isLoading && selectedIssueId && historyEvents.length === 0 ? (
                  <CardSkeleton lines={5} />
                ) : !selectedIssueId ? (
                  <EmptyState
                    title="Select an issue"
                    description="Choose a row from the issue list to browse creation, binding, and review events."
                  />
                ) : historyEvents.length === 0 ? (
                  <EmptyState
                    title="No audit events"
                    description="Audit history will appear here once activity exists for the selected issue."
                  />
                ) : (
                  <div className="relative flex flex-col gap-4">
                    <div className="absolute left-[11px] top-3 bottom-3 w-px bg-border" />
                    {historyEvents.map((event) => (
                      <div key={event.event_id} className="relative flex gap-4 rounded-lg border border-border bg-secondary/10 p-4">
                        <div className="relative z-10 flex size-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary">
                          {event.action.slice(0, 1).toUpperCase()}
                        </div>
                        <div className="flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="font-medium text-foreground">{event.action}</p>
                            <Badge variant="outline">{event.actor}</Badge>
                          </div>
                          <p className="mt-1 text-sm text-muted-foreground">{formatDateTime(event.timestamp)}</p>
                          <div className="mt-3 flex flex-col gap-2 text-sm text-muted-foreground">
                            {Object.entries(event.details).map(([key, value]) => (
                              <div key={key} className="rounded-md border border-border bg-card/60 px-3 py-2">
                                <span className="font-medium text-foreground">{key}: </span>
                                <span>{typeof value === "string" ? value : JSON.stringify(value)}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="review" className="flex flex-col gap-6">
          <Card className="bg-card border border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-lg font-semibold text-foreground">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
                  <Microscope className="h-4 w-4 text-primary" />
                </div>
                Manual Review Queue
              </CardTitle>
              <CardDescription>
                Resolve unresolved submissions and optionally attach a canonical antibody entity during review.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {state.isLoading && state.reviewQueue.length === 0 ? (
                <CardSkeleton lines={5} />
              ) : state.reviewQueue.length === 0 ? (
                <EmptyState
                  title="No pending reviews"
                  description="Items requiring manual adjudication will appear here when the backend marks them as pending review."
                />
              ) : (
                <div className="flex flex-col gap-4">
                  {state.reviewQueue.map((item) => {
                    const draft = reviewDrafts[item.id] ?? {
                      reviewer: "",
                      clone: "",
                      catalog_number: "",
                      lot_number: "",
                    };

                    return (
                      <div
                        key={item.id}
                        data-testid={`quality-review-item-${item.id}`}
                        className="rounded-lg border border-border bg-secondary/10 p-5"
                      >
                        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                          <div className="flex-1">
                            <div className="flex flex-wrap items-center gap-2">
                              <Badge variant={getStatusVariant(item.status)}>{item.status}</Badge>
                              <Badge variant="outline">{item.feedback_key.normalized_marker}</Badge>
                              <Badge variant="outline">{item.feedback_key.fluorochrome}</Badge>
                              <Badge variant="outline">{item.feedback_key.brand}</Badge>
                            </div>
                            <p className="mt-3 text-sm text-foreground">{item.issue_text}</p>
                            <p className="mt-2 text-sm text-muted-foreground">
                              Reported by {item.reported_by} on {formatDateTime(item.created_at)}
                            </p>
                          </div>

                          <div className="grid gap-3 lg:min-w-[340px]">
                            <Input
                              value={draft.reviewer}
                              onChange={(event) => handleReviewDraftChange(item.id, "reviewer", event.target.value)}
                              placeholder="Reviewer name"
                              data-testid={`quality-reviewer-input-${item.id}`}
                              className="bg-card border-border"
                            />
                            <div className="grid gap-3 md:grid-cols-2">
                              <Input
                                value={draft.clone}
                                onChange={(event) => handleReviewDraftChange(item.id, "clone", event.target.value)}
                                placeholder="Clone (optional)"
                                data-testid={`quality-review-clone-input-${item.id}`}
                                className="bg-card border-border"
                              />
                              <Input
                                value={draft.catalog_number}
                                onChange={(event) => handleReviewDraftChange(item.id, "catalog_number", event.target.value)}
                                placeholder="Catalog number (optional)"
                                data-testid={`quality-review-catalog-input-${item.id}`}
                                className="bg-card border-border"
                              />
                            </div>
                            <Input
                              value={draft.lot_number}
                              onChange={(event) => handleReviewDraftChange(item.id, "lot_number", event.target.value)}
                              placeholder="Lot number (optional)"
                              data-testid={`quality-review-lot-input-${item.id}`}
                              className="bg-card border-border"
                            />
                            {reviewErrors[item.id] && (
                              <p className="text-sm text-destructive">{reviewErrors[item.id]}</p>
                            )}
                            <Button
                              onClick={() => void handleResolveReview(item)}
                              data-testid={`quality-resolve-btn-${item.id}`}
                              disabled={state.isLoading}
                            >
                              <FlaskConical data-icon="inline-start" />
                              Resolve Review
                            </Button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Dialog open={candidateModalOpen} onOpenChange={handleCandidateModalChange}>
        <DialogContent
          className="sm:max-w-3xl"
          data-testid="quality-candidate-modal"
        >
          <DialogHeader>
            <DialogTitle>Select a candidate antibody</DialogTitle>
            <DialogDescription>
              Choose the closest inventory record. The confirmed match will be attached when the issue is submitted.
            </DialogDescription>
          </DialogHeader>

          <div className="overflow-hidden rounded-md border border-border">
            <div className="max-h-[55vh] overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="border-b border-border bg-secondary/30">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-foreground">Select</th>
                    <th className="px-4 py-3 text-left font-medium text-foreground">Marker</th>
                    <th className="px-4 py-3 text-left font-medium text-foreground">Clone</th>
                    <th className="px-4 py-3 text-left font-medium text-foreground">Brand</th>
                    <th className="px-4 py-3 text-left font-medium text-foreground">Catalog</th>
                    <th className="px-4 py-3 text-left font-medium text-foreground">Fluorochrome</th>
                    <th className="px-4 py-3 text-left font-medium text-foreground">Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {state.candidates.map((candidate, index) => {
                    const candidateKey = serializeEntityKey(candidate.entity_key);

                    return (
                      <tr
                        key={candidateKey}
                        data-testid={`quality-candidate-item-${index}`}
                        className={cn(
                          "border-b border-border last:border-b-0",
                          index % 2 === 0 ? "bg-secondary/10" : ""
                        )}
                      >
                        <td className="px-4 py-3 align-top">
                          <input
                            type="radio"
                            name="quality-candidate"
                            checked={selectedCandidateKey === candidateKey}
                            onChange={() => setSelectedCandidateKey(candidateKey)}
                            data-testid={`quality-candidate-radio-${index}`}
                            className="mt-1 h-4 w-4 accent-primary"
                          />
                        </td>
                        <td className="px-4 py-3 font-medium text-foreground">
                          {candidate.matched_marker ?? candidate.entity_key.normalized_marker}
                        </td>
                        <td className="px-4 py-3 text-foreground">{candidate.entity_key.clone}</td>
                        <td className="px-4 py-3 text-foreground">{candidate.entity_key.brand}</td>
                        <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                          {candidate.entity_key.catalog_number}
                        </td>
                        <td className="px-4 py-3 text-foreground">{form.fluorochrome.trim() || "—"}</td>
                        <td className="px-4 py-3">
                          <Badge variant="secondary">{Math.round(candidate.confidence * 100)}%</Badge>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={handleCandidateDismiss}
              data-testid="quality-cancel-candidate-btn"
            >
              Cancel
            </Button>
            <Button
              onClick={handleCandidateConfirm}
              disabled={!selectedCandidateKey}
              data-testid="quality-confirm-candidate-btn"
            >
              <CheckCircle2 data-icon="inline-start" />
              Confirm Candidate
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
