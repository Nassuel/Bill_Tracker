import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Bill, BillStatus } from "@/types/bill";

const CATEGORY_LABELS: Record<string, string> = {
  water: "Water",
  gas: "Gas",
  electric: "Electric",
  trash: "Trash",
  mortgage: "Mortgage",
  auto: "Auto",
  insurance: "Insurance",
  pest: "Pest Control",
  other: "Other",
};

type BadgeVariant = "default" | "secondary" | "destructive" | "outline" | "success" | "warning";

const STATUS_VARIANT: Record<BillStatus, BadgeVariant> = {
  pending: "warning",
  paid: "success",
  overdue: "destructive",
  unknown: "outline",
};

function formatCurrency(n: number | null): string {
  if (n === null || n === undefined) return "—";
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(n);
}

function formatDate(s: string | null): string {
  if (!s) return "—";
  const d = new Date(s);
  if (isNaN(d.getTime())) return s;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function isOverdue(bill: Bill): boolean {
  if (!bill.due_date || bill.status === "paid") return false;
  return new Date(bill.due_date) < new Date();
}

interface BillsTableProps {
  bills: Bill[];
}

export function BillsTable({ bills }: BillsTableProps) {
  if (bills.length === 0) {
    return (
      <div className="rounded-md border p-8 text-center text-sm text-muted-foreground">
        No bills scraped yet. Click <strong>Refresh All</strong> to start.
      </div>
    );
  }

  const sorted = [...bills].sort((a, b) => {
    if (!a.due_date) return 1;
    if (!b.due_date) return -1;
    return new Date(a.due_date).getTime() - new Date(b.due_date).getTime();
  });

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Provider</TableHead>
            <TableHead>Category</TableHead>
            <TableHead className="text-right">Amount Due</TableHead>
            <TableHead>Due Date</TableHead>
            <TableHead>Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {sorted.map((bill) => {
            const effectiveStatus: BillStatus = isOverdue(bill) ? "overdue" : bill.status;
            return (
              <TableRow key={bill.id}>
                <TableCell className="font-medium">
                  {bill.name}
                  {bill.error && (
                    <span
                      className="ml-2 cursor-help text-xs text-destructive underline decoration-dotted"
                      title={bill.error}
                    >
                      error
                    </span>
                  )}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {CATEGORY_LABELS[bill.category] ?? bill.category}
                </TableCell>
                <TableCell className="text-right font-mono">
                  {formatCurrency(bill.amount_due)}
                </TableCell>
                <TableCell>{formatDate(bill.due_date)}</TableCell>
                <TableCell>
                  <Badge variant={STATUS_VARIANT[effectiveStatus] ?? "outline"}>
                    {effectiveStatus}
                  </Badge>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
