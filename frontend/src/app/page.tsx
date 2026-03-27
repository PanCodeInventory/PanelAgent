import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export default function Home() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6 lg:px-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
          FlowCyt Panel Assistant
        </h1>
        <p className="mt-4 text-lg text-muted-foreground">
          Hybrid AI tool for multi-color flow cytometry panel design
        </p>
        <p className="mt-2 text-sm text-muted-foreground">
          Combining deterministic algorithms with LLM evaluation to generate
          physically valid panels
        </p>
      </div>

      <div className="mt-12 grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">🧠</span>
              AI Experimental Design
            </CardTitle>
            <CardDescription>
              Let AI recommend the best marker combinations for your experiment
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Describe your experimental goal, and AI will analyze your antibody
              inventory to recommend optimal marker combinations with detailed
              rationale.
            </p>
            <Link href="/exp-design">
              <Button className="w-full">Start Experimental Design</Button>
            </Link>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">🛠️</span>
              Panel Generation
            </CardTitle>
            <CardDescription>
              Generate conflict-free panels from your marker list
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-muted-foreground">
              Enter your target markers and let the backtracking solver find all
              physically valid panel configurations, then have AI evaluate and
              select the best option.
            </p>
            <Link href="/panel-design">
              <Button className="w-full">Generate Panel</Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      <div className="mt-12">
        <h2 className="text-2xl font-semibold text-foreground">
          How It Works
        </h2>
        <div className="mt-6 grid gap-6 sm:grid-cols-3">
          <div className="rounded-lg border bg-card p-6">
            <div className="mb-4 text-3xl">🔍</div>
            <h3 className="font-semibold text-card-foreground">
              Search Phase
            </h3>
            <p className="mt-2 text-sm text-muted-foreground">
              Deterministic backtracking algorithm finds all physically valid
              panel configurations with no channel conflicts.
            </p>
          </div>
          <div className="rounded-lg border bg-card p-6">
            <div className="mb-4 text-3xl">🤖</div>
            <h3 className="font-semibold text-card-foreground">
              AI Evaluation
            </h3>
            <p className="mt-2 text-sm text-muted-foreground">
              LLM expert evaluates candidates based on brightness matching and
              spectral overlap to select the optimal panel.
            </p>
          </div>
          <div className="rounded-lg border bg-card p-6">
            <div className="mb-4 text-3xl">📊</div>
            <h3 className="font-semibold text-card-foreground">
              Visualization
            </h3>
            <p className="mt-2 text-sm text-muted-foreground">
              Interactive spectral simulation and gating strategy generation for
              your final panel selection.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
