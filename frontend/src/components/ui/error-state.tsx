import { AlertTriangle } from "lucide-react";
import { Button } from "./button";
import { cn } from "@/lib/utils";

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
  className?: string;
}

function ErrorState({ message, onRetry, className }: ErrorStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-4 rounded-lg border border-destructive/20 bg-destructive/5 p-8 text-center",
        className
      )}
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
        <AlertTriangle className="h-6 w-6 text-destructive" />
      </div>
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-foreground">
          错误
        </h3>
        <p className="max-w-md text-sm text-muted-foreground">
          {message}
        </p>
      </div>
      {onRetry && (
        <Button variant="default" onClick={onRetry} size="sm">
          重试
        </Button>
      )}
    </div>
  );
}

export { ErrorState };
