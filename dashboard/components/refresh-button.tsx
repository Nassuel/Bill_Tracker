"use client";

import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface RefreshButtonProps {
  onClick: () => void;
  loading: boolean;
}

export function RefreshButton({ onClick, loading }: RefreshButtonProps) {
  return (
    <Button onClick={onClick} disabled={loading} size="sm">
      <RefreshCw className={loading ? "animate-spin" : ""} />
      {loading ? "Scraping…" : "Refresh All"}
    </Button>
  );
}
