"use client";

import { useMemo, useState, type FormEvent } from "react";
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
import { ErrorState } from "@/components/ui/error-state";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { useQualityRegistry } from "@/lib/hooks/use-quality-registry";
import type {
  CandidateMatch,
  EntityKey,
  QualityIssueCreate,
} from "@/lib/api/quality-registry";
import {
  CheckCircle2,
  Search,
  ShieldAlert,
} from "lucide-react";

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

export default function QualityRegistryPage() {
  const {
    state,
    clearError,
    confirmCandidate,
    createIssue,
    lookupCandidates,
  } = useQualityRegistry();

  const [form, setForm] = useState<FormState>(initialFormState);
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [candidateModalOpen, setCandidateModalOpen] = useState(false);
  const [selectedCandidateKey, setSelectedCandidateKey] = useState("");
  const [confirmedCandidate, setConfirmedCandidate] = useState<CandidateMatch | null>(null);
  const [confirmedLookupKey, setConfirmedLookupKey] = useState("");
  const [dismissedLookupKey, setDismissedLookupKey] = useState("");
  const [submitSuccess, setSubmitSuccess] = useState(false);

  const currentLookupKey = useMemo(
    () => [form.species, form.marker.trim(), form.fluorochrome.trim()].join("::"),
    [form.fluorochrome, form.marker, form.species]
  );

  const lookupReady = Boolean(
    form.marker.trim() && form.fluorochrome.trim()
  );

  const [lookupTimeout, setLookupTimeout] = useState<number | null>(null);

  const handleFormChange = (field: keyof FormState, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setFormErrors((prev) => ({ ...prev, [field]: undefined }));
    setSubmitSuccess(false);

    if (field === "marker" || field === "fluorochrome" || field === "species") {
      setCandidateModalOpen(false);
      setSelectedCandidateKey("");
      setConfirmedCandidate(null);
      setConfirmedLookupKey("");
      setDismissedLookupKey("");
      if (lookupTimeout) {
        window.clearTimeout(lookupTimeout);
      }

      const newValue = field === "marker" || field === "fluorochrome" ? value.trim() : form.marker.trim();
      const newFluor = field === "fluorochrome" ? value.trim() : form.fluorochrome.trim();

      if (newValue && newFluor) {
        const timeout = window.setTimeout(async () => {
          const candidates = await lookupCandidates({
            text: [newValue, newFluor, form.issue_text]
              .map((v) => v.trim())
              .filter(Boolean)
              .join(" "),
            species: field === "species" ? value : form.species,
            marker: newValue,
            fluorochrome: newFluor,
          });

          if (candidates.length === 0) {
            setCandidateModalOpen(false);
            setSelectedCandidateKey("");
            setConfirmedCandidate(null);
            setConfirmedLookupKey("");
            return;
          }

          const availableKeys = candidates.map((candidate) => serializeEntityKey(candidate.entity_key));
          setSelectedCandidateKey((prev) => (availableKeys.includes(prev) ? prev : availableKeys[0]));

          const currentKey = [field === "species" ? value : form.species, newValue, newFluor].join("::");
          if (currentKey === confirmedLookupKey || currentKey === dismissedLookupKey) {
            return;
          }

          setCandidateModalOpen(true);
        }, 500);

        setLookupTimeout(timeout);
      }
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
    setSubmitSuccess(true);
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

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const nextErrors: FormErrors = {};
    if (!form.issue_text.trim()) {
      nextErrors.issue_text = "请描述观察到的质量问题。";
    }
    if (!form.reported_by.trim()) {
      nextErrors.reported_by = "请填写报告人姓名。";
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

    if (confirmedCandidate && currentLookupKey === confirmedLookupKey) {
      await confirmCandidate({
        issue_id: createdIssue.id,
        entity_key: confirmedCandidate.entity_key,
      });
    }

    resetForm();
  };

  return (
    <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          抗体质量登记
        </h1>
        <p className="mt-2 text-muted-foreground">
          记录试剂问题，系统将自动搜索可能的库存匹配。
        </p>
      </div>

      {state.error && (
        <div className="mb-6">
          <ErrorState message={state.error} />
        </div>
      )}

      {submitSuccess && (
        <div className="mb-6 rounded-lg border border-green-200 bg-green-50 p-4 text-green-800">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-5 w-5" />
            <span className="font-medium">问题已成功提交！</span>
          </div>
          <p className="mt-1 text-sm text-green-700">
            感谢您的反馈，我们将尽快处理您的质量问题报告。
          </p>
        </div>
      )}

      <Card className="bg-card border border-border">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
              <ShieldAlert className="h-4 w-4 text-primary" />
            </div>
            问题登记
          </CardTitle>
          <CardDescription>
            用自然语言描述抗体问题，系统将自动搜索可能的库存匹配。
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form className="flex flex-col gap-6" onSubmit={handleSubmit}>
            <div className="flex flex-col gap-2">
              <label className="text-sm font-medium text-foreground" htmlFor="quality-issue-text">
                问题描述
              </label>
              <textarea
                id="quality-issue-text"
                value={form.issue_text}
                onChange={(event) => handleFormChange("issue_text", event.target.value)}
                rows={5}
                aria-invalid={Boolean(formErrors.issue_text)}
                data-testid="quality-issue-textarea"
                placeholder="例如：CD8 APC 批次在小鼠活化脾细胞中染色偏弱且背景升高"
                className="w-full resize-none rounded-lg border border-border bg-secondary/50 px-3 py-2.5 text-sm text-foreground ring-offset-background transition-colors placeholder:text-muted-foreground focus-visible:border-primary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary/50"
              />
              {formErrors.issue_text && (
                <p className="text-sm text-destructive">{formErrors.issue_text}</p>
              )}
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-foreground" htmlFor="quality-reporter">
                  报告人
                </label>
                <Input
                  id="quality-reporter"
                  value={form.reported_by}
                  onChange={(event) => handleFormChange("reported_by", event.target.value)}
                  aria-invalid={Boolean(formErrors.reported_by)}
                  data-testid="quality-reporter-input"
                  placeholder="您的姓名或团队"
                  className="bg-secondary/50 border-border"
                />
                {formErrors.reported_by && (
                  <p className="text-sm text-destructive">{formErrors.reported_by}</p>
                )}
              </div>

              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-foreground" htmlFor="quality-species">
                  物种
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

            <div className="grid gap-4 md:grid-cols-2">
              <div className="flex flex-col gap-2">
                <label className="text-sm font-medium text-foreground" htmlFor="quality-marker">
                  标志物
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
                  荧光素
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
            </div>

            <div className="rounded-lg border border-border bg-secondary/10 p-4">
              <div className="flex items-center gap-2 text-sm font-medium text-foreground">
                <Search className="h-4 w-4 text-primary" />
                候选抗体查找
              </div>
              <p className="mt-2 text-sm text-muted-foreground">
                在填写标志物和荧光素后，库存查找将在500毫秒后自动运行。
              </p>
              {state.isLookingUp && (
                <p className="mt-3 text-sm text-muted-foreground">
                  正在搜索库存中的候选抗体...
                </p>
              )}
              {confirmedCandidate && (
                <div className="mt-4 rounded-lg border border-border bg-card/70 p-4">
                  <div className="flex items-center gap-2 text-sm font-medium text-foreground">
                    <CheckCircle2 className="h-4 w-4 text-primary" />
                    已确认候选
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2 text-sm text-muted-foreground">
                    <Badge variant="secondary">{confirmedCandidate.matched_marker ?? confirmedCandidate.entity_key.normalized_marker}</Badge>
                    <Badge variant="outline">{confirmedCandidate.entity_key.clone}</Badge>
                    <Badge variant="outline">{confirmedCandidate.entity_key.brand}</Badge>
                    <Badge variant="outline">{confirmedCandidate.entity_key.catalog_number}</Badge>
                    <Badge variant="outline">{form.fluorochrome.trim() || "荧光素待定"}</Badge>
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
                {state.isLoading || state.isConfirming ? "提交中..." : "登记问题"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Dialog open={candidateModalOpen} onOpenChange={handleCandidateModalChange}>
        <DialogContent
          className="sm:max-w-3xl"
          data-testid="quality-candidate-modal"
        >
          <DialogHeader>
            <DialogTitle>选择候选抗体</DialogTitle>
            <DialogDescription>
              选择最匹配的库存记录。确认的匹配将在问题提交时附加。
            </DialogDescription>
          </DialogHeader>

          <div className="overflow-hidden rounded-md border border-border">
            <div className="max-h-[55vh] overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="border-b border-border bg-secondary/30">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-foreground">选择</th>
                    <th className="px-4 py-3 text-left font-medium text-foreground">标志物</th>
                    <th className="px-4 py-3 text-left font-medium text-foreground">克隆号</th>
                    <th className="px-4 py-3 text-left font-medium text-foreground">品牌</th>
                    <th className="px-4 py-3 text-left font-medium text-foreground">目录号</th>
                    <th className="px-4 py-3 text-left font-medium text-foreground">荧光素</th>
                    <th className="px-4 py-3 text-left font-medium text-foreground">置信度</th>
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
              取消
            </Button>
            <Button
              onClick={handleCandidateConfirm}
              disabled={!selectedCandidateKey}
              data-testid="quality-confirm-candidate-btn"
            >
              <CheckCircle2 data-icon="inline-start" />
              确认候选
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
