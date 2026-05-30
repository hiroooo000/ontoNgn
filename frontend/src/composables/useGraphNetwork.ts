import { ref, shallowRef } from 'vue';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';
import type { VisNode, VisEdge, GraphNode } from '../types/graph';

export function useGraphNetwork() {
    const networkRef = shallowRef<Network | null>(null);
    const nodesDataset = new DataSet<VisNode>([]);
    const edgesDataset = new DataSet<VisEdge>([]);
    const allGraphNodes = ref<Record<string, GraphNode>>({});
    const selectedNode = ref<GraphNode | null>(null);

    const initNetwork = (container: HTMLElement) => {
        const data = { nodes: nodesDataset, edges: edgesDataset };
        const options = {
            nodes: {
                shape: 'box',
                margin: { top: 8, bottom: 8, left: 12, right: 12 },
                font: { color: '#f8fafc', size: 14, face: 'sans-serif' },
                borderWidth: 2,
                color: {
                    border: '#3b82f6',
                    background: '#1e3a8a',
                    highlight: { border: '#60a5fa', background: '#2563eb' }
                },
                shadow: true
            },
            edges: {
                width: 1.5,
                color: { color: '#475569', highlight: '#94a3b8' },
                font: { color: '#cbd5e1', size: 11, align: 'horizontal', background: '#0f172a', strokeWidth: 0 },
                arrows: { to: {enabled: true, scaleFactor: 0.5} },
                smooth: { enabled: true, type: 'continuous', roundness: 0.5 }
            },
            physics: {
                solver: 'forceAtlas2Based',
                forceAtlas2Based: {
                    gravitationalConstant: -100,
                    centralGravity: 0.01,
                    springLength: 200,
                    springConstant: 0.08,
                    damping: 0.4,
                    avoidOverlap: 1
                },
                maxVelocity: 50,
                timestep: 0.35,
                stabilization: { enabled: true, iterations: 500, updateInterval: 100 }
            },
            interaction: { hover: true, tooltipDelay: 200, zoomView: true, dragView: true }
        };

        networkRef.value = new Network(container, data, options);

        networkRef.value.on("click", (params) => {
            if (params.nodes.length > 0) {
                const nodeId = params.nodes[0];
                selectedNode.value = allGraphNodes.value[nodeId] || null;
            } else {
                selectedNode.value = null;
            }
        });

        networkRef.value.on("stabilized", () => {
            // @ts-ignore
            if (window._needsFit && networkRef.value) {
                networkRef.value.fit({ animation: { duration: 800, easingFunction: 'easeInOutQuad' } });
                // @ts-ignore
                window._needsFit = false;
            }
        });
    };

    const updateGraphData = (nodes: GraphNode[], visNodes: VisNode[], visEdges: VisEdge[]) => {
        const nodeDict: Record<string, GraphNode> = {};
        nodes.forEach(n => nodeDict[n.id] = n);
        allGraphNodes.value = nodeDict;

        if (networkRef.value) networkRef.value.setOptions({ physics: { enabled: false } });
        
        nodesDataset.clear();
        edgesDataset.clear();
        
        nodesDataset.add(visNodes);
        edgesDataset.add(visEdges);
        
        if (networkRef.value) {
            networkRef.value.setOptions({ physics: { enabled: true } });
            networkRef.value.stabilize(500);
        }
        // @ts-ignore
        window._needsFit = true;
    };

    return {
        initNetwork,
        updateGraphData,
        selectedNode
    };
}
