import { useState } from 'react';
import useStore from '../store';

export default function Inspector() {
  const { selectedNode, selectedNodeData, clearSelection, isDualView, dualNodes, selectNode, setSelectedNodeData, layoutMode, topologyMode, viewMode } = useStore();
  const [expandedReasoning, setExpandedReasoning] = useState({});
  const [showLeaderboard, setShowLeaderboard] = useState(false);

  if (!selectedNode) return null;

  // Get the appropriate drift property based on layout mode
  const getDrift = (node) => {
    if (layoutMode === 'manifold') {
      return node.drift_umap !== undefined ? node.drift_umap : 0;
    }
    return node.drift !== undefined ? node.drift : 0;
  };

  // Helper: Calculate 3D Euclidean distance
  const calculateDistance3D = (pos1, pos2) => {
    if (!pos1 || !pos2) return 0;
    const [x1, y1, z1] = pos1;
    const [x2, y2, z2] = pos2;
    return Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2);
  };

  // Get position based on current layout and topology mode
  const getPosition = (node) => {
    if (!node) return [0, 0, 0];
    if (layoutMode === 'manifold') {
      return viewMode === 'human' || viewMode === 'hybrid'
        ? node.pos_human_umap || [0, 0, 0]
        : node.pos_ai_umap || [0, 0, 0];
    } else {
      if (viewMode === 'human' || viewMode === 'hybrid') {
        return topologyMode === 'organic' && node.pos_human_organic
          ? node.pos_human_organic
          : node.pos_human;
      } else {
        return topologyMode === 'organic' && node.pos_ai_organic
          ? node.pos_ai_organic
          : node.pos_ai;
      }
    }
  };

  // Calculate spatial neighbors (k=5) in 3D space
  const spatialNeighbors = isDualView && dualNodes
    ? dualNodes
        .filter((node) => node.name !== selectedNode.name)
        .map((node) => ({
          ...node,
          dist3D: calculateDistance3D(getPosition(selectedNode), getPosition(node)),
        }))
        .sort((a, b) => a.dist3D - b.dist3D)
        .slice(0, 5)
    : [];

  // Calculate distortion scores for semantic bridges
  const semanticBridgesWithDistortion = selectedNodeData?.relationships?.map((rel) => {
    const targetNode = dualNodes?.find((n) => n.name === rel.target);
    if (!targetNode) return { ...rel, distortion3D: 0 };

    const dist3D = calculateDistance3D(getPosition(selectedNode), getPosition(targetNode));
    return {
      ...rel,
      distortion3D: dist3D,
    };
  }) || [];

  // Get top drift concepts for leaderboard
  const topDriftNodes = isDualView && dualNodes
    ? [...dualNodes].sort((a, b) => getDrift(b) - getDrift(a)).slice(0, 15)
    : [];

  const handleSelectDriftNode = async (node) => {
    selectNode(node);

    // Fetch node details
    try {
      const res = await fetch(`http://localhost:8001/api/node/${node.name}`);
      const data = await res.json();
      setSelectedNodeData(data);
    } catch (err) {
      console.error('Failed to load node:', err);
    }
  };

  const toggleReasoning = (index) => {
    setExpandedReasoning((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  return (
    <div className="absolute right-0 top-0 h-screen w-96 glass p-6 overflow-y-auto pointer-events-auto z-50">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-xl font-bold text-cyber-blue glow-blue">
            {selectedNode.name.toUpperCase()}
          </h2>
          <p className="text-xs text-cyber-dim mt-1">NODE INSPECTOR</p>
        </div>
        <button
          onClick={clearSelection}
          className="text-cyber-dim hover:text-cyber-text transition-colors"
        >
          ✕
        </button>
      </div>

      {/* Drift Score (Dual View Only) */}
      {isDualView && getDrift(selectedNode) > 0 && (
        <div className="mb-6 border border-cyber-magenta/30 rounded p-4">
          <div className="text-xs text-cyber-dim mb-2">
            SEMANTIC DRIFT {layoutMode === 'manifold' ? '(MANIFOLD)' : '(GRAPH)'}
          </div>
          <div className="text-3xl font-bold text-cyber-magenta glow-magenta">
            {getDrift(selectedNode).toFixed(3)}
          </div>
          <div className="text-xs text-cyber-dim mt-2">
            Distance between Human and AI concept spaces
          </div>
        </div>
      )}

      {/* Drift Leaderboard Toggle (Dual View Only) */}
      {isDualView && topDriftNodes.length > 0 && (
        <div className="mb-6">
          <button
            onClick={() => setShowLeaderboard(!showLeaderboard)}
            className="w-full px-4 py-2 border border-cyber-border hover:border-cyber-magenta text-cyber-text hover:text-cyber-magenta transition-colors rounded text-sm font-mono"
          >
            {showLeaderboard ? '▼' : '▶'} DRIFT LEADERBOARD
          </button>

          {showLeaderboard && (
            <div className="mt-3 space-y-2 max-h-96 overflow-y-auto">
              {topDriftNodes.map((node, i) => (
                <div
                  key={node.name}
                  onClick={() => handleSelectDriftNode(node)}
                  className={`p-2 rounded border transition-colors cursor-pointer ${
                    node.name === selectedNode.name
                      ? 'border-cyber-magenta bg-cyber-magenta/10'
                      : 'border-cyber-border hover:border-cyber-magenta/50 hover:bg-cyber-magenta/5'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="text-xs text-cyber-dim w-6">#{i + 1}</div>
                      <div className="text-sm text-cyber-text font-mono">
                        {node.name}
                      </div>
                    </div>
                    <div className="text-sm text-cyber-magenta font-bold">
                      {getDrift(node).toFixed(3)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Metrics */}
      <div className="mb-6">
        <div className="text-xs text-cyber-dim mb-2">SEMANTIC DIVERGENCE</div>
        <div className="h-2 bg-cyber-border rounded overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-cyber-blue to-cyber-red transition-all"
            style={{ width: `${selectedNode.avgDistance * 100}%` }}
          />
        </div>
        <div className="text-right text-xs text-cyber-text mt-1">
          {(selectedNode.avgDistance * 100).toFixed(1)}%
        </div>
      </div>

      {/* Connections */}
      <div className="mb-6">
        <div className="text-xs text-cyber-dim mb-2">CONNECTIONS</div>
        <div className="text-2xl font-bold text-cyber-text">
          {selectedNode.connections}
        </div>
      </div>

      {/* Spatial Context (Topic Cluster) - Only in Dual View */}
      {isDualView && spatialNeighbors.length > 0 && (
        <div className="mb-6">
          <div className="text-xs text-cyber-dim mb-2 flex items-center gap-2">
            <span>📍 SPATIAL CONTEXT</span>
            <span className="text-cyber-text/50">(3D Neighbors)</span>
          </div>
          <div className="text-xs text-cyber-dim mb-3">
            Local manifold cluster around selected node
          </div>

          <div className="space-y-2">
            {spatialNeighbors.map((neighbor, i) => (
              <div
                key={neighbor.name}
                onClick={() => handleSelectDriftNode(neighbor)}
                className="border border-cyber-border/50 rounded p-2 hover:border-green-500/50 hover:bg-green-500/5 transition-colors cursor-pointer"
              >
                <div className="flex items-center justify-between">
                  <div className="text-sm text-cyber-text font-mono">
                    {neighbor.name}
                  </div>
                  <div className="text-xs text-green-500">
                    {neighbor.dist3D.toFixed(2)}u
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Semantic Bridges (High-D Connections) */}
      {selectedNodeData && (
        <div>
          <div className="text-xs text-cyber-dim mb-2 flex items-center gap-2">
            <span>🔗 SEMANTIC BRIDGES</span>
            <span className="text-cyber-text/50">({selectedNodeData.relationships?.length || 0})</span>
          </div>
          <div className="text-xs text-cyber-dim mb-3">
            Connections from high-dimensional semantic space
          </div>

          <div className="space-y-3">
            {semanticBridgesWithDistortion.slice(0, 10).map((rel, i) => {
              // Determine distortion color
              let distortionColor = 'text-green-500';
              let distortionLabel = 'Local';
              if (rel.distortion3D > 5) {
                distortionColor = 'text-red-500';
                distortionLabel = 'Wormhole';
              } else if (rel.distortion3D > 2) {
                distortionColor = 'text-yellow-500';
                distortionLabel = 'Stretching';
              }

              return (
                <div
                  key={i}
                  className="border border-cyber-border rounded p-3 hover:border-cyber-blue/50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="text-sm text-cyber-text font-mono">
                      → {rel.target}
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="text-xs text-cyber-dim">
                        {rel.distance.toFixed(3)}
                      </div>
                    </div>
                  </div>

                  {/* Distortion metric */}
                  {isDualView && (
                    <div className={`text-xs ${distortionColor} mb-2`}>
                      3D Distortion: {rel.distortion3D.toFixed(2)}u ({distortionLabel})
                    </div>
                  )}

                  {rel.bridge && (
                    <div className="text-xs text-cyber-dim mb-2 leading-relaxed">
                      {rel.bridge}
                    </div>
                  )}

                  {rel.reasoning && (
                    <div className="mt-2">
                      <button
                        onClick={() => toggleReasoning(i)}
                        className="text-xs text-cyber-blue hover:text-cyber-blue/80 transition-colors"
                      >
                        {expandedReasoning[i] ? '▼' : '▶'} THINKING TRACE
                      </button>

                      {expandedReasoning[i] && (
                        <div className="mt-2 p-2 bg-black/40 rounded border border-cyber-border/30">
                          <div className="text-xs text-cyber-dim font-mono leading-relaxed whitespace-pre-wrap">
                            {rel.reasoning}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
