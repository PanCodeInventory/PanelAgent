"use client";

import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { CardSkeleton, TableSkeleton } from "@/components/ui/loading-skeleton";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import { useQualityAdmin } from "@/lib/hooks/use-quality-admin";
import type { QualityIssue, QualityIssueUpdate } from "@/lib/hooks/use-quality-admin";
import {
  CheckCircle2,
  ClipboardList,
  Edit2,
  History,
  Inbox,
  RefreshCw,
  ShieldAlert,
} from "lucide-react";

type TabValue = "all" | "pending" | "review";
type BadgeVariant = "default" | "secondary" | "destructive" | "outline";

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString();
}

function getStatusVariant(status: string): BadgeVariant {
  if (status === "resolved") return "default";
  if (status === "pending_review") return "destructive";
  return "secondary";
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    open: "待处理",
    pending_review: "审核中",
    resolved: "已解决",
  };
  return labels[status] || status;
}

export default function QualityAdminClient() {
  const {
    state,
    clearError,
    getHistory,
    listIssues,
    loadReviewQueue,
    updateIssue,
    resolveReview,
  } = useQualityAdmin();

  const [activeTab, setActiveTab] = useState<TabValue>("all");
  const [selectedIssueId, setSelectedIssueId] = useState<string | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [resolveOpen, setResolveOpen] = useState(false);
  const [reviewerName, setReviewerName] = useState("");
  const [editForm, setEditForm] = useState<QualityIssueUpdate>({
    issue_text: "",
    reported_by: "",
  });

  useEffect(() => {
    void listIssues();
    void loadReviewQueue();
  }, [listIssues, loadReviewQueue]);

  useEffect(() => {
    if (selectedIssueId) {
      void getHistory(selectedIssueId);
    }
  }, [selectedIssueId, getHistory]);

  const handleTabChange = (value: string) => {
    setActiveTab(value as TabValue);
    clearError();
  };

  const handleRowClick = (issue: QualityIssue) => {
    setSelectedIssueId(issue.id);
    setEditForm({
      issue_text: issue.issue_text,
      reported_by: issue.reported_by,
    });
    setDetailOpen(true);
  };

  const handleEditClick = (issue: QualityIssue) => {
    setSelectedIssueId(issue.id);
    setEditForm({
      issue_text: issue.issue_text,
      reported_by: issue.reported_by,
    });
    setEditOpen(true);
  };

  const handleResolveClick = (issueId: string) => {
    setSelectedIssueId(issueId);
    setReviewerName("");
    setResolveOpen(true);
  };

  const handleEditSubmit = async () => {
    if (!selectedIssueId) return;

    const updated = await updateIssue(selectedIssueId, editForm);
    if (updated) {
      setEditOpen(false);
    }
  };

  const handleResolveSubmit = async () => {
    if (!selectedIssueId || !reviewerName.trim()) return;

    const resolved = await resolveReview(selectedIssueId, {
      reviewer: reviewerName.trim(),
    });
    if (resolved) {
      setResolveOpen(false);
      setReviewerName("");
    }
  };

  const filteredIssues = state.issues.filter((issue) => {
    if (activeTab === "pending") return issue.status === "open";
    if (activeTab === "review") return issue.status === "pending_review";
    return true;
  });

  const selectedIssue = state.issues.find((i) => i.id === selectedIssueId);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <ShieldAlert className="w-6 h-6 text-primary" />
          <h2 className="text-2xl font-bold text-foreground">质量管理</h2>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            void listIssues();
            void loadReviewQueue();
          }}
          disabled={state.isLoading}
        >
          <RefreshCw className={cn("w-4 h-4 mr-2", state.isLoading && "animate-spin")} />
          刷新
        </Button>
      </div>

      {state.error && (
        <ErrorState
          message={state.error}
          onRetry={() => {
            void listIssues();
            void loadReviewQueue();
          }}
        />
      )}

      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList className="mb-4">
          <TabsTrigger value="all">
            全部问题
            <Badge variant="secondary" className="ml-2">
              {state.issues.length}
            </Badge>
          </TabsTrigger>
          <TabsTrigger value="pending">
            待处理
          </TabsTrigger>
          <TabsTrigger value="review">
            审核队列
            {state.reviewQueue.length > 0 && (
              <Badge variant="destructive" className="ml-2">
                {state.reviewQueue.length}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4">
          <IssuesTable
            issues={filteredIssues}
            isLoading={state.isLoading}
            onRowClick={handleRowClick}
            onEditClick={handleEditClick}
          />
        </TabsContent>

        <TabsContent value="pending" className="space-y-4">
          <IssuesTable
            issues={filteredIssues}
            isLoading={state.isLoading}
            onRowClick={handleRowClick}
            onEditClick={handleEditClick}
          />
        </TabsContent>

        <TabsContent value="review" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Inbox className="w-5 h-5" />
                待审核问题
              </CardTitle>
              <CardDescription>
                需要管理员审核并分配库存记录的质量问题
              </CardDescription>
            </CardHeader>
            <CardContent>
              {state.isLoading && state.reviewQueue.length === 0 ? (
                <TableSkeleton rows={3} columns={5} />
              ) : state.reviewQueue.length === 0 ? (
                <EmptyState
                  title="审核队列为空"
                  description="当前没有待审核的质量问题。"
                />
              ) : (
                <div className="overflow-hidden rounded-md border border-border">
                  <table className="w-full text-sm">
                    <thead className="border-b border-border bg-secondary/30">
                      <tr>
                        <th className="px-4 py-3 text-left font-medium">标志物</th>
                        <th className="px-4 py-3 text-left font-medium">荧光素</th>
                        <th className="px-4 py-3 text-left font-medium">问题描述</th>
                        <th className="px-4 py-3 text-left font-medium">报告人</th>
                        <th className="px-4 py-3 text-left font-medium">操作</th>
                      </tr>
                    </thead>
                    <tbody>
                      {state.reviewQueue.map((item) => (
                        <tr
                          key={item.id}
                          className="border-b border-border last:border-b-0 hover:bg-secondary/20"
                        >
                          <td className="px-4 py-3 font-medium">
                            {item.feedback_key.normalized_marker}
                          </td>
                          <td className="px-4 py-3">{item.feedback_key.fluorochrome}</td>
                          <td className="px-4 py-3 max-w-xs truncate">
                            {item.issue_text}
                          </td>
                          <td className="px-4 py-3 text-muted-foreground">
                            {item.reported_by}
                          </td>
                          <td className="px-4 py-3">
                            <Button
                              size="sm"
                              onClick={() => handleResolveClick(item.id)}
                            >
                              <CheckCircle2 className="w-4 h-4 mr-1" />
                              解决
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <DetailDialog
        open={detailOpen}
        onOpenChange={setDetailOpen}
        issue={selectedIssue}
        history={state.history}
        isLoading={state.isLoading}
      />

      <EditDialog
        open={editOpen}
        onOpenChange={setEditOpen}
        issue={selectedIssue}
        form={editForm}
        onFormChange={setEditForm}
        onSubmit={handleEditSubmit}
        isLoading={state.isLoading}
      />

      <ResolveDialog
        open={resolveOpen}
        onOpenChange={setResolveOpen}
        reviewerName={reviewerName}
        onReviewerChange={setReviewerName}
        onSubmit={handleResolveSubmit}
        isLoading={state.isLoading}
      />
    </div>
  );
}

interface IssuesTableProps {
  issues: QualityIssue[];
  isLoading: boolean;
  onRowClick: (issue: QualityIssue) => void;
  onEditClick: (issue: QualityIssue) => void;
}

function IssuesTable({ issues, isLoading, onRowClick, onEditClick }: IssuesTableProps) {
  if (isLoading && issues.length === 0) {
    return <TableSkeleton rows={6} columns={6} />;
  }

  if (issues.length === 0) {
    return (
      <EmptyState
        title="暂无质量问题"
        description="当前没有符合条件的质量问题记录。"
      />
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ClipboardList className="w-5 h-5" />
          问题列表
        </CardTitle>
        <CardDescription>
          点击行查看详情，使用编辑按钮修改问题信息
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="overflow-hidden rounded-md border border-border">
          <table className="w-full text-sm">
            <thead className="border-b border-border bg-secondary/30">
              <tr>
                <th className="px-4 py-3 text-left font-medium">标志物</th>
                <th className="px-4 py-3 text-left font-medium">荧光素</th>
                <th className="px-4 py-3 text-left font-medium">品牌</th>
                <th className="px-4 py-3 text-left font-medium">状态</th>
                <th className="px-4 py-3 text-left font-medium">报告人</th>
                <th className="px-4 py-3 text-left font-medium">创建时间</th>
                <th className="px-4 py-3 text-left font-medium">操作</th>
              </tr>
            </thead>
            <tbody>
              {issues.map((issue, idx) => (
                <tr
                  key={issue.id}
                  onClick={() => onRowClick(issue)}
                  className={cn(
                    "border-b border-border last:border-b-0 cursor-pointer hover:bg-secondary/20",
                    idx % 2 === 0 ? "bg-secondary/10" : ""
                  )}
                >
                  <td className="px-4 py-3 font-medium">
                    {issue.feedback_key.normalized_marker}
                  </td>
                  <td className="px-4 py-3">{issue.feedback_key.fluorochrome}</td>
                  <td className="px-4 py-3">{issue.feedback_key.brand}</td>
                  <td className="px-4 py-3">
                    <Badge variant={getStatusVariant(issue.status)}>
                      {getStatusLabel(issue.status)}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {issue.reported_by}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground">
                    {formatDateTime(issue.created_at)}
                  </td>
                  <td className="px-4 py-3">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onEditClick(issue);
                      }}
                    >
                      <Edit2 className="w-4 h-4" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

interface DetailDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  issue: QualityIssue | undefined;
  history: { event_id: string; action: string; actor: string; timestamp: string; details: Record<string, unknown> }[];
  isLoading: boolean;
}

function DetailDialog({ open, onOpenChange, issue, history, isLoading }: DetailDialogProps) {
  const historyEvents = [...history].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-3xl max-h-[80vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle>问题详情</DialogTitle>
          <DialogDescription>
            {issue ? `ID: ${issue.id}` : "加载中..."}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 overflow-y-auto max-h-[60vh] pr-2">
          {issue ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-muted-foreground">标志物</Label>
                  <p className="font-medium">{issue.feedback_key.normalized_marker}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">荧光素</Label>
                  <p className="font-medium">{issue.feedback_key.fluorochrome}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">品牌</Label>
                  <p className="font-medium">{issue.feedback_key.brand}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">状态</Label>
                  <Badge variant={getStatusVariant(issue.status)}>
                    {getStatusLabel(issue.status)}
                  </Badge>
                </div>
              </div>

              <div>
                <Label className="text-muted-foreground">问题描述</Label>
                <p className="mt-1 p-3 bg-secondary/20 rounded-md text-sm">
                  {issue.issue_text}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-muted-foreground">报告人</Label>
                  <p>{issue.reported_by}</p>
                </div>
                <div>
                  <Label className="text-muted-foreground">创建时间</Label>
                  <p>{formatDateTime(issue.created_at)}</p>
                </div>
              </div>
            </div>
          ) : (
            <CardSkeleton lines={4} />
          )}

          <div className="border-t border-border pt-4">
            <h4 className="font-medium flex items-center gap-2 mb-4">
              <History className="w-4 h-4" />
              审核历史
            </h4>

            {isLoading && historyEvents.length === 0 ? (
              <CardSkeleton lines={3} />
            ) : historyEvents.length === 0 ? (
              <p className="text-muted-foreground text-sm">暂无审核记录</p>
            ) : (
              <div className="relative flex flex-col gap-4">
                <div className="absolute left-[11px] top-3 bottom-3 w-px bg-border" />
                {historyEvents.map((event) => (
                  <div
                    key={event.event_id}
                    className="relative flex gap-4 rounded-lg border border-border bg-secondary/10 p-4"
                  >
                    <div className="relative z-10 flex size-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary">
                      {event.action.slice(0, 1).toUpperCase()}
                    </div>
                    <div className="flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-medium">{event.action}</p>
                        <Badge variant="outline">{event.actor}</Badge>
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {formatDateTime(event.timestamp)}
                      </p>
                      {Object.keys(event.details).length > 0 && (
                        <div className="mt-3 flex flex-col gap-2 text-sm">
                          {Object.entries(event.details).map(([key, value]) => (
                            <div
                              key={key}
                              className="rounded-md border border-border bg-card/60 px-3 py-2"
                            >
                              <span className="font-medium">{key}: </span>
                              <span>
                                {typeof value === "string" ? value : JSON.stringify(value)}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            关闭
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

interface EditDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  issue: QualityIssue | undefined;
  form: QualityIssueUpdate;
  onFormChange: (form: QualityIssueUpdate) => void;
  onSubmit: () => void;
  isLoading: boolean;
}

function EditDialog({
  open,
  onOpenChange,
  issue,
  form,
  onFormChange,
  onSubmit,
  isLoading,
}: EditDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>编辑问题</DialogTitle>
          <DialogDescription>
            {issue ? `编辑 ID: ${issue.id}` : "加载中..."}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="edit-issue-text">问题描述</Label>
            <textarea
              id="edit-issue-text"
              value={form.issue_text}
              onChange={(e) =>
                onFormChange({ ...form, issue_text: e.target.value })
              }
              rows={4}
              className="w-full resize-none rounded-lg border border-border bg-secondary/50 px-3 py-2 text-sm"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="edit-reported-by">报告人</Label>
            <Input
              id="edit-reported-by"
              value={form.reported_by}
              onChange={(e) =>
                onFormChange({ ...form, reported_by: e.target.value })
              }
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={onSubmit} disabled={isLoading}>
            {isLoading ? "保存中..." : "保存"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

interface ResolveDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  reviewerName: string;
  onReviewerChange: (name: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
}

function ResolveDialog({
  open,
  onOpenChange,
  reviewerName,
  onReviewerChange,
  onSubmit,
  isLoading,
}: ResolveDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>解决问题</DialogTitle>
          <DialogDescription>
            确认审核并解决此质量问题
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="reviewer-name">审核人姓名</Label>
            <Input
              id="reviewer-name"
              value={reviewerName}
              onChange={(e) => onReviewerChange(e.target.value)}
              placeholder="请输入您的姓名"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button
            onClick={onSubmit}
            disabled={isLoading || !reviewerName.trim()}
          >
            {isLoading ? "处理中..." : "确认解决"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
