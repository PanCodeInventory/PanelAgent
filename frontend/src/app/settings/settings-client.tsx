"use client";

import { useEffect, useState, type FormEvent } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useSettings } from "@/lib/hooks/use-settings";
import { Settings, AlertCircle, CheckCircle2 } from "lucide-react";

export default function SettingsClientPage() {
  const { state, loadSettings, saveSettings, clearError } = useSettings();

  const [apiBase, setApiBase] = useState("");
  const [modelName, setModelName] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [hasApiKey, setHasApiKey] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    void loadSettings();
  }, [loadSettings]);

  useEffect(() => {
    if (state.settings) {
      setApiBase(state.settings.api_base);
      setModelName(state.settings.model_name);
      setHasApiKey(state.settings.has_api_key);
    }
  }, [state.settings]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    clearError();
    setSuccess(false);

    const data: {
      api_base?: string;
      model_name?: string;
      api_key?: string;
    } = {
      api_base: apiBase,
      model_name: modelName,
    };

    if (apiKey.trim()) {
      data.api_key = apiKey;
    }

    const result = await saveSettings(data);

    if (result) {
      setSuccess(true);
      setApiKey("");
      setHasApiKey(result.has_api_key);
      window.setTimeout(() => setSuccess(false), 3000);
    }
  };

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
          管理 LLM 配置，包括 API 地址、模型名称和 API 密钥。
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

      {success && (
        <div className="mb-6 rounded-lg border border-green-500/50 bg-green-500/10 p-4">
          <div className="flex items-center gap-2 text-green-600">
            <CheckCircle2 className="size-4" />
            <p className="text-sm">设置已保存</p>
          </div>
        </div>
      )}

      <Card className="bg-card border border-border">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg font-semibold text-foreground">
            <div className="flex size-8 items-center justify-center rounded-full bg-primary/10">
              <Settings className="size-4 text-primary" />
            </div>
            LLM 配置
          </CardTitle>
          <CardDescription>
            配置 OpenAI 兼容 API 的连接参数。留空 API 密钥表示不修改已存储的密钥。
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form
            className="flex flex-col gap-6"
            onSubmit={handleSubmit}
            data-testid="settings-form"
          >
            <div className="flex flex-col gap-2">
              <label
                className="text-sm font-medium text-foreground"
                htmlFor="settings-api-base"
              >
                API 地址
              </label>
              <Input
                id="settings-api-base"
                value={apiBase}
                onChange={(event) => setApiBase(event.target.value)}
                placeholder="https://api.openai.com/v1"
                data-testid="settings-api-base"
                className="bg-secondary/50 border-border"
                disabled={state.isLoading}
              />
              <p className="text-xs text-muted-foreground">
                OpenAI 兼容 API 的基础 URL
              </p>
            </div>

            <div className="flex flex-col gap-2">
              <label
                className="text-sm font-medium text-foreground"
                htmlFor="settings-model-name"
              >
                模型名称
              </label>
              <Input
                id="settings-model-name"
                value={modelName}
                onChange={(event) => setModelName(event.target.value)}
                placeholder="gpt-4o"
                data-testid="settings-model-name"
                className="bg-secondary/50 border-border"
                disabled={state.isLoading}
              />
              <p className="text-xs text-muted-foreground">
                要使用的 LLM 模型名称
              </p>
            </div>

            <div className="flex flex-col gap-2">
              <label
                className="text-sm font-medium text-foreground"
                htmlFor="settings-api-key"
              >
                API 密钥
              </label>
              <Input
                id="settings-api-key"
                type="password"
                value={apiKey}
                onChange={(event) => setApiKey(event.target.value)}
                placeholder={hasApiKey ? "••••••••" : "sk-..."}
                data-testid="settings-api-key"
                className="bg-secondary/50 border-border"
                disabled={state.isLoading}
              />
              <p className="text-xs text-muted-foreground">
                {hasApiKey
                  ? "已存储密钥。输入新密钥以替换，留空保持现有密钥。"
                  : "输入 API 密钥以启用 LLM 功能"}
              </p>
            </div>

            <div className="flex justify-end">
              <Button
                type="submit"
                disabled={state.isLoading || state.isSaving}
                data-testid="settings-save-button"
              >
                {state.isSaving ? "保存中..." : "保存设置"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
