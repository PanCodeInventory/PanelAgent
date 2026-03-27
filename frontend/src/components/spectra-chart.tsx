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
} from "recharts";
import { apiClient } from "@/lib/api-client";
import type { components } from "@/lib/api/generated";
import { Badge } from "@/components/ui/badge";

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

  // Transform series data into chart-friendly format
  const chartData: ChartDataPoint[] = useMemo(() => {
    if (seriesData.length === 0) return [];

    // Find the longest x array to use as reference
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
      <div className="rounded-md border bg-muted/30 p-8">
        <div className="text-center text-muted-foreground">
          <p className="text-sm">Select a panel candidate to view spectral data</p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="rounded-md border bg-muted/30 p-16">
        <div className="text-center text-muted-foreground">
          <p className="text-lg font-medium">Loading spectral data...</p>
          <p className="mt-2 animate-spin text-2xl">⏳</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-900/20">
        <p className="text-sm text-red-800 dark:text-red-200">
          <span className="font-semibold">Error: </span>
          {error}
        </p>
      </div>
    );
  }

  if (seriesData.length === 0) {
    return (
      <div className="rounded-md border bg-muted/30 p-8">
        <div className="text-center text-muted-foreground">
          <p className="text-sm">No spectral data available for these fluorochromes</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Warnings */}
      {warnings.length > 0 && (
        <div className="rounded-md border border-yellow-200 bg-yellow-50 p-4 dark:border-yellow-900 dark:bg-yellow-900/20">
          <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200 mb-2">
            Unknown fluorochromes:
          </p>
          <div className="flex flex-wrap gap-2">
            {warnings.map((warning) => (
              <Badge key={warning} variant="outline" className="border-yellow-500">
                {warning}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Chart */}
      <div className="h-[400px] w-full rounded-md border bg-background p-4">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <XAxis
              dataKey="wavelength"
              type="number"
              domain={[350, 900]}
              tickCount={12}
              label={{ value: "Wavelength (nm)", position: "insideBottom", offset: -10 }}
            />
            <YAxis
              domain={[0, 100]}
              label={{ value: "Normalized Intensity (%)", angle: -90, position: "insideLeft" }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--background))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "6px",
              }}
              labelFormatter={(value) => `${value} nm`}
            />
            <Legend verticalAlign="top" height={36} />
            {seriesData.map((series) => (
              <Line
                key={series.fluorochrome}
                type="monotone"
                dataKey={series.fluorochrome}
                stroke={series.color}
                strokeWidth={2}
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
