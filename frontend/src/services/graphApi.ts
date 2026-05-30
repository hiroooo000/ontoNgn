import type { GraphSearchResponse } from '../types/graph';

export async function fetchGraphData(keyword: string, hops: number): Promise<GraphSearchResponse> {
  const url = `/api/v1/graph/search?q=${encodeURIComponent(keyword)}&hops=${hops}`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }

  return (await response.json()) as GraphSearchResponse;
}
