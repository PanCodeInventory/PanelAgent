"use client";

import { useState, useEffect } from "react";
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

type PanelCandidate = components["schemas"]["PanelCandidate"];
type AntibodyInfo = components["schemas"]["AntibodyInfo"];

interface CandidateTableProps {
  candidate: PanelCandidate;
}

function CandidateTable({ candidate }: CandidateTableProps) {
  const entries = Object.entries(candidate).map(([marker, info]) => ({
    marker,
    ...(info as AntibodyInfo),
  }));

  return (
    <div className="rounded-md border">
      <table className="w-full text-sm">
        <thead className="border-b bg-muted/50">
          <tr>
            <th className="px-4 py-2 text-left font-medium">Marker</th>
            <th className="px-4 py-2 text-left font-medium">Fluorochrome</th>
            <th className="px-4 py-2 text-left font-medium">System Code</th>
            <th className="px-4 py-2 text-left font-medium">Brightness</th>
            <th className="px-4 py-2 text-left font-medium">Clone</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry, idx) => (
            <tr key={`${entry.marker}-${idx}`} className="border-b last:border-b-0">
              <td className="px-4 py-2 font-medium">{entry.marker}</td>
              <td className="px-4 py-2">{entry.fluorochrome}</td>
              <td className="px-4 py-2">
                <code className="rounded bg-muted px-1 py-0.5 text-xs">
                  {entry.system_code}
                </code>
              </td>
              <td className="px-4 py-2">
                <div className="flex items-center gap-1">
                  <span className="font-medium">{entry.brightness}</span>
                  <span className="text-muted-foreground">/5</span>
                </div>
              </td>
              <td className="px-4 py-2 text-muted-foreground">
                {entry.clone ?? "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Extract fluorochromes from a candidate panel
function extractFluorochromes(candidate: PanelCandidate): string[] {
  return Object.values(candidate).map((info) => (info as AntibodyInfo).fluorochrome);
}

export default function PanelDesignPage() {
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
    // Clear previous evaluation when searching new panels
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

  // Get fluorochromes for currently selected candidate
  const selectedCandidate = genState.candidates[parseInt(selectedTab.replace("option", "")) || 0];
  const selectedFluorochromes = selectedCandidate ? extractFluorochromes(selectedCandidate) : [];

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          Panel Generation
        </h1>
        <p className="mt-2 text-muted-foreground">
          Generate conflict-free panels from your marker list using backtracking
          search and AI evaluation
        </p>
      </div>

      {/* Marker Input Section */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>📝</span>
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
              className="flex-1"
              disabled={genState.isLoading}
            />
            <select
              value={species}
              onChange={(e) => setSpecies(e.target.value)}
              className="rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
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
                  <span className="mr-2 animate-spin">⏳</span>
                  {genState.isDiagnosing ? "Diagnosing..." : "Searching..."}
                </>
              ) : (
                <>🔍 Search Panels</>
              )}
            </Button>
            <Button variant="outline" onClick={handleClear} disabled={genState.isLoading}>
              Clear
            </Button>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>Current inventory:</span>
            <Badge variant="secondary">{species}</Badge>
          </div>
        </CardContent>
      </Card>

      {/* Error Display */}
      {genState.error && (
        <Card className="mb-8 border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-900/20">
          <CardContent className="pt-6">
            <p className="text-sm text-red-800 dark:text-red-200">
              <span className="font-semibold">Error: </span>
              {genState.error}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Missing Markers */}
      {genState.missingMarkers.length > 0 && (
        <Card className="mb-8 border-yellow-200 bg-yellow-50 dark:border-yellow-900 dark:bg-yellow-900/20">
          <CardHeader>
            <CardTitle className="text-yellow-800 dark:text-yellow-200">
              ⚠️ Missing Markers
            </CardTitle>
            <CardDescription className="text-yellow-700 dark:text-yellow-300">
              The following markers were not found in the inventory
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {genState.missingMarkers.map((marker) => (
                <Badge key={marker} variant="outline" className="border-yellow-500">
                  {marker}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Candidate Panels Section */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>📋</span>
            Candidate Panels
          </CardTitle>
          <CardDescription>
            Physically valid panel configurations (no channel conflicts)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {genState.candidates.length === 0 && !genState.isLoading && !genState.error && (
            <div className="rounded-md border p-8 text-center text-muted-foreground">
              <p className="text-lg font-medium">No candidates yet</p>
              <p className="mt-2 text-sm">
                Enter markers above and click &quot;Search Panels&quot; to generate valid panel configurations
              </p>
            </div>
          )}

          {genState.candidates.length > 0 && (
            <Tabs 
              value={selectedTab} 
              onValueChange={setSelectedTab}
              className="w-full"
            >
              <TabsList className="mb-4">
                {genState.candidates.map((_, idx) => (
                  <TabsTrigger key={idx} value={`option${idx}`}>
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

      {/* AI Evaluation Section */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>🤖</span>
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
                <span className="mr-2 animate-spin">⏳</span>
                Evaluating...
              </>
            ) : (
              <>✨ Evaluate with AI</>
            )}
          </Button>

          {/* Evaluation Error */}
          {evalState.error && (
            <div className="rounded-md border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-900/20">
              <p className="text-sm text-red-800 dark:text-red-200">
                <span className="font-semibold">Error: </span>
                {evalState.error}
              </p>
            </div>
          )}

          {/* Recommended Panel */}
          {evalState.result?.selectedPanel && (
            <div className="rounded-md border p-6">
              <h4 className="mb-4 font-semibold">🏆 Recommended Panel</h4>
              <CandidateTable candidate={evalState.result.selectedPanel} />
            </div>
          )}

          {/* Rationale */}
          {evalState.result?.rationale && (
            <div className="rounded-md border p-6">
              <h4 className="mb-2 font-semibold">💡 Selection Rationale</h4>
              <p className="text-sm text-muted-foreground">
                {evalState.result.rationale}
              </p>
            </div>
          )}

          {/* Gating Strategy */}
          {evalState.result?.gatingDetail && evalState.result.gatingDetail.length > 0 && (
            <div className="rounded-md border p-6">
              <h4 className="mb-2 font-semibold">🚪 Gating Strategy</h4>
              <ul className="list-inside list-disc space-y-1 text-sm text-muted-foreground">
                {evalState.result.gatingDetail.map((step, idx) => (
                  <li key={idx}>
                    {typeof step === "string" 
                      ? step 
                      : JSON.stringify(step)}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Empty evaluation state */}
          {!evalState.result && !evalState.isLoading && !evalState.error && (
            <div className="rounded-md border p-6">
              <h4 className="mb-2 font-semibold">🏆 Recommended Panel</h4>
              <p className="text-sm text-muted-foreground">
                AI evaluation results will appear here, including the recommended
                panel and rationale.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Spectral Visualization Section */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>📊</span>
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

      {/* Diagnosis Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>🔍</span>
            Conflict Diagnosis
          </CardTitle>
          <CardDescription>
            Analysis when no valid panel can be found
          </CardDescription>
        </CardHeader>
        <CardContent>
          {genState.diagnosis ? (
            <div className="rounded-md border border-yellow-200 bg-yellow-50 p-4 dark:border-yellow-900 dark:bg-yellow-900/20">
              <h4 className="mb-2 font-semibold text-yellow-800 dark:text-yellow-200">
                Diagnosis Report
              </h4>
              <p className="whitespace-pre-wrap text-sm text-yellow-800 dark:text-yellow-200">
                {genState.diagnosis}
              </p>
            </div>
          ) : (
            <div className="rounded-md border border-yellow-200 bg-yellow-50 p-4 dark:border-yellow-900 dark:bg-yellow-900/20">
              <p className="text-sm text-yellow-800 dark:text-yellow-200">
                <span className="font-semibold">Diagnostic messages</span> will
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
