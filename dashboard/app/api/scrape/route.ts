import { NextResponse } from "next/server";

const PYTHON_API = process.env.PYTHON_API_URL ?? "http://localhost:8000";

export async function POST(req: Request) {
  try {
    const body = await req.json().catch(() => ({}));
    const provider = (body as { provider?: string }).provider;
    const url = provider ? `${PYTHON_API}/scrape/${provider}` : `${PYTHON_API}/scrape`;

    const res = await fetch(url, { method: "POST" });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch {
    return NextResponse.json(
      {
        error:
          "Python scraper API is not running. " +
          "Start it with: cd scraper && uvicorn api:app --reload",
      },
      { status: 503 },
    );
  }
}
