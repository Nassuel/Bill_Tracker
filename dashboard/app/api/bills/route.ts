import { NextResponse } from "next/server";
import { readFile } from "fs/promises";
import path from "path";

const DATA_FILE = process.env.DATA_FILE_PATH
  ? path.resolve(process.env.DATA_FILE_PATH)
  : path.join(process.cwd(), "..", "data", "bills.json");

export async function GET() {
  try {
    const content = await readFile(DATA_FILE, "utf-8");
    return NextResponse.json(JSON.parse(content));
  } catch {
    return NextResponse.json({ bills: [], last_scraped: null });
  }
}
