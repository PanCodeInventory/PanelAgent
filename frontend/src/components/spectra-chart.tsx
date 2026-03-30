"use client";

import { useEffect, useState, useMemo } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from "recharts";
import { apiClient } from "@/lib/api-client";
import type { components } from "@/lib/api/generated";
import { Badge } from "@/components/ui/badge";
import { CardSkeleton } from "@/components/ui/loading-skeleton";

type SpectraSeries = components["schemas"]["SpectraSeries"];
type SpectraRenderRequest = components["schemas"]["SpectraRenderRequest"];
type SpectraRenderResponse = components["schemas"]["SpectraRenderResponse"];

interface SpectraChartProps {
  fluorochromes: string[];
}

interface ChartDataPoint {
  wavelength: number;
  [key: string]: number;
}

export function SpectraChart({ fluorochromes }: SpectraChartProps) {
  const [seriesData, setSeriesData] = useState<SpectraSeries[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (fluorochromes.length === 0) {
      setSeriesData([]);
      setWarnings([]);
      setError(null);
      return;
    }

    const fetchSpectraData = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const requestBody: SpectraRenderRequest = {
          fluorochromes: fluorochromes,
        };

        const response = await apiClient.post<SpectraRenderResponse>(
          "/spectra/render-data",
          requestBody
        );

        if (response.error) {
          setError(response.error);
          setSeriesData([]);
          return;
        }

        const data = response.data;

        if (!data) {
          setError("No response from server");
          setSeriesData([]);
          return;
        }

        setSeriesData(data.series ?? []);
        setWarnings(data.warnings ?? []);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error occurred");
        setSeriesData([]);
      } finally {
        setIsLoading(false);
      }
    };

    void fetchSpectraData();
  }, [fluorochromes]);

  const chartData: ChartDataPoint[] = useMemo(() => {
    if (seriesData.length === 0) return [];

    const referenceSeries = seriesData.reduce((longest, series) =>
      series.x.length > longest.x.length ? series : longest
    );

    return referenceSeries.x.map((wavelength, idx) => {
      const point: ChartDataPoint = { wavelength };
      seriesData.forEach((series) => {
        point[series.fluorochrome] = series.y[idx] ?? 0;
      });
      return point;
    });
  }, [seriesData]);

  if (fluorochromes.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-secondary/20 p-8">
        <div className="text-center text-muted-foreground">
          <p className="text-sm">Select a panel candidate to view spectral data</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return <CardSkeleton />;
  }

  if (error) {
    return (
      <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-4">
        <p className="text-sm text-destructive">
          <span className="font-semibold">Error: </span>
          {error}
        </p>
      </div>
    );
  }

  if (seriesData.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-secondary/20 p-8">
        <div className="text-center text-muted-foreground">
          <p className="text-sm">No spectral data available for these fluorochromes</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {warnings.length > 0 && (
        <div className="rounded-lg border p-4" style={{ borderColor: 'var(--warning-border)', backgroundColor: 'var(--warning-bg)' }}>
          <p className="mb-2 text-sm font-medium" style={{ color: 'var(--warning-text)' }}>
            Unknown fluorochromes:
          </p>
          <div className="flex flex-wrap gap-2">
            {warnings.map((warning) => (
              <Badge key={warning} variant="outline" style={{ borderColor: 'var(--warning-border)', color: 'var(--warning-text)' }}>
                {warning}
              </Badge>
            ))}
          </div>
        </div>
      )}

      <div className="h-[400px] w-full rounded-lg border border-border bg-card p-4">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="oklch(0.82 0.01 250 / 40%)"
            />
            <XAxis
              dataKey="wavelength"
              type="number"
              domain={[350, 900]}
              tickCount={12}
              tick={{ fill: "oklch(0.35 0.03 250)", fontSize: 12 }}
              label={{
                value: "Wavelength (nm)",
                position: "insideBottom",
                offset: -10,
                fill: "oklch(0.35 0.03 250)",
                fontSize: 12,
              }}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fill: "oklch(0.35 0.03 250)", fontSize: 12 }}
              label={{
                value: "Normalized Intensity (%)",
                angle: -90,
                position: "insideLeft",
                fill: "oklch(0.35 0.03 250)",
                fontSize: 12,
              }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "oklch(0.995 0.001 75)",
                border: "1px solid oklch(0.85 0.02 250 / 40%)",
                borderRadius: "6px",
                color: "oklch(0.15 0.02 250)",
                boxShadow: "0 2px 8px oklch(0.15 0.02 250 / 8%)",
              }}
              labelStyle={{ color: "oklch(0.15 0.02 250)" }}
              itemStyle={{ color: "oklch(0.35 0.03 250)" }}
              labelFormatter={(value) => `${value} nm`}
            />
            <Legend
              verticalAlign="top"
              height={36}
              wrapperStyle={{ color: "oklch(0.35 0.03 250)" }}
            />
            {seriesData.map((series) => (
              <Line
                key={series.fluorochrome}
                type="monotone"
                dataKey={series.fluorochrome}
                stroke={series.color}
                strokeWidth={2.5}
                dot={false}
                isAnimationActive={false}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
