"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Bill } from "@/types/bill";

const CATEGORY_LABELS: Record<string, string> = {
  water: "Water",
  gas: "Gas",
  electric: "Electric",
  trash: "Trash",
  mortgage: "Mortgage",
  auto: "Auto",
  insurance: "Insurance",
  pest: "Pest",
  other: "Other",
};

interface SpendingChartProps {
  bills: Bill[];
}

export function SpendingChart({ bills }: SpendingChartProps) {
  const data = Object.entries(
    bills.reduce(
      (acc, bill) => {
        const cat = bill.category ?? "other";
        acc[cat] = (acc[cat] ?? 0) + (bill.amount_due ?? 0);
        return acc;
      },
      {} as Record<string, number>,
    ),
  )
    .map(([category, total]) => ({
      name: CATEGORY_LABELS[category] ?? category,
      total,
    }))
    .filter((d) => d.total > 0)
    .sort((a, b) => b.total - a.total);

  if (data.length === 0) {
    return (
      <div className="rounded-md border p-8 text-center text-sm text-muted-foreground">
        No spending data to display yet.
      </div>
    );
  }

  return (
    <div className="rounded-md border p-4">
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={data} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-border" />
          <XAxis
            dataKey="name"
            tickLine={false}
            axisLine={false}
            tick={{ fontSize: 12 }}
          />
          <YAxis
            tickFormatter={(v: number) => `$${v}`}
            tickLine={false}
            axisLine={false}
            tick={{ fontSize: 12 }}
            width={60}
          />
          <Tooltip
            formatter={(value: number) =>
              new Intl.NumberFormat("en-US", {
                style: "currency",
                currency: "USD",
              }).format(value)
            }
            cursor={{ fill: "hsl(var(--muted))" }}
          />
          <Bar
            dataKey="total"
            fill="hsl(var(--primary))"
            radius={[4, 4, 0, 0]}
            maxBarSize={60}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
