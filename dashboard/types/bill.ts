export type BillCategory =
  | "water"
  | "gas"
  | "electric"
  | "trash"
  | "mortgage"
  | "auto"
  | "insurance"
  | "pest"
  | "other";

export type BillStatus = "pending" | "paid" | "overdue" | "unknown";

export interface Bill {
  id: string;
  name: string;
  category: BillCategory;
  amount_due: number | null;
  due_date: string | null;
  last_updated: string;
  status: BillStatus;
  account_number?: string;
  error?: string;
}

export interface BillsData {
  bills: Bill[];
  last_scraped: string | null;
}
