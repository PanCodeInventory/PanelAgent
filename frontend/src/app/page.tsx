import Link from "next/link";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { BarChart3, Bot, Brain, Search, ShieldAlert, Wrench } from "lucide-react";

export default function Home() {
  return (
    <div className="relative min-h-screen">
      <div className="absolute inset-0 bg-background pointer-events-none" />

      <div className="relative mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
            <span className="text-primary">FlowCyt</span>{" "}
            <span className="text-foreground">Panel Assistant</span>
          </h1>
          <p className="mt-6 text-xl text-muted-foreground max-w-2xl mx-auto">
            Hybrid AI tool for multi-color flow cytometry panel design
          </p>
          <p className="mt-3 text-base text-muted-foreground max-w-xl mx-auto">
            Combining deterministic algorithms with LLM evaluation to generate
            physically valid panels grounded in your real antibody inventory
          </p>
        </div>

        <div className="mt-16 grid gap-6 md:grid-cols-3">
          <Card className="group bg-card border border-border hover:border-primary/20 transition-colors duration-200 rounded-xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Brain className="h-5 w-5" />
                </div>
                <span className="text-foreground">AI Experimental Design</span>
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
              <Link href="/exp-design" className="block">
                <Button 
                  className="w-full transition-all duration-200" 
                  variant="default"
                >
                  Start Experimental Design
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card className="group bg-card border border-border hover:border-primary/20 transition-colors duration-200 rounded-xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <Wrench className="h-5 w-5" />
                </div>
                <span className="text-foreground">Panel Generation</span>
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
              <Link href="/panel-design" className="block">
                <Button 
                  className="w-full transition-all duration-200" 
                  variant="default"
                >
                  Generate Panel
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card className="group bg-card border border-border hover:border-primary/20 transition-colors duration-200 rounded-xl">
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <ShieldAlert className="h-5 w-5" />
                </div>
                <span className="text-foreground">Quality Registry</span>
              </CardTitle>
              <CardDescription>Report antibody quality issues and help improve panel recommendations</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">Submit feedback about antibodies that do not perform well. AI will find matching candidates from your inventory for confirmation.</p>
              <Link href="/quality-registry" className="block">
                <Button className="w-full transition-all duration-200" variant="default">Report Issue</Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        <div className="mt-20">
          <h2 className="text-3xl font-bold text-foreground text-center">
            How It Works
          </h2>
          <p className="mt-3 text-muted-foreground text-center max-w-lg mx-auto">
            A search-then-evaluate architecture combining deterministic rigor with AI intelligence
          </p>
          
          <div className="mt-12 relative">
            <div className="hidden md:block absolute top-12 left-[16.67%] right-[16.67%] h-px bg-border" />
            
            <div className="grid gap-8 sm:grid-cols-3">
              <div className="relative">
                <div className="flex flex-col items-center text-center">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-card border border-border mb-4">
                    <span className="font-mono text-sm text-primary font-semibold">01</span>
                  </div>
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary mb-4">
                    <Search className="h-6 w-6" />
                  </div>
                  <div className="bg-card/50 border border-border rounded-xl p-5 w-full">
                    <h3 className="font-semibold text-card-foreground">
                      Search Phase
                    </h3>
                    <p className="mt-2 text-sm text-muted-foreground">
                      Deterministic backtracking algorithm finds all physically valid
                      panel configurations with no channel conflicts.
                    </p>
                  </div>
                </div>
              </div>

              <div className="relative">
                <div className="flex flex-col items-center text-center">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-card border border-border mb-4">
                    <span className="font-mono text-sm text-primary font-semibold">02</span>
                  </div>
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary mb-4">
                    <Bot className="h-6 w-6" />
                  </div>
                  <div className="bg-card/50 border border-border rounded-xl p-5 w-full">
                    <h3 className="font-semibold text-card-foreground">
                      AI Evaluation
                    </h3>
                    <p className="mt-2 text-sm text-muted-foreground">
                      LLM expert evaluates candidates based on brightness matching and
                      spectral overlap to select the optimal panel.
                    </p>
                  </div>
                </div>
              </div>

              <div className="relative">
                <div className="flex flex-col items-center text-center">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-card border border-border mb-4">
                    <span className="font-mono text-sm text-primary font-semibold">03</span>
                  </div>
                  <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary mb-4">
                    <BarChart3 className="h-6 w-6" />
                  </div>
                  <div className="bg-card/50 border border-border rounded-xl p-5 w-full">
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
          </div>
        </div>
      </div>
    </div>
  );
}
