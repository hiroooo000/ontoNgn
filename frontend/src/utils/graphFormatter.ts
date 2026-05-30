import type { GraphNode, GraphEdge, VisNode, VisEdge } from '../types/graph';

export function formatNodes(nodes: GraphNode[]): VisNode[] {
    return nodes.map(node => {
        let displayLabel = node.label;
        if (node.properties) {
            if (node.properties.name) displayLabel = String(node.properties.name);
            else if (node.properties.title) displayLabel = String(node.properties.title);
            else if (node.properties.value) displayLabel = String(node.properties.value);
        }
        
        if (displayLabel && displayLabel.length > 20) {
            displayLabel = displayLabel.substring(0, 17) + '...';
        }

        let bgColor = '#1e3a8a';
        let borderColor = '#3b82f6';
        
        if (node.label === 'Document') {
            bgColor = '#064e3b';
            borderColor = '#10b981';
        } else if (node.label === 'ap:UnclassifiedConcept') {
            bgColor = '#701a75';
            borderColor = '#d946ef';
        }

        return {
            id: node.id,
            label: displayLabel,
            title: `${node.label}: ${node.id}`,
            color: {
                background: bgColor,
                border: borderColor
            }
        };
    });
}

export function formatEdges(edges: GraphEdge[]): VisEdge[] {
    return edges.map(edge => ({
        from: edge.source_id,
        to: edge.target_id,
        label: edge.relation_type,
        title: edge.relation_type
    }));
}
