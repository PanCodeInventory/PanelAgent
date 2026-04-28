"use client";

import { useEffect, useState } from "react";
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
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { TableSkeleton } from "@/components/ui/loading-skeleton";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { usePanelHistory } from "@/lib/hooks/use-panel-history";
import type { SelectedAntibody } from "@/lib/hooks/use-panel-history";
import { History, Clock, Database, Beaker, AlertTriangle } from "lucide-react";

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString("zh-CN");
}

function getBrightnessStyle(b: number): React.CSSProperties {
  if (b >= 4) return { backgroundColor: "var(--brightness-high)" };
  if (b >= 3) return { backgroundColor: "var(--brightness-medium)" };
  return { backgroundColor: "var(--brightness-low)" };
}

function PanelTable({ panel }: { panel: SelectedAntibody[] }) {
  return (
    <div className="rounded-md border border-border">
      <table className="w-full text-sm">
        <thead className="border-b border-border bg-secondary/30">
          <tr>
            <th className="px-3 py-2 text-left font-medium text-foreground">标志物</th>
            <th className="px-3 py-2 text-left font-medium text-foreground">荧光素</th>
            <th className="px-3 py-2 text-left font-medium text-foreground">亮度</th>
          </tr>
        </thead>
        <tbody>
          {panel.map((antibody, idx) => (
            <tr
              key={`${antibody.marker}-${idx}`}
              className={cn(
                "border-b border-border last:border-b-0",
                idx % 2 === 0 ? "bg-secondary/10" : ""
              )}
            >
              <td className="px-3 py-2 font-medium text-foreground">{antibody.marker}</td>
              <td className="px-3 py-2 text-foreground">{antibody.fluorochrome}</td>
              <td className="px-3 py-2">
                <div className="flex items-center gap-1">
                  {Array.from({ length: 5 }, (_, i) => (
                    <div
                      key={i}
                      className={cn(
                        "h-1.5 w-1.5 rounded-full",
                        i >= antibody.brightness && "bg-muted-foreground/10"
                      )}
                      style={i < antibody.brightness ? getBrightnessStyle(antibody.brightness) : undefined}
                    />
                  ))}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function HistoryClientPage() {
  const { state, loadHistory, loadDetail, clearError } = usePanelHistory();
  const [detailOpen, setDetailOpen] = useState(false);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  const handleRowClick = async (id: string) => {
    await loadDetail(id);
    setDetailOpen(true);
  };

  const handleCloseDetail = () => {
    setDetailOpen(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <History className="w-6 h-6 text-primary" />
        <h2 className="text-2xl font-bold text-foreground">方案历史</h2>
      </div>

      {state.error && (
        <ErrorState message={state.error} onRetry={loadHistory} />
      )}

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary/10">
              <History className="h-4 w-4 text-primary" />
            </div>
            历史记录
          </CardTitle>
          <CardDescription>
            点击行查看详细信息
          </CardDescription>
        </CardHeader>
        <CardContent>
          {state.isLoading && state.entries.length === 0 ? (
            <TableSkeleton rows={6} columns={4} />
          ) : state.entries.length === 0 ? (
            <EmptyState
              title="暂无历史记录"
              description="配色方案生成后将自动保存到历史记录中"
            />
          ) : (
            <div className="overflow-hidden rounded-md border border-border">
              <table className="w-full text-sm">
                <thead className="border-b border-border bg-secondary/30">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-foreground">时间</th>
                    <th className="px-4 py-3 text-left font-medium text-foreground">物种</th>
                    <th className="px-4 py-3 text-left font-medium text-foreground">标志物数量</th>
                    <th className="px-4 py-3 text-left font-medium text-foreground">模型</th>
                  </tr>
                </thead>
                <tbody>
                  {state.entries.map((entry, idx) => (
                    <tr
                      key={entry.id}
                      onClick={() => void handleRowClick(entry.id)}
                      className={cn(
                        "border-b border-border last:border-b-0 cursor-pointer transition-colors hover:bg-primary/5",
                        idx % 2 === 0 ? "bg-secondary/10" : ""
                      )}
                    >
                      <td className="px-4 py-3 text-foreground">
                        {formatDateTime(entry.created_at)}
                      </td>
                      <td className="px-4 py-3 text-foreground">
                        <Badge variant="secondary">{entry.species}</Badge>
                      </td>
                      <td className="px-4 py-3 text-foreground">
                        <Badge variant="outline">{entry.requested_markers?.length ?? 0}</Badge>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                        {entry.model_name}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Dialog open={detailOpen} onOpenChange={setDetailOpen}>
        <DialogContent className="sm:max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>配色方案详情</DialogTitle>
            <DialogDescription>
              查看完整的配色方案信息
            </DialogDescription>
          </DialogHeader>

          {state.currentDetail && (
            <div className="space-y-6">
              <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  <span>{formatDateTime(state.currentDetail.created_at)}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4" />
                  <span className="font-mono">{state.currentDetail.inventory_file}</span>
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="flex items-center gap-2 text-sm font-medium text-foreground">
                  <Beaker className="h-4 w-4 text-primary" />
                  请求的标志物
                </h4>
                <div className="flex flex-wrap gap-2">
                  {state.currentDetail.requested_markers.map((marker) => (
                    <Badge key={marker} variant="secondary">
                      {marker}
                    </Badge>
                  ))}
                </div>
              </div>

              {state.currentDetail.missing_markers.length > 0 && (
                <div className="space-y-2">
                  <h4 className="flex items-center gap-2 text-sm font-medium text-foreground" style={{ color: 'var(--warning-text)' }}>
                    <AlertTriangle className="h-4 w-4" />
                    缺失的标志物
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {state.currentDetail.missing_markers.map((marker) => (
                      <Badge key={marker} variant="outline" style={{ borderColor: 'var(--warning-border)', color: 'var(--warning-text)' }}>
                        {marker}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              <div className="space-y-2">
                <h4 className="text-sm font-medium text-foreground">最终配色方案</h4>
                <PanelTable panel={state.currentDetail.selected_panel} />
              </div>

              <div className="space-y-2">
                <h4 className="text-sm font-medium text-foreground">选择理由</h4>
                <div className="rounded-lg border border-border bg-secondary/10 p-4">
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {state.currentDetail.rationale}
                  </p>
                </div>
              </div>

              <div className="rounded-lg border border-border bg-secondary/10 p-4 space-y-2">
                <h4 className="text-sm font-medium text-foreground">元数据</h4>
                <div className="grid gap-2 text-sm">
                  <div className="flex gap-2">
                    <span className="text-muted-foreground">模型:</span>
                    <span className="font-mono">{state.currentDetail.model_name}</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-muted-foreground">API:</span>
                    <span className="font-mono text-xs">{state.currentDetail.api_base}</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
