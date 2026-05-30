export interface GraphNodeProperty {
  [key: string]: any;
}

export interface GraphNode {
  id: string;
  label: string;
  properties?: GraphNodeProperty;
}

export interface GraphEdge {
  source_id: string;
  target_id: string;
  relation_type: string;
  properties?: GraphNodeProperty;
}

export interface GraphSearchResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface VisNode {
  id: string;
  label: string;
  title?: string;
  color?: {
    background: string;
    border: string;
  };
}

export interface VisEdge {
  id?: string;
  from: string;
  to: string;
  label: string;
  title?: string;
}
