import { describe, it, expect } from 'vitest';
import { formatNodes, formatEdges } from './graphFormatter';
import type { GraphNode, GraphEdge } from '../types/graph';

describe('graphFormatter', () => {
    describe('formatNodes', () => {
        it('should format a basic node correctly', () => {
            const nodes: GraphNode[] = [{ id: '1', label: 'Person' }];
            const result = formatNodes(nodes);
            
            expect(result).toHaveLength(1);
            expect(result[0].id).toBe('1');
            expect(result[0].label).toBe('Person');
            expect(result[0].color?.background).toBe('#1e3a8a');
        });

        it('should use properties.name as label if available', () => {
            const nodes: GraphNode[] = [{ id: '1', label: 'Person', properties: { name: 'Alice' } }];
            const result = formatNodes(nodes);
            
            expect(result[0].label).toBe('Alice');
        });

        it('should truncate long labels to 20 characters', () => {
            const nodes: GraphNode[] = [{ id: '1', label: 'VeryLongLabelThatExceedsTwentyCharacters' }];
            const result = formatNodes(nodes);
            
            expect(result[0].label).toBe('VeryLongLabelThat...');
        });

        it('should apply specific colors for Document and ap:UnclassifiedConcept', () => {
            const nodes: GraphNode[] = [
                { id: '1', label: 'Document' },
                { id: '2', label: 'ap:UnclassifiedConcept' }
            ];
            const result = formatNodes(nodes);
            
            expect(result[0].color?.background).toBe('#064e3b');
            expect(result[1].color?.background).toBe('#701a75');
        });
    });

    describe('formatEdges', () => {
        it('should format edges correctly', () => {
            const edges: GraphEdge[] = [{ source_id: '1', target_id: '2', relation_type: 'KNOWS' }];
            const result = formatEdges(edges);
            
            expect(result).toHaveLength(1);
            expect(result[0].from).toBe('1');
            expect(result[0].to).toBe('2');
            expect(result[0].label).toBe('KNOWS');
            expect(result[0].title).toBe('KNOWS');
        });
    });
});
