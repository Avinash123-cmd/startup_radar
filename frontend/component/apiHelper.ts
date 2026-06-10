export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const cache = new Map<string, { data: any; timestamp: number }>();

export async function fetchWithCache<T = any>(
  url: string,
  options: RequestInit & { forceRefresh?: boolean } = {}
): Promise<T> {
  const { forceRefresh = false, ...fetchOptions } = options;
  const isGet = !fetchOptions.method || fetchOptions.method.toUpperCase() === "GET";

  if (isGet && !forceRefresh) {
    const cached = cache.get(url);
    if (cached && Date.now() - cached.timestamp < 300000) { // 5 minutes TTL
      return cached.data;
    }
  }

  const res = await fetch(url, fetchOptions);
  if (!res.ok) {
    throw new Error(`Request to ${url} failed with status ${res.status}`);
  }

  const contentType = res.headers.get("content-type");
  let data: any = null;
  if (contentType && contentType.includes("application/json")) {
    data = await res.json();
  } else {
    data = await res.text();
  }

  if (isGet) {
    cache.set(url, { data, timestamp: Date.now() });
  } else {
    // Clear cache on mutations (POST, PUT, DELETE, etc.)
    cache.clear();
  }

  return data;
}
