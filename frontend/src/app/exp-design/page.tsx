"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  FlaskConical,
  Palette,
  Dna,
  Sparkles,
  ArrowRight,
  RotateCcw,
  Lightbulb,
  CheckCircle2,
  Rocket,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  LoadingSkeleton,
  TableSkeleton,
} from "@/components/ui/loading-skeleton";
import { ErrorState } from "@/components/ui/error-state";
import { EmptyState } from "@/components/ui/empty-state";
import { useMarkerRecommendation } from "@/lib/hooks/use-marker-recommendation";
import { cn } from "@/lib/utils";

interface MarkerDetail {
  marker: string;
  type: string;
  reason: string;
}

function getTypeBadgeStyle(type: string): React.CSSProperties {
  const normalizedType = type.toLowerCase();
  if (normalizedType.includes("lineage")) {
    return { backgroundColor: 'var(--badge-lineage-bg)', color: 'var(--badge-lineage-text)', borderColor: 'var(--badge-lineage-border)' };
  }
  if (normalizedType.includes("activation")) {
    return { backgroundColor: 'var(--badge-activation-bg)', color: 'var(--badge-activation-text)', borderColor: 'var(--badge-activation-border)' };
  }
  if (normalizedType.includes("exhaustion")) {
    return { backgroundColor: 'var(--badge-exhaustion-bg)', color: 'var(--badge-exhaustion-text)', borderColor: 'var(--badge-exhaustion-border)' };
  }
  if (normalizedType.includes("functional")) {
    return { backgroundColor: 'var(--badge-functional-bg)', color: 'var(--badge-functional-text)', borderColor: 'var(--badge-functional-border)' };
  }
  return {};
}

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

  const { state: recState, recommend, clear: clearRecommendations } =
    useMarkerRecommendation();

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
        <h1 className="font-heading text-3xl font-bold tracking-tight text-foreground">
          AI Experimental Design
        </h1>
        <p className="mt-2 text-muted-foreground">
          Describe your experiment, and AI will recommend the optimal marker
          combination from your inventory
        </p>
      </div>

      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
              <Sparkles className="h-4 w-4 text-primary" />
            </div>
            <span>Experiment Configuration</span>
          </CardTitle>
          <CardDescription>
            Define your experimental goals and constraints
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm font-medium leading-none text-foreground">
              <FlaskConical className="h-4 w-4 text-muted-foreground" />
              Experimental Goal
            </label>
            <textarea
              value={expGoal}
              onChange={(e) => setExpGoal(e.target.value)}
              placeholder="e.g., Analyze tumor-infiltrating lymphocyte exhaustion status in mouse melanoma model"
              rows={4}
              className="w-full resize-none rounded-lg border border-border bg-secondary/50 px-3 py-2.5 text-sm text-foreground ring-offset-background transition-colors placeholder:text-muted-foreground focus-visible:border-primary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary/50"
            />
            <p className="text-xs text-muted-foreground">
              Describe what you want to study — cell types, conditions, biological
              questions
            </p>
          </div>

          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm font-medium leading-none text-foreground">
              <Palette className="h-4 w-4 text-muted-foreground" />
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
                className="w-full flex-1 accent-primary"
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
                  className="w-full rounded-lg border border-border bg-secondary/50 px-3 py-2 text-center text-sm font-mono text-foreground ring-offset-background transition-colors focus-visible:border-primary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary/50"
                />
                <span className="text-sm text-muted-foreground">colors</span>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              How many fluorochromes (colors) do you plan to use?
            </p>
          </div>

          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm font-medium leading-none text-foreground">
              <Dna className="h-4 w-4 text-muted-foreground" />
              Species
            </label>
            <select
              value={species}
              onChange={(e) => setSpecies(e.target.value)}
              className="w-full rounded-lg border border-border bg-secondary/50 px-3 py-2.5 text-sm font-mono text-foreground ring-offset-background transition-colors focus-visible:border-primary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary/50"
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

          <div className="flex gap-3 pt-2">
            <Button
              className="flex-1"
              size="lg"
              onClick={handleRecommend}
              disabled={recState.isLoading || !expGoal.trim()}
            >
              {recState.isLoading ? (
                <>
                  <LoadingSkeleton className="mr-2 h-4 w-4 rounded-full" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Sparkles data-icon="inline-start" />
                  Recommend Markers
                </>
              )}
            </Button>
            <Button
              variant="outline"
              onClick={handleClear}
              disabled={recState.isLoading}
            >
              <RotateCcw data-icon="inline-start" />
              Clear
            </Button>
          </div>
        </CardContent>
      </Card>

      {recState.error && (
        <div className="mb-8">
          <ErrorState message={recState.error} onRetry={handleRecommend} />
        </div>
      )}

      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
              <Lightbulb className="h-4 w-4 text-primary" />
            </div>
            <span>Recommended Markers</span>
          </CardTitle>
          <CardDescription>
            AI-selected markers with design rationale
          </CardDescription>
        </CardHeader>
        <CardContent>
          {recState.isLoading ? (
            <TableSkeleton rows={numColors} columns={3} />
          ) : recState.markersDetail.length === 0 ? (
            <EmptyState
              title="No recommendations yet"
              description="Recommended markers will appear here after AI analysis. Each marker will include its type (e.g., lineage, functional, activation) and selection rationale."
            />
          ) : (
            <div className="overflow-hidden rounded-lg border border-border">
              <table className="w-full text-sm">
                <thead className="border-b border-border bg-muted/50">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-foreground">
                      Marker
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-foreground">
                      Type
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-foreground">
                      Rationale
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {recState.markersDetail.map((detail: MarkerDetail, idx: number) => (
                    <tr
                      key={idx}
                      className={cn(
                        "border-b border-border last:border-b-0",
                        idx % 2 === 1 && "bg-secondary/30"
                      )}
                    >
                      <td className="px-4 py-3 font-mono font-medium text-foreground">
                        {detail.marker}
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          variant="outline"
                          style={getTypeBadgeStyle(detail.type)}
                        >
                          {detail.type}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground">
                        {detail.reason}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {recState.markers.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                <Rocket className="h-4 w-4 text-primary" />
              </div>
              <span>Use This Panel</span>
            </CardTitle>
            <CardDescription>
              Transfer recommended markers to Panel Generation
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-lg border border-border bg-secondary/30 p-4">
              <p className="mb-3 text-sm font-medium text-foreground">
                Selected Markers:
              </p>
              <div className="flex flex-wrap gap-2">
                {recState.markers.map((marker: string) => (
                  <Badge
                    key={marker}
                    variant="outline"
                    className="border-primary/30 bg-primary/5 font-mono text-primary"
                  >
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
              variant="default"
              className="w-full"
              onClick={handleUseThisPanel}
            >
              <CheckCircle2 data-icon="inline-start" />
              Use This Panel
              <ArrowRight data-icon="inline-end" />
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
