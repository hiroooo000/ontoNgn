import { describe, it, expect, vi, beforeEach } from 'vitest';
import { fetchGraphData, expandGraphData } from './graphApi';

describe('graphApi', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('fetches and returns graph data correctly', async () => {
    const mockData = {
      nodes: [{ id: '1', label: 'Test' }],
      edges: [],
      hits: [{ id: '1', label: 'Test' }]
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData)
    } as Response);

    const result = await fetchGraphData('keyword', 2);

    expect(globalThis.fetch).toHaveBeenCalledWith('/api/v1/graph/search?q=keyword&hops=2');
    expect(result).toEqual(mockData);
  });

  it('throws an error when the response is not ok', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404
    } as Response);

    await expect(fetchGraphData('missing', 1)).rejects.toThrow('API error: 404');
  });

  it('fetches and returns expanded graph data correctly', async () => {
    const mockData = {
      nodes: [{ id: 'node_1', label: 'Node 1' }],
      edges: []
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData)
    } as Response);

    const result = await expandGraphData('node_1', 3);

    expect(globalThis.fetch).toHaveBeenCalledWith('/api/v1/graph/expand?node_id=node_1&hops=3');
    expect(result).toEqual(mockData);
  });
});
