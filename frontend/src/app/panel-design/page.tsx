"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { usePanelGeneration } from "@/lib/hooks/use-panel-generation";
import { usePanelEvaluation } from "@/lib/hooks/use-panel-evaluation";
import { SpectraChart } from "@/components/spectra-chart";
import type { components } from "@/lib/api/generated";
import { cn } from "@/lib/utils";
import { TableSkeleton, CardSkeleton } from "@/components/ui/loading-skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { EmptyState } from "@/components/ui/empty-state";
import {
  Search,
  Bot,
  BarChart3,
  AlertTriangle,
  Sparkles,
  Beaker,
  ChevronRight,
} from "lucide-react";

type PanelCandidate = components["schemas"]["PanelCandidate"];
type AntibodyInfo = components["schemas"]["AntibodyInfo"];

interface CandidateTableProps {
  candidate: PanelCandidate;
}

const getBrightnessColor = (b: number) => {
  if (b >= 4) return "bg-emerald-400";
  if (b >= 3) return "bg-yellow-400";
  return "bg-red-400";
};

function CandidateTable({ candidate }: CandidateTableProps) {
  const entries = Object.entries(candidate).map(([marker, info]) => ({
    marker,
    ...(info as AntibodyInfo),
  }));

  return (
    <div className="rounded-md border border-border">
      <table className="w-full text-sm">
        <thead className="border-b border-border bg-secondary/30">
          <tr>
            <th className="px-4 py-2 text-left font-medium text-foreground">Marker</th>
            <th className="px-4 py-2 text-left font-medium text-foreground">Fluorochrome</th>
            <th className="px-4 py-2 text-left font-medium text-foreground">System Code</th>
            <th className="px-4 py-2 text-left font-medium text-foreground">Brightness</th>
            <th className="px-4 py-2 text-left font-medium text-foreground">Clone</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry, idx) => (
            <tr
              key={`${entry.marker}-${idx}`}
              className={cn(
                "border-b border-border last:border-b-0",
                idx % 2 === 0 ? "bg-secondary/10" : ""
              )}
            >
              <td className="px-4 py-2 font-medium text-foreground">{entry.marker}</td>
              <td className="px-4 py-2 text-foreground">{entry.fluorochrome}</td>
              <td className="px-4 py-2">
                <code className="rounded bg-secondary/50 px-1.5 py-0.5 text-xs font-mono text-foreground">
                  {entry.system_code}
                </code>
              </td>
              <td className="px-4 py-2">
                <div className="flex items-center gap-1">
                  {Array.from({ length: 5 }, (_, i) => (
                    <div
                      key={i}
                      className={cn(
                        "h-1.5 w-1.5 rounded-full",
                        i < entry.brightness
                          ? getBrightnessColor(entry.brightness)
                          : "bg-muted/30"
                      )}
                    />
                  ))}
                </div>
              </td>
              <td className="px-4 py-2 font-mono text-xs text-muted-foreground">
                {entry.clone ?? "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function extractFluorochromes(candidate: PanelCandidate): string[] {
  return Object.values(candidate).map((info) => (info as AntibodyInfo).fluorochrome);
}

function PanelDesignPageContent() {
  const searchParams = useSearchParams();

  const getInitialMarkers = () => {
    const markersParam = searchParams.get("markers");
    if (markersParam) {
      return decodeURIComponent(markersParam);
    }
    return "CD45.2, CD3, NK1.1, Perforin, Granzyme B, TNF-α, IFN-γ";
  };

  const [markers, setMarkers] = useState(getInitialMarkers);
  const [species, setSpecies] = useState("Mouse (小鼠)");
  const [selectedTab, setSelectedTab] = useState("option0");

  const { state: genState, generate, clear: clearGeneration } = usePanelGeneration();
  const { state: evalState, evaluate, clear: clearEvaluation } = usePanelEvaluation();

  useEffect(() => {
    const markersParam = searchParams.get("markers");
    if (markersParam) {
      const decodedMarkers = decodeURIComponent(markersParam);
      const markerList = decodedMarkers.split(",").map((m) => m.trim()).filter(Boolean);
      if (markerList.length > 0) {
        void generate(markerList, species);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSearch = async () => {
    clearEvaluation();
    const markerList = markers.split(",").map((m) => m.trim()).filter(Boolean);
    await generate(markerList, species);
    setSelectedTab("option0");
  };

  const handleClear = () => {
    setMarkers("");
    clearGeneration();
    clearEvaluation();
    setSelectedTab("option0");
  };

  const handleEvaluate = async () => {
    if (genState.candidates.length > 0) {
      await evaluate(genState.candidates, genState.missingMarkers);
    }
  };

  const selectedCandidate = genState.candidates[parseInt(selectedTab.replace("option", "")) || 0];
  const selectedFluorochromes = selectedCandidate ? extractFluorochromes(selectedCandidate) : [];

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          Panel Generation
        </h1>
        <p className="mt-2 text-muted-foreground">
          Generate conflict-free panels from your marker list using backtracking
          search and AI evaluation
        </p>
      </div>

      <Card className="mb-6 bg-card border border-border">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
              <Search className="h-4 w-4 text-primary" />
            </div>
            Marker Input
          </CardTitle>
          <CardDescription>
            Enter target markers separated by commas
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-col gap-4 sm:flex-row">
            <Input
              value={markers}
              onChange={(e) => setMarkers(e.target.value)}
              placeholder="e.g., CD3, CD4, CD8, FoxP3"
              className="flex-1 bg-secondary/50 border-border"
              disabled={genState.isLoading}
            />
            <select
              value={species}
              onChange={(e) => setSpecies(e.target.value)}
              className="rounded-md border border-border bg-secondary/50 px-3 py-2 text-sm font-mono text-foreground ring-offset-background"
              disabled={genState.isLoading}
            >
              <option>Mouse (小鼠)</option>
              <option>Human (人)</option>
            </select>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={handleSearch}
              disabled={genState.isLoading || !markers.trim()}
            >
              {genState.isLoading ? (
                <>
                  <Search className="mr-2 h-4 w-4 animate-pulse" />
                  {genState.isDiagnosing ? "Diagnosing..." : "Searching..."}
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Search Panels
                </>
              )}
            </Button>
            <Button variant="outline" onClick={handleClear} disabled={genState.isLoading}>
              Clear
            </Button>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>Current inventory:</span>
            <Badge variant="secondary" className="font-mono">{species}</Badge>
          </div>
        </CardContent>
      </Card>

      {genState.error && (
        <div className="mb-6">
          <ErrorState message={genState.error} onRetry={handleSearch} />
        </div>
      )}

      {genState.missingMarkers.length > 0 && (
        <Card className="mb-6 border-yellow-500/20 bg-yellow-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-yellow-400">
              <AlertTriangle className="h-5 w-5" />
              Missing Markers
            </CardTitle>
            <CardDescription className="text-yellow-200/70">
              The following markers were not found in the inventory
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {genState.missingMarkers.map((marker) => (
                <Badge key={marker} variant="outline" className="border-yellow-500/50 text-yellow-400 font-mono">
                  {marker}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="mb-6 bg-card border border-border">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
              <Beaker className="h-4 w-4 text-primary" />
            </div>
            Candidate Panels
          </CardTitle>
          <CardDescription>
            Physically valid panel configurations (no channel conflicts)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {genState.candidates.length === 0 && !genState.isLoading && !genState.error && (
            <EmptyState
              title="No candidates yet"
              description="Enter markers above and click Search Panels to generate valid panel configurations"
            />
          )}

          {genState.isLoading && (
            <TableSkeleton rows={5} columns={5} />
          )}

          {genState.candidates.length > 0 && !genState.isLoading && (
            <Tabs
              value={selectedTab}
              onValueChange={setSelectedTab}
              className="w-full"
            >
              <TabsList className="mb-4 bg-secondary/30">
                {genState.candidates.map((_, idx) => (
                  <TabsTrigger
                    key={idx}
                    value={`option${idx}`}
                    className="data-[state=active]:bg-primary/20 data-[state=active]:text-primary"
                  >
                    Option {idx + 1}
                  </TabsTrigger>
                ))}
              </TabsList>
              {genState.candidates.map((candidate, idx) => (
                <TabsContent key={idx} value={`option${idx}`}>
                  <CandidateTable candidate={candidate} />
                </TabsContent>
              ))}
            </Tabs>
          )}
        </CardContent>
      </Card>

      <Card className="mb-6 bg-card border border-border">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
              <Bot className="h-4 w-4 text-primary" />
            </div>
            AI Expert Evaluation
          </CardTitle>
          <CardDescription>
            Let AI analyze candidates and select the best panel
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <Button
            variant="secondary"
            onClick={handleEvaluate}
            disabled={genState.candidates.length === 0 || evalState.isLoading}
          >
            {evalState.isLoading ? (
              <>
                <Sparkles className="mr-2 h-4 w-4 animate-pulse" />
                Evaluating...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Evaluate with AI
              </>
            )}
          </Button>

          {evalState.error && (
            <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4">
              <p className="text-sm text-destructive">
                <span className="font-semibold">Error: </span>
                {evalState.error}
              </p>
            </div>
          )}

          {evalState.isLoading && <CardSkeleton />}

          {evalState.result?.selectedPanel && (
            <div className="rounded-lg border border-primary/30 bg-primary/5 p-6">
              <h4 className="mb-4 flex items-center gap-2 font-semibold text-foreground">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/20 text-xs text-primary">1</span>
                Recommended Panel
              </h4>
              <CandidateTable candidate={evalState.result.selectedPanel} />
            </div>
          )}

          {evalState.result?.rationale && (
            <div className="rounded-lg border border-border bg-card/50 p-6">
              <h4 className="mb-3 flex items-center gap-2 font-semibold text-foreground">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/20 text-xs text-primary">2</span>
                Selection Rationale
              </h4>
              <div className="border-l-2 border-primary pl-4">
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {evalState.result.rationale}
                </p>
              </div>
            </div>
          )}

          {evalState.result?.gatingDetail && evalState.result.gatingDetail.length > 0 && (
            <div className="rounded-lg border border-border bg-card/50 p-6">
              <h4 className="mb-4 flex items-center gap-2 font-semibold text-foreground">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/20 text-xs text-primary">3</span>
                Gating Strategy
              </h4>
              <div className="relative space-y-4">
                <div className="absolute left-[11px] top-6 bottom-4 w-px bg-border" />
                {evalState.result.gatingDetail.map((step, idx) => (
                  <div key={idx} className="relative flex items-start gap-4">
                    <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary">
                      {idx + 1}
                    </div>
                    <div className="flex-1 space-y-1">
                      {typeof step === "object" && step !== null ? (
                        <>
                          <div className="flex items-center gap-2 text-sm">
                            <span className="text-muted-foreground">Parent:</span>
                            <span className="font-mono font-medium text-foreground">{(step as { parent?: string }).parent ?? "—"}</span>
                          </div>
                          <div className="flex items-center gap-2 text-sm">
                            <span className="text-muted-foreground">Axis:</span>
                            <span className="font-mono text-foreground">{(step as { axis?: string }).axis ?? "—"}</span>
                          </div>
                          <div className="flex items-center gap-2 text-sm">
                            <span className="text-muted-foreground">Gate:</span>
                            <span className="font-mono text-foreground">{(step as { gate?: string }).gate ?? "—"}</span>
                          </div>
                          <div className="flex items-center gap-2 text-sm">
                            <ChevronRight className="h-4 w-4 text-primary" />
                            <span className="font-medium text-primary">{(step as { population?: string }).population ?? "—"}</span>
                          </div>
                        </>
                      ) : (
                        <p className="text-sm text-muted-foreground">{String(step)}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!evalState.result && !evalState.isLoading && !evalState.error && (
            <div className="rounded-lg border border-border bg-card/50 p-6">
              <h4 className="mb-2 font-semibold text-foreground">Recommended Panel</h4>
              <p className="text-sm text-muted-foreground">
                AI evaluation results will appear here, including the recommended
                panel and rationale.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="mb-6 bg-card border border-border">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
              <BarChart3 className="h-4 w-4 text-primary" />
            </div>
            Spectral Visualization
          </CardTitle>
          <CardDescription>
            Interactive spectral simulation for fluorescence overlap analysis
          </CardDescription>
        </CardHeader>
        <CardContent>
          <SpectraChart fluorochromes={selectedFluorochromes} />
        </CardContent>
      </Card>

      <Card className="bg-card border border-border">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
              <AlertTriangle className="h-4 w-4 text-primary" />
            </div>
            Conflict Diagnosis
          </CardTitle>
          <CardDescription>
            Analysis when no valid panel can be found
          </CardDescription>
        </CardHeader>
        <CardContent>
          {genState.diagnosis ? (
            <div className="rounded-lg bg-secondary/30 p-4">
              <h4 className="mb-2 flex items-center gap-2 font-semibold text-foreground">
                <AlertTriangle className="h-4 w-4 text-yellow-400" />
                Diagnosis Report
              </h4>
              <p className="whitespace-pre-wrap font-mono text-sm text-muted-foreground">
                {genState.diagnosis}
              </p>
            </div>
          ) : (
            <div className="rounded-lg bg-secondary/30 p-4">
              <p className="text-sm text-muted-foreground">
                <span className="font-semibold text-foreground">Diagnostic messages</span> will
                appear here if the solver cannot find a valid panel, including
                which markers are competing for the same channels.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function PanelDesignPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
          <CardSkeleton />
        </div>
      }
    >
      <PanelDesignPageContent />
    </Suspense>
  );
}
