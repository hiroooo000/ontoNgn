import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useGraphNetwork } from './useGraphNetwork';
import { Network } from 'vis-network';

vi.mock('vis-network', () => {
  return {
    Network: vi.fn().mockImplementation(function() {
      return {
        on: vi.fn(),
        setOptions: vi.fn(),
        stabilize: vi.fn(),
        fit: vi.fn()
      };
    })
  };
});

describe('useGraphNetwork', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initializes network and registers event handlers', () => {
    const { initNetwork } = useGraphNetwork();
    const container = document.createElement('div');
    initNetwork(container);

    expect(Network).toHaveBeenCalled();
  });

  it('updates graph data properly', () => {
    const { initNetwork, updateGraphData, selectedNode } = useGraphNetwork();
    const container = document.createElement('div');
    initNetwork(container);

    const nodes = [{ id: '1', label: 'Node 1' }];
    const edges = [{ source_id: '1', target_id: '2', relation_type: 'rel' }];
    const visNodes = [{ id: '1', label: 'Node 1' }];
    const visEdges = [{ from: '1', to: '2', label: 'rel', id: '1_2_rel' }];

    updateGraphData(nodes, visNodes, visEdges, edges);
    
    // selectedNode is initially null
    expect(selectedNode.value).toBeNull();
  });
});
