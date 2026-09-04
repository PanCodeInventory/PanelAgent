"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useSettings } from "@/lib/hooks/use-settings";
import { settingsApi, type ProviderPreset } from "@/lib/api/settings";
import { Settings, AlertCircle, Info } from "lucide-react";

function ReadOnlyField({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-sm font-medium text-foreground">{label}</span>
      <div className="rounded-md border border-border bg-secondary/50 px-3 py-2 text-sm text-foreground">
        {value}
      </div>
    </div>
  );
}

export default function SettingsClientPage() {
  const { state, loadSettings } = useSettings();

  const [providers, setProviders] = useState<ProviderPreset[]>([]);

  useEffect(() => {
    void loadSettings();
    settingsApi.getProviders().then((res) => {
      if (res.data) setProviders(res.data);
    });
  }, [loadSettings]);

  const providerLabel = useMemo(() => {
    const id = state.settings?.provider ?? "custom";
    return (
      providers.find((p) => p.id === id)?.label ??
      (id === "custom" ? "自定义" : id)
    );
  }, [providers, state.settings]);

  const apiKeyStatus = state.settings
    ? state.settings.has_api_key
      ? "已配置"
      : "未配置"
    : "";

  return (
    <div
      className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8"
      data-testid="settings-page"
    >
      <div className="mb-6">
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          设置
        </h1>
        <p className="mt-2 text-muted-foreground">
          当前生效的 LLM 配置（只读）。
        </p>
      </div>

      {state.error && (
        <div className="mb-6 rounded-lg border border-destructive/50 bg-destructive/10 p-4">
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="size-4" />
            <p className="text-sm">{state.error}</p>
          </div>
        </div>
      )}

      <div className="mb-6 flex items-start gap-2 rounded-lg border border-border bg-muted/40 p-4">
        <Info className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">
          LLM 设置由宿主机 <code className="font-mono">config/.env</code>{" "}
          配置，重启容器后生效，此处仅作展示。
        </p>
      </div>

      <Card className="bg-card border border-border">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <div className="flex size-8 items-center justify-center rounded-full bg-primary/10">
              <Settings className="size-4 text-primary" />
            </div>
            LLM 配置
          </CardTitle>
          <CardDescription>
            当前生效配置，来自宿主机环境变量，不可在本页面修改。
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className="flex flex-col gap-6"
            data-testid="settings-view"
          >
            <ReadOnlyField label="模型供应商" value={providerLabel} />
            <ReadOnlyField
              label="API 地址"
              value={state.settings?.api_base ?? "—"}
            />
            <ReadOnlyField
              label="模型名称"
              value={state.settings?.model_name ?? "—"}
            />
            <ReadOnlyField label="API 密钥" value={apiKeyStatus} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
