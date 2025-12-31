import { create } from 'zustand';

const useStore = create((set) => ({
  // Galaxy data
  nodes: [],
  edges: [],
  loading: true,

  // Dual-view data
  dualNodes: [],
  dualMetadata: null,
  isDualView: false,
  viewMode: 'hybrid', // 'human', 'ai', or 'hybrid'
  topologyMode: 'sphere', // 'sphere' or 'organic'
  layoutMode: 'graph', // 'graph' or 'manifold'

  // Selected node
  selectedNode: null,
  selectedNodeData: null,

  // Search
  searchQuery: '',

  // Actions
  setGalaxyData: (nodes, edges) => set({ nodes, edges, loading: false }),
  setDualGalaxyData: (dualData) => set({
    dualNodes: dualData.nodes,
    dualMetadata: dualData.metadata,
    loading: false
  }),
  toggleDualView: () => set((state) => ({
    isDualView: !state.isDualView,
    selectedNode: null,
    selectedNodeData: null
  })),
  setViewMode: (mode) => set({ viewMode: mode }),
  setTopologyMode: (mode) => set({
    topologyMode: mode,
    selectedNode: null,
    selectedNodeData: null
  }),
  setLayoutMode: (mode) => set({
    layoutMode: mode,
    selectedNode: null,
    selectedNodeData: null,
    loading: true
  }),
  selectNode: (node) => set({ selectedNode: node }),
  setSelectedNode: (node) => set({ selectedNode: node }),
  setSelectedNodeData: (data) => set({ selectedNodeData: data }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  clearSelection: () => set({ selectedNode: null, selectedNodeData: null }),
}));

export default useStore;
