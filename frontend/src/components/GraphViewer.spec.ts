import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import GraphViewer from './GraphViewer.vue';
import * as graphApi from '../services/graphApi';

// Mock dependencies
vi.mock('../services/graphApi', () => ({
  fetchGraphData: vi.fn()
}));

const mockInitNetwork = vi.fn();
const mockUpdateGraphData = vi.fn();
const mockSelectedNode = { value: null };

vi.mock('../composables/useGraphNetwork', () => ({
  useGraphNetwork: () => ({
    initNetwork: mockInitNetwork,
    updateGraphData: mockUpdateGraphData,
    selectedNode: mockSelectedNode
  })
}));

describe('GraphViewer.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('mounts correctly and calls initNetwork on mount', () => {
    const wrapper = mount(GraphViewer);
    
    // Verify container is rendered
    expect(wrapper.find('div.w-full.h-screen.absolute').exists()).toBe(true);
    
    // Verify initNetwork was called
    expect(mockInitNetwork).toHaveBeenCalled();
  });

  it('toggles panel when button is clicked', async () => {
    const wrapper = mount(GraphViewer);
    
    const panel = wrapper.find('.glass-panel');
    const button = wrapper.find('button');
    
    // Initially not collapsed
    expect(panel.classes()).not.toContain('-translate-x-full');
    
    // Click button
    await button.trigger('click');
    
    // Should be collapsed
    expect(panel.classes()).toContain('-translate-x-full');
  });

  it('calls fetchGraphData and updates graph when search form is submitted', async () => {
    // Mock API response
    const mockData = { nodes: [{ id: '1', label: 'test' }], edges: [] };
    vi.spyOn(graphApi, 'fetchGraphData').mockResolvedValue(mockData);
    
    const wrapper = mount(GraphViewer);
    
    // Set search keyword
    const input = wrapper.find('input[type="text"]');
    await input.setValue('test-keyword');
    
    // Submit form
    await wrapper.find('form').trigger('submit');
    
    expect(graphApi.fetchGraphData).toHaveBeenCalledWith('test-keyword', 1);
    
    // Fast forward promises
    await new Promise(resolve => setTimeout(resolve, 0));
    
    expect(mockUpdateGraphData).toHaveBeenCalled();
  });
});
