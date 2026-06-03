import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { ref } from 'vue';
import GraphViewer from './GraphViewer.vue';
import * as graphApi from '../services/graphApi';

// Mock dependencies
vi.mock('../services/graphApi', () => ({
  fetchGraphData: vi.fn(),
  expandGraphData: vi.fn()
}));

const mockInitNetwork = vi.fn();
const mockUpdateGraphData = vi.fn();
const mockSelectedNode = ref<unknown>(null);
const mockDoubleClickedNode = ref<unknown>(null);
const mockTooltipData = ref<unknown>(null);

vi.mock('../composables/useGraphNetwork', () => ({
  useGraphNetwork: () => ({
    initNetwork: mockInitNetwork,
    updateGraphData: mockUpdateGraphData,
    selectedNode: mockSelectedNode,
    doubleClickedNode: mockDoubleClickedNode,
    tooltipData: mockTooltipData
  })
}));

describe('GraphViewer.vue', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSelectedNode.value = null;
    mockDoubleClickedNode.value = null;
    mockTooltipData.value = null;
  });

  it('mounts correctly and calls initNetwork on mount', () => {
    const wrapper = mount(GraphViewer);
    expect(wrapper.find('div.w-full.h-screen.absolute').exists()).toBe(true);
    expect(mockInitNetwork).toHaveBeenCalled();
  });

  it('toggles panel when button is clicked', async () => {
    const wrapper = mount(GraphViewer);
    const panel = wrapper.find('.glass-panel');
    const button = wrapper.find('button.rounded-r-md');
    
    expect(panel.classes()).not.toContain('-translate-x-full');
    await button.trigger('click');
    expect(panel.classes()).toContain('-translate-x-full');
  });

  it('calls fetchGraphData and updates graph when search form is submitted', async () => {
    const mockData = { nodes: [{ id: '1', label: 'test' }], edges: [], hits: [] };
    vi.spyOn(graphApi, 'fetchGraphData').mockResolvedValue(mockData);
    
    const wrapper = mount(GraphViewer);
    const input = wrapper.find('input[type="text"]');
    await input.setValue('test-keyword');
    await wrapper.find('form').trigger('submit');
    
    expect(graphApi.fetchGraphData).toHaveBeenCalledWith('test-keyword', 1);
    await new Promise(resolve => setTimeout(resolve, 0));
    expect(mockUpdateGraphData).toHaveBeenCalled();
  });

  it('allows selecting up to 10 hops', () => {
    const wrapper = mount(GraphViewer);
    const options = wrapper.findAll('select option');
    expect(options.length).toBe(10);
    expect(options[9].text()).toBe('10 Hops');
  });

  it('displays search hits and expands graph on hit click', async () => {
    const mockData = { nodes: [], edges: [], hits: [{ id: 'hit-1', label: 'Hit Node' }] };
    vi.spyOn(graphApi, 'fetchGraphData').mockResolvedValue(mockData);
    const wrapper = mount(GraphViewer);
    await wrapper.find('input[type="text"]').setValue('test');
    await wrapper.find('form').trigger('submit');
    await new Promise(resolve => setTimeout(resolve, 0)); 
    
    // Check hit list
    const hits = wrapper.findAll('.hit-item');
    expect(hits.length).toBe(1);
    
    // Click hit
    vi.spyOn(graphApi, 'expandGraphData').mockResolvedValue({ nodes: [], edges: [] });
    await hits[0].trigger('click');
    
    expect(graphApi.expandGraphData).toHaveBeenCalledWith('hit-1', 1);
  });

  it('shows tooltip when tooltipData is set', async () => {
    const wrapper = mount(GraphViewer);
    mockTooltipData.value = { visible: true, x: 100, y: 100, data: { label: 'Node1' }, type: 'node' };
    await wrapper.vm.$nextTick();
    const tooltip = wrapper.find('.graph-tooltip');
    expect(tooltip.exists()).toBe(true);
  });

  it('calls expandGraphData when doubleClickedNode changes', async () => {
    vi.spyOn(graphApi, 'expandGraphData').mockResolvedValue({ nodes: [], edges: [] });
    const wrapper = mount(GraphViewer);
    
    mockDoubleClickedNode.value = { id: 'node-2' };
    await wrapper.vm.$nextTick();
    await new Promise(resolve => setTimeout(resolve, 0)); // wait for watch effect
    
    expect(graphApi.expandGraphData).toHaveBeenCalledWith('node-2', 1);
  });
});
