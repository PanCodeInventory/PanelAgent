import { cn } from "@/lib/utils";

interface LoadingSkeletonProps {
  className?: string;
}

function LoadingSkeleton({ className }: LoadingSkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-muted/50",
        className
      )}
    />
  );
}

interface TableSkeletonProps {
  rows?: number;
  columns?: number;
  className?: string;
}

function TableSkeleton({
  rows = 5,
  columns = 4,
  className,
}: TableSkeletonProps) {
  return (
    <div className={cn("w-full space-y-3", className)}>
      {/* Table header */}
      <div className="flex gap-4">
        {Array.from({ length: columns }).map((_, colIndex) => (
          <div
            key={`header-${colIndex}`}
            className="h-8 flex-1 animate-pulse rounded bg-muted/60"
          />
        ))}
      </div>
      {/* Table rows */}
      <div className="space-y-2">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={`row-${rowIndex}`} className="flex gap-4">
            {Array.from({ length: columns }).map((_, colIndex) => (
              <div
                key={`cell-${rowIndex}-${colIndex}`}
                className="h-12 flex-1 animate-pulse rounded bg-muted/40"
              />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}

interface CardSkeletonProps {
  className?: string;
  header?: boolean;
  lines?: number;
}

function CardSkeleton({
  className,
  header = true,
  lines = 3,
}: CardSkeletonProps) {
  return (
    <div
      className={cn(
        "space-y-4 rounded-lg border border-border bg-card p-6",
        className
      )}
    >
      {header && (
        <div className="flex items-center justify-between">
          <div className="h-6 w-1/3 animate-pulse rounded bg-muted/60" />
          <div className="h-8 w-20 animate-pulse rounded bg-muted/50" />
        </div>
      )}
      <div className="space-y-3">
        {Array.from({ length: lines }).map((_, index) => (
          <div
            key={`line-${index}`}
            className="h-4 animate-pulse rounded bg-muted/40"
            style={{ width: `${85 + Math.random() * 15}%` }}
          />
        ))}
      </div>
    </div>
  );
}

export { LoadingSkeleton, TableSkeleton, CardSkeleton };
