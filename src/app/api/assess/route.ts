import { NextRequest } from "next/server";

const BACKEND_URL = process.env.CARTRUST_BACKEND_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const res = await fetch(`${BACKEND_URL}/assess`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(60_000),
    });

    const data = await res.json();

    if (!res.ok) {
      return Response.json(
        { error: data.detail || "Backend error" },
        { status: res.status }
      );
    }

    return Response.json(data);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unexpected error";
    const isTimeout = message.includes("timeout") || message.includes("abort");
    return Response.json(
      { error: isTimeout ? "Assessment timed out — please try again" : message },
      { status: 500 }
    );
  }
}
