import { NextResponse } from "next/server";

const PYTHON_API = process.env.PYTHON_API_URL ?? "http://localhost:8000";

export async function GET() {
  try {
    const res = await fetch(`${PYTHON_API}/status`, { cache: "no-store" });
    return NextResponse.json(await res.json());
  } catch {
    return NextResponse.json({ running: false, provider: null, error: "Python API unavailable" });
  }
}
