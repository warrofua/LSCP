import { useState } from 'react';
import useStore from '../store';

export default function Interface() {
  const {
    searchQuery,
    setSearchQuery,
    selectNode,
    setSelectedNodeData,
    nodes,
    dualNodes,
    isDualView,
    toggleDualView,
    viewMode,
    setViewMode,
    topologyMode,
    setTopologyMode,
    layoutMode,
    setLayoutMode
  } = useStore();
  const [results, setResults] = useState([]);
  const [showResults, setShowResults] = useState(false);

  const handleSearch = (e) => {
    const query = e.target.value;
    setSearchQuery(query);

    if (query.length > 0) {
      // Use dualNodes in dual view, nodes in single view
      const searchNodes = isDualView ? dualNodes : nodes;
      const filtered = searchNodes.filter((n) =>
        n.name.toLowerCase().includes(query.toLowerCase())
      );
      setResults(filtered.slice(0, 5));
      setShowResults(true);
    } else {
      setResults([]);
      setShowResults(false);
    }
  };

  const handleSelectResult = async (node) => {
    selectNode(node);
    setShowResults(false);
    setSearchQuery('');

    // Fetch node details
    try {
      const res = await fetch(`http://localhost:8001/api/node/${node.name}`);
      const data = await res.json();
      setSelectedNodeData(data);
    } catch (err) {
      console.error('Failed to load node:', err);
    }
  };

  return (
    <div className="absolute top-0 left-0 right-0 p-6 pointer-events-none z-40">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-cyber-blue glow-blue">
            LSCP VIEWER
          </h1>
          <p className="text-xs text-cyber-dim">
            Latent Space Cartography Protocol
          </p>
        </div>

        <div className="text-right text-xs text-cyber-dim">
          <div>NODES: {nodes.length}</div>
          <div>SYSTEM: ONLINE</div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="max-w-md mx-auto relative pointer-events-auto">
        <input
          type="text"
          value={searchQuery}
          onChange={handleSearch}
          placeholder="Search concepts..."
          className="w-full px-4 py-2 bg-cyber-panel/90 border border-cyber-border text-cyber-text rounded focus:outline-none focus:border-cyber-blue transition-colors"
        />

        {/* Search Results */}
        {showResults && results.length > 0 && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-cyber-panel/95 border border-cyber-border rounded overflow-hidden">
            {results.map((node) => (
              <div
                key={node.id}
                onClick={() => handleSelectResult(node)}
                className="px-4 py-2 hover:bg-cyber-blue/20 cursor-pointer transition-colors border-b border-cyber-border last:border-b-0"
              >
                <div className="text-sm text-cyber-text">{node.name}</div>
                <div className="text-xs text-cyber-dim">
                  Distance: {node.avgDistance.toFixed(3)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* View Mode Controls */}
      <div className="max-w-md mx-auto mt-4 pointer-events-auto">
        <div className="flex items-center justify-center gap-2">
          {/* Dual View Toggle */}
          <button
            onClick={toggleDualView}
            className={`px-4 py-2 rounded font-mono text-xs border transition-all ${
              isDualView
                ? 'bg-cyber-blue/20 border-cyber-blue text-cyber-blue'
                : 'bg-cyber-panel border-cyber-border text-cyber-text hover:border-cyber-blue'
            }`}
          >
            {isDualView ? 'DUAL VIEW' : 'SINGLE VIEW'}
          </button>

          {/* View Mode Buttons (only show in dual view) */}
          {isDualView && (
            <>
              <div className="w-px h-6 bg-cyber-border" />
              <div className="flex gap-1">
                <button
                  onClick={() => setViewMode('human')}
                  className={`px-3 py-2 rounded font-mono text-xs border transition-all ${
                    viewMode === 'human'
                      ? 'bg-[#00d4ff]/20 border-[#00d4ff] text-[#00d4ff]'
                      : 'bg-cyber-panel border-cyber-border text-cyber-text hover:border-[#00d4ff]'
                  }`}
                >
                  HUMAN
                </button>
                <button
                  onClick={() => setViewMode('hybrid')}
                  className={`px-3 py-2 rounded font-mono text-xs border transition-all ${
                    viewMode === 'hybrid'
                      ? 'bg-white/20 border-white text-white'
                      : 'bg-cyber-panel border-cyber-border text-cyber-text hover:border-white'
                  }`}
                >
                  HYBRID
                </button>
                <button
                  onClick={() => setViewMode('ai')}
                  className={`px-3 py-2 rounded font-mono text-xs border transition-all ${
                    viewMode === 'ai'
                      ? 'bg-[#d946ef]/20 border-[#d946ef] text-[#d946ef]'
                      : 'bg-cyber-panel border-cyber-border text-cyber-text hover:border-[#d946ef]'
                  }`}
                >
                  AI
                </button>
              </div>
            </>
          )}
        </div>

        {/* Topology Mode Toggle (Dual View Only) */}
        {isDualView && (
          <div className="flex items-center justify-center gap-2 mt-2">
            <div className="text-xs text-cyber-dim">GRAPH:</div>
            <div className="flex gap-1">
              <button
                onClick={() => setTopologyMode('sphere')}
                className={`px-3 py-1 rounded font-mono text-xs border transition-all ${
                  topologyMode === 'sphere'
                    ? 'bg-cyber-blue/20 border-cyber-blue text-cyber-blue'
                    : 'bg-cyber-panel border-cyber-border text-cyber-text hover:border-cyber-blue'
                }`}
                title="Same relationship graph for both (constrained)"
              >
                CONSTRAINED
              </button>
              <button
                onClick={() => setTopologyMode('organic')}
                className={`px-3 py-1 rounded font-mono text-xs border transition-all ${
                  topologyMode === 'organic'
                    ? 'bg-cyber-magenta/20 border-cyber-magenta text-cyber-magenta'
                    : 'bg-cyber-panel border-cyber-border text-cyber-text hover:border-cyber-magenta'
                }`}
                title="Separate k-NN graphs (authentic topology)"
              >
                AUTHENTIC
              </button>
            </div>
          </div>
        )}

        {/* Layout Mode Toggle (Dual View Only) */}
        {isDualView && (
          <div className="flex items-center justify-center gap-2 mt-2">
            <div className="text-xs text-cyber-dim">LAYOUT:</div>
            <div className="flex gap-1">
              <button
                onClick={() => setLayoutMode('graph')}
                className={`px-3 py-1 rounded font-mono text-xs border transition-all ${
                  layoutMode === 'graph'
                    ? 'bg-green-500/20 border-green-500 text-green-500'
                    : 'bg-cyber-panel border-cyber-border text-cyber-text hover:border-green-500'
                }`}
                title="Force-directed graph layout from relationships"
              >
                GRAPH
              </button>
              <button
                onClick={() => setLayoutMode('manifold')}
                className={`px-3 py-1 rounded font-mono text-xs border transition-all ${
                  layoutMode === 'manifold'
                    ? 'bg-yellow-500/20 border-yellow-500 text-yellow-500'
                    : 'bg-cyber-panel border-cyber-border text-cyber-text hover:border-yellow-500'
                }`}
                title="UMAP manifold reduction from embeddings"
              >
                MANIFOLD
              </button>
            </div>
          </div>
        )}

        {/* Color Legend (Dual View Only) */}
        {isDualView && (
          <div className="mt-4 glass rounded p-3 border border-cyber-border/30">
            <div className="text-xs text-cyber-dim mb-2 font-bold">COLOR KEY</div>

            {/* Node Colors */}
            <div className="mb-3">
              <div className="text-xs text-cyber-dim mb-1">Nodes:</div>
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-xs">
                  <div className="w-3 h-3 rounded-full bg-[#00d4ff]" style={{boxShadow: '0 0 8px #00d4ff'}}></div>
                  <span className="text-cyber-text">Human (MiniLM)</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <div className="w-3 h-3 rounded-full bg-[#d946ef]" style={{boxShadow: '0 0 8px #d946ef'}}></div>
                  <span className="text-cyber-text">AI (Qwen)</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <div className="w-3 h-3 rounded-full bg-green-500" style={{boxShadow: '0 0 8px #00ff00'}}></div>
                  <span className="text-cyber-text">Spatial Neighbors</span>
                </div>
              </div>
            </div>

            {/* Connection Line Colors */}
            <div>
              <div className="text-xs text-cyber-dim mb-1">Connection Lines:</div>
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-xs">
                  <div className="w-8 h-0.5 bg-green-500"></div>
                  <span className="text-cyber-text">Local Integrity</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <div className="w-8 h-0.5 bg-yellow-500"></div>
                  <span className="text-cyber-text">Stretching</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  <div className="w-8 h-0.5 bg-red-500"></div>
                  <span className="text-cyber-text">Wormholes</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
