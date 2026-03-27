"use client";

import { useState } from "react";
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

export default function PanelDesignPage() {
  const [markers, setMarkers] = useState(
    "CD45.2, CD3, NK1.1, Perforin, Granzyme B, TNF-α, IFN-γ"
  );
  const [species, setSpecies] = useState("Mouse (小鼠)");

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
            />
            <select
              value={species}
              onChange={(e) => setSpecies(e.target.value)}
              className="rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
            >
              <option>Mouse (小鼠)</option>
              <option>Human (人)</option>
            </select>
          </div>
          <div className="flex gap-2">
            <Button>🔍 Search Panels</Button>
            <Button variant="outline">Clear</Button>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>Current inventory:</span>
            <Badge variant="secondary">{species}</Badge>
          </div>
        </CardContent>
      </Card>

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
          <Tabs defaultValue="option1" className="w-full">
            <TabsList className="mb-4">
              <TabsTrigger value="option1">Option 1</TabsTrigger>
              <TabsTrigger value="option2">Option 2</TabsTrigger>
              <TabsTrigger value="option3">Option 3</TabsTrigger>
            </TabsList>
            <TabsContent value="option1">
              <div className="rounded-md border">
                <table className="w-full text-sm">
                  <thead className="border-b bg-muted/50">
                    <tr>
                      <th className="px-4 py-2 text-left font-medium">Marker</th>
                      <th className="px-4 py-2 text-left font-medium">Fluorochrome</th>
                      <th className="px-4 py-2 text-left font-medium">System Code</th>
                      <th className="px-4 py-2 text-left font-medium">Brightness</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b">
                      <td className="px-4 py-2 text-muted-foreground">
                        No candidates generated yet
                      </td>
                      <td className="px-4 py-2"></td>
                      <td className="px-4 py-2"></td>
                      <td className="px-4 py-2"></td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </TabsContent>
            <TabsContent value="option2">
              <div className="rounded-md border p-8 text-center text-muted-foreground">
                Panel configuration will appear here after generation
              </div>
            </TabsContent>
            <TabsContent value="option3">
              <div className="rounded-md border p-8 text-center text-muted-foreground">
                Panel configuration will appear here after generation
              </div>
            </TabsContent>
          </Tabs>
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
          <Button variant="secondary">✨ Evaluate with AI</Button>
          <div className="rounded-md border p-6">
            <h4 className="mb-2 font-semibold">🏆 Recommended Panel</h4>
            <p className="text-sm text-muted-foreground">
              AI evaluation results will appear here, including the recommended
              panel and rationale.
            </p>
          </div>
          <div className="rounded-md border p-6">
            <h4 className="mb-2 font-semibold">🚪 Gating Strategy</h4>
            <p className="text-sm text-muted-foreground">
              Step-by-step gating strategy will be generated by AI for the
              selected panel.
            </p>
          </div>
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
          <div className="rounded-md border bg-muted/30 p-16">
            <div className="text-center text-muted-foreground">
              <p className="text-lg font-medium">Spectral Chart Placeholder</p>
              <p className="mt-2 text-sm">
                Gaussian emission spectra visualization will appear here
              </p>
            </div>
          </div>
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
          <div className="rounded-md border border-yellow-200 bg-yellow-50 p-4 dark:border-yellow-900 dark:bg-yellow-900/20">
            <p className="text-sm text-yellow-800 dark:text-yellow-200">
              <span className="font-semibold">Diagnostic messages</span> will
              appear here if the solver cannot find a valid panel, including
              which markers are competing for the same channels.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
