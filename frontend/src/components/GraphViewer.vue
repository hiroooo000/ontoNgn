<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useGraphNetwork } from '../composables/useGraphNetwork';
import { fetchGraphData } from '../services/graphApi';
import { formatNodes, formatEdges } from '../utils/graphFormatter';

const { initNetwork, updateGraphData, selectedNode } = useGraphNetwork();

const networkContainer = ref<HTMLElement | null>(null);
const searchKeyword = ref('');
const searchHops = ref('1');
const isLoading = ref(false);
const isPanelCollapsed = ref(false);

const togglePanel = () => {
  isPanelCollapsed.value = !isPanelCollapsed.value;
};

const handleSearch = async () => {
  if (!searchKeyword.value.trim()) return;

  isLoading.value = true;
  try {
    const data = await fetchGraphData(searchKeyword.value.trim(), parseInt(searchHops.value));
    const visNodes = formatNodes(data.nodes || []);
    const visEdges = formatEdges(data.edges || []);
    updateGraphData(data.nodes || [], visNodes, visEdges);
  } catch (error: unknown) {
    console.error('Failed to fetch graph data:', error);
    const msg = error instanceof Error ? error.message : String(error);
    alert('データの取得に失敗しました。詳細: ' + msg);
  } finally {
    isLoading.value = false;
  }
};

onMounted(() => {
  if (networkContainer.value) {
    initNetwork(networkContainer.value);
  }
});
</script>

<template>
  <div
    class="font-sans antialiased bg-slate-900 text-slate-50 w-full h-screen overflow-hidden relative"
  >
    <!-- Graph Canvas -->
    <div ref="networkContainer" class="w-full h-screen absolute top-0 left-0 z-0"></div>

    <!-- Toggle Button -->
    <button
      @click="togglePanel"
      class="absolute top-5 z-20 bg-slate-700 hover:bg-slate-600 text-white p-2 rounded-r-md border border-l-0 border-slate-500 shadow-lg flex items-center justify-center transition-all duration-300"
      :style="{ left: isPanelCollapsed ? '0' : '320px' }"
    >
      <svg
        class="w-5 h-5"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          :d="isPanelCollapsed ? 'M9 5l7 7-7 7' : 'M15 19l-7-7 7-7'"
        ></path>
      </svg>
    </button>

    <!-- Left Pane -->
    <div
      class="absolute top-0 left-0 w-[320px] h-full z-10 flex flex-col shadow-2xl transition-transform duration-300 glass-panel"
      :class="{ '-translate-x-full': isPanelCollapsed }"
    >
      <!-- Header / Search Area -->
      <div class="p-5 border-b border-slate-600">
        <h1 class="text-xl font-bold mb-4 text-blue-400 flex items-center">
          <svg
            class="w-6 h-6 mr-2"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13 10V3L4 14h7v7l9-11h-7z"
            ></path>
          </svg>
          Graph Insights
        </h1>

        <form @submit.prevent="handleSearch" class="flex flex-col space-y-3">
          <div>
            <label class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1 block"
              >Search Nodes</label
            >
            <div class="relative">
              <input
                v-model="searchKeyword"
                type="text"
                class="w-full bg-slate-900/50 border border-slate-600 rounded-md py-2 pl-3 pr-10 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 placeholder-slate-500"
                placeholder="Keyword..."
              />
              <div class="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                <svg
                  class="w-4 h-4 text-slate-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  ></path>
                </svg>
              </div>
            </div>
          </div>

          <div class="flex items-center space-x-2">
            <div class="flex-1">
              <label
                class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1 block"
                >Hops</label
              >
              <select
                v-model="searchHops"
                class="w-full bg-slate-900/50 border border-slate-600 rounded-md py-2 px-3 text-sm focus:outline-none focus:border-blue-500"
              >
                <option value="1">1 Hop</option>
                <option value="2">2 Hops</option>
                <option value="3">3 Hops</option>
              </select>
            </div>
            <div class="flex-none pt-5">
              <button
                type="submit"
                class="bg-blue-600 hover:bg-blue-500 text-white font-medium py-2 px-4 rounded-md transition-colors text-sm w-full"
              >
                Search
              </button>
            </div>
          </div>
        </form>
      </div>

      <!-- Properties Area -->
      <div class="flex-1 p-5 overflow-y-auto">
        <h2 class="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
          Selected Node Properties
        </h2>

        <div class="bg-slate-900/40 rounded-md border border-slate-700 p-4 min-h-[200px]">
          <p v-if="!selectedNode" class="text-slate-500 text-sm italic text-center mt-10">
            Click on a node to view its properties.
          </p>

          <div v-else>
            <div class="mb-4 pb-3 border-b border-slate-700">
              <div class="text-xs text-slate-400 mb-1">LABEL</div>
              <div class="text-lg font-bold text-blue-300">
                {{ selectedNode.label || 'Unknown' }}
              </div>
              <div class="text-xs text-slate-400 mt-2 mb-1">ID</div>
              <div class="text-sm font-mono text-slate-300 break-all">{{ selectedNode.id }}</div>
            </div>

            <div class="text-xs text-slate-400 mb-2">PROPERTIES (JSON)</div>
            <pre class="text-xs font-mono text-green-300 overflow-x-auto whitespace-pre-wrap">{{
              JSON.stringify(selectedNode.properties || {}, null, 2)
            }}</pre>
          </div>
        </div>

        <!-- Loading indicator -->
        <div v-if="isLoading" class="mt-4 text-center">
          <svg
            class="animate-spin inline-block w-6 h-6 text-blue-500"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            ></circle>
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          <span class="text-sm text-slate-400 ml-2">Loading graph...</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.glass-panel {
  background: rgba(30, 41, 59, 0.7);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
}
</style>
