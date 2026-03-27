"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useMarkerRecommendation } from "@/lib/hooks/use-marker-recommendation";

export default function ExpDesignPage() {
  const [expGoal, setExpGoal] = useState("");
  const [numColors, setNumColors] = useState(8);
  const [species, setSpecies] = useState("Mouse (小鼠)");
  const router = useRouter();

  const updateNumColors = (value: number) => {
    if (Number.isNaN(value)) {
      return;
    }

    setNumColors(Math.min(30, Math.max(1, value)));
  };

  const { state: recState, recommend, clear: clearRecommendations } = useMarkerRecommendation();

  const handleRecommend = async () => {
    if (!expGoal.trim()) return;
    await recommend(expGoal, numColors, species);
  };

  const handleUseThisPanel = () => {
    if (recState.markers.length === 0) return;
    const markersParam = recState.markers.join(",");
    router.push(`/panel-design?markers=${encodeURIComponent(markersParam)}`);
  };

  const handleClear = () => {
    setExpGoal("");
    setNumColors(8);
    clearRecommendations();
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          AI Experimental Design
        </h1>
        <p className="mt-2 text-muted-foreground">
          Describe your experiment, and AI will recommend the optimal marker
          combination from your inventory
        </p>
      </div>

      {/* Input Section */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>📝</span>
            Experiment Configuration
          </CardTitle>
          <CardDescription>
            Define your experimental goals and constraints
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Research Goal Input */}
          <div className="space-y-2">
            <label className="text-sm font-medium leading-none">
              Experimental Goal
            </label>
            <textarea
              value={expGoal}
              onChange={(e) => setExpGoal(e.target.value)}
              placeholder="e.g., Analyze tumor-infiltrating lymphocyte exhaustion status in mouse melanoma model"
              rows={4}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
            <p className="text-xs text-muted-foreground">
              Describe what you want to study — cell types, conditions, biological
              questions
            </p>
          </div>

          {/* Number of Colors */}
          <div className="space-y-2">
              <label className="text-sm font-medium leading-none">
                Target Number of Colors
              </label>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <input
                type="range"
                min="1"
                max="30"
                step="1"
                value={numColors}
                onChange={(e) => updateNumColors(Number(e.target.value))}
                aria-label="Target Number of Colors"
                className="w-full flex-1 accent-foreground"
              />
              <div className="flex items-center gap-2 sm:w-32">
                <input
                  type="number"
                  min="1"
                  max="30"
                  step="1"
                  value={numColors}
                  onChange={(e) => updateNumColors(Number(e.target.value))}
                  aria-label="Number of colors input"
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-center text-sm font-mono ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                />
                <span className="text-sm text-muted-foreground">colors</span>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              How many fluorochromes (colors) do you plan to use?
            </p>
          </div>

          {/* Species Selector */}
          <div className="space-y-2">
            <label className="text-sm font-medium leading-none">Species</label>
            <select
              value={species}
              onChange={(e) => setSpecies(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
            >
              <option>Mouse (小鼠)</option>
              <option>Human (人)</option>
            </select>
            <p className="text-xs text-muted-foreground">
              Select which antibody inventory to use
            </p>
          </div>

          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>Current inventory:</span>
            <Badge variant="secondary">{species}</Badge>
          </div>

          <div className="flex gap-2">
            <Button 
              className="flex-1" 
              size="lg"
              onClick={handleRecommend}
              disabled={recState.isLoading || !expGoal.trim()}
            >
              {recState.isLoading ? (
                <>
                  <span className="mr-2 animate-spin">⏳</span>
                  Analyzing...
                </>
              ) : (
                <>
                  <span className="mr-2">🤖</span>
                  Recommend Markers
                </>
              )}
            </Button>
            <Button variant="outline" onClick={handleClear} disabled={recState.isLoading}>
              Clear
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Error Display */}
      {recState.error && (
        <Card className="mb-8 border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-900/20">
          <CardContent className="pt-6">
            <p className="text-sm text-red-800 dark:text-red-200">
              <span className="font-semibold">Error: </span>
              {recState.error}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Recommended Markers Section */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <span>💡</span>
            Recommended Markers
          </CardTitle>
          <CardDescription>
            AI-selected markers with design rationale
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <table className="w-full text-sm">
              <thead className="border-b bg-muted/50">
                <tr>
                  <th className="px-4 py-2 text-left font-medium">Marker</th>
                  <th className="px-4 py-2 text-left font-medium">Type</th>
                  <th className="px-4 py-2 text-left font-medium">Rationale</th>
                </tr>
              </thead>
              <tbody>
                {recState.markersDetail.length === 0 && !recState.isLoading && (
                  <tr className="border-b">
                    <td
                      colSpan={3}
                      className="px-4 py-8 text-center text-muted-foreground"
                    >
                      <p className="text-sm">
                        Recommended markers will appear here after AI analysis
                      </p>
                      <p className="mt-1 text-xs">
                        Each marker will include its type (e.g., lineage, functional,
                        activation) and selection rationale
                      </p>
                    </td>
                  </tr>
                )}
                {recState.markersDetail.map((detail, idx) => (
                  <tr key={idx} className="border-b last:border-b-0">
                    <td className="px-4 py-2 font-medium">{detail.marker}</td>
                    <td className="px-4 py-2">
                      <Badge variant="outline">{detail.type}</Badge>
                    </td>
                    <td className="px-4 py-2 text-muted-foreground">{detail.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Action Section */}
      {recState.markers.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span>🚀</span>
              Use This Panel
            </CardTitle>
            <CardDescription>
              Transfer recommended markers to Panel Generation
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-md border bg-muted/50 p-4">
              <p className="text-sm font-medium mb-2">Selected Markers:</p>
              <div className="flex flex-wrap gap-2">
                {recState.markers.map((marker) => (
                  <Badge key={marker} variant="secondary">
                    {marker}
                  </Badge>
                ))}
              </div>
            </div>
            <p className="text-sm text-muted-foreground">
              Once you are satisfied with the AI recommendations, transfer the marker
              list to the Panel Generation page to find optimal fluorochrome
              assignments.
            </p>
            <Button 
              variant="secondary" 
              className="w-full"
              onClick={handleUseThisPanel}
            >
              <span className="mr-2">✅</span>
              Use This Panel
            </Button>
            <p className="text-xs text-muted-foreground">
              This will populate the marker input in the Panel Generation page with
              the recommended markers.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
