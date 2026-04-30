"use client";

import { useCallback, useEffect, useState } from "react";
import type { Bill, BillsData } from "@/types/bill";
import { BillsTable } from "@/components/bills-table";
import { RefreshButton } from "@/components/refresh-button";
import { Separator } from "@/components/ui/separator";
import { SpendingChart } from "@/components/spending-chart";
import { StatCard } from "@/components/stat-card";

function formatCurrency(n: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(n);
}

function timeAgo(iso: string | null): string {
  if (!iso) return "never";
  const diffMs = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diffMs / 60_000);
  if (m < 1) return "just now";
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  if (h < 24) return `${h}h ago`;
  return `${Math.floor(h / 24)}d ago`;
}

function computeStats(bills: Bill[]) {
  const now = new Date();
  const sevenDays = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);

  const totalDue = bills.reduce((s, b) => s + (b.amount_due ?? 0), 0);
  const dueSoon = bills
    .filter((b) => {
      if (!b.due_date) return false;
      const d = new Date(b.due_date);
      return d >= now && d <= sevenDays;
    })
    .reduce((s, b) => s + (b.amount_due ?? 0), 0);
  const overdueAmounts = bills
    .filter((b) => b.due_date && new Date(b.due_date) < now && b.status !== "paid")
    .reduce((s, b) => s + (b.amount_due ?? 0), 0);
  const overdueCount = bills.filter(
    (b) => b.due_date && new Date(b.due_date) < now && b.status !== "paid",
  ).length;

  return { totalDue, dueSoon, overdueAmounts, overdueCount };
}

export default function DashboardPage() {
  const [data, setData] = useState<BillsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [scraping, setScraping] = useState(false);
  const [notice, setNotice] = useState<{ type: "error" | "info"; text: string } | null>(null);

  const fetchBills = useCallback(async () => {
    try {
      const res = await fetch("/api/bills");
      setData(await res.json());
    } catch {
      setNotice({ type: "error", text: "Could not load bills data." });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchBills();
  }, [fetchBills]);

  const handleRefresh = async () => {
    setScraping(true);
    setNotice(null);
    try {
      const res = await fetch("/api/scrape", { method: "POST" });
      const result = await res.json();

      if (!res.ok) {
        setNotice({ type: "error", text: result.error ?? "Failed to start scraping." });
        setScraping(false);
        return;
      }

      setNotice({ type: "info", text: "Scraping in progress — this may take a few minutes…" });

      const poll = setInterval(async () => {
        try {
          const statusRes = await fetch("/api/status");
          const status = await statusRes.json();
          if (!status.running) {
            clearInterval(poll);
            await fetchBills();
            setScraping(false);
            setNotice(null);
          }
        } catch {
          clearInterval(poll);
          setScraping(false);
        }
      }, 2500);
    } catch {
      setNotice({
        type: "error",
        text: "Python scraper API is not running. Start it with: cd scraper && uvicorn api:app --reload",
      });
      setScraping(false);
    }
  };

  const bills = data?.bills ?? [];
  const { totalDue, dueSoon, overdueAmounts, overdueCount } = computeStats(bills);

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* Header */}
      <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur">
        <div className="container mx-auto flex h-16 items-center justify-between px-4">
          <div>
            <h1 className="text-xl font-bold tracking-tight">Bill Tracker</h1>
            <p className="text-xs text-muted-foreground">
              Last scraped:{" "}
              <span className="font-medium">{timeAgo(data?.last_scraped ?? null)}</span>
            </p>
          </div>
          <RefreshButton onClick={handleRefresh} loading={scraping} />
        </div>
      </header>

      <main className="container mx-auto flex-1 space-y-6 px-4 py-6">
        {/* Notice banner */}
        {notice && (
          <div
            className={`rounded-md border px-4 py-3 text-sm ${
              notice.type === "error"
                ? "border-destructive/50 bg-destructive/10 text-destructive"
                : "border-blue-200 bg-blue-50 text-blue-800"
            }`}
          >
            {notice.text}
          </div>
        )}

        {/* Skeleton while first load */}
        {loading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-28 animate-pulse rounded-xl border bg-muted" />
            ))}
          </div>
        ) : (
          <>
            {/* Stat cards */}
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCard
                title="Total Due"
                value={formatCurrency(totalDue)}
                description={`Across ${bills.length} provider${bills.length !== 1 ? "s" : ""}`}
              />
              <StatCard
                title="Due This Week"
                value={formatCurrency(dueSoon)}
                description="Next 7 days"
              />
              <StatCard
                title="Overdue"
                value={overdueCount > 0 ? formatCurrency(overdueAmounts) : "$0.00"}
                description={
                  overdueCount > 0
                    ? `${overdueCount} bill${overdueCount !== 1 ? "s" : ""} past due`
                    : "All clear"
                }
                highlight={overdueCount > 0}
              />
              <StatCard
                title="Providers Tracked"
                value={String(bills.length)}
                description={
                  bills.filter((b) => b.error).length > 0
                    ? `${bills.filter((b) => b.error).length} with errors`
                    : "All scrapers configured"
                }
              />
            </div>

            {/* Bills table */}
            <section>
              <h2 className="mb-3 text-lg font-semibold">Bills</h2>
              <BillsTable bills={bills} />
            </section>

            <Separator />

            {/* Chart */}
            <section>
              <h2 className="mb-3 text-lg font-semibold">Spending by Category</h2>
              <SpendingChart bills={bills} />
            </section>
          </>
        )}
      </main>
    </div>
  );
}
