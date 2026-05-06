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
    const markers = [...recState.markers];
    const markersParam = markers.join(",");
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
          AI 实验设计
        </h1>
        <p className="mt-2 text-muted-foreground">
          描述您的实验，AI将从您的库存中推荐最优标志物组合
        </p>
      </div>

      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
              <Sparkles className="h-4 w-4 text-primary" />
            </div>
            <span>实验配置</span>
          </CardTitle>
          <CardDescription>
            定义您的实验目标和约束条件
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm font-medium leading-none text-foreground">
              <FlaskConical className="h-4 w-4 text-muted-foreground" />
              实验目标
            </label>
            <textarea
              value={expGoal}
              onChange={(e) => setExpGoal(e.target.value)}
              placeholder="例如：分析小鼠黑色素瘤模型中肿瘤浸润淋巴细胞的耗竭状态"
              rows={4}
              className="w-full resize-none rounded-lg border border-border bg-secondary/50 px-3 py-2.5 text-sm text-foreground ring-offset-background transition-colors placeholder:text-muted-foreground focus-visible:border-primary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary/50"
            />
            <p className="text-xs text-muted-foreground">
              描述您想研究的内容 — 细胞类型、条件、生物学问题
            </p>
          </div>

          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm font-medium leading-none text-foreground">
              <Palette className="h-4 w-4 text-muted-foreground" />
              目标颜色数
            </label>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
              <input
                type="range"
                min="1"
                max="30"
                step="1"
                value={numColors}
                onChange={(e) => updateNumColors(Number(e.target.value))}
                aria-label="目标颜色数"
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
                  aria-label="颜色数输入"
                  className="w-full rounded-lg border border-border bg-secondary/50 px-3 py-2 text-center text-sm font-mono text-foreground ring-offset-background transition-colors focus-visible:border-primary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary/50"
                />
                <span className="text-sm text-muted-foreground">色</span>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              您计划使用多少种荧光素（颜色）？
            </p>
          </div>

          <div className="space-y-2">
            <label className="flex items-center gap-2 text-sm font-medium leading-none text-foreground">
              <Dna className="h-4 w-4 text-muted-foreground" />
              物种
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
              选择使用哪种抗体库存
            </p>
          </div>

          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span>当前库存：</span>
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
                    分析中...
                  </>
                ) : (
                  <>
                    <Sparkles data-icon="inline-start" />
                    推荐标志物
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                onClick={handleClear}
                disabled={recState.isLoading}
              >
                <RotateCcw data-icon="inline-start" />
                清空
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
            <span>推荐标志物</span>
          </CardTitle>
          <CardDescription>
            AI精选标志物及选择理由
          </CardDescription>
        </CardHeader>
        <CardContent>
          {recState.isLoading ? (
            <TableSkeleton rows={numColors} columns={3} />
          ) : recState.markersDetail.length === 0 ? (
            <EmptyState
              title="暂无推荐"
              description="AI分析后推荐的标志物将显示在此处。每个标志物将包含其类型（如谱系、功能、活化）和选择理由。"
            />
          ) : (
            <div className="overflow-hidden rounded-lg border border-border">
              <table className="w-full text-sm">
                <thead className="border-b border-border bg-muted/50">
                  <tr>
                    <th className="px-4 py-3 text-left font-medium text-foreground">
                      标志物
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-foreground">
                      类型
                    </th>
                    <th className="px-4 py-3 text-left font-medium text-foreground">
                      理由
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
              <span>使用此方案</span>
            </CardTitle>
            <CardDescription>
              将推荐标志物传递到配色方案生成页面
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-lg border border-border bg-secondary/30 p-4">
              <p className="mb-3 text-sm font-medium text-foreground">
                已选标志物：
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
              满意AI推荐后，将标志物列表传递到配色方案页面以寻找最优荧光素分配方案。
            </p>
            <Button
              variant="default"
              className="w-full"
              onClick={handleUseThisPanel}
            >
              <CheckCircle2 data-icon="inline-start" />
              使用此方案
              <ArrowRight data-icon="inline-end" />
            </Button>
            <p className="text-xs text-muted-foreground">
              此操作将在配色方案页面中填入推荐的标志物。
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
