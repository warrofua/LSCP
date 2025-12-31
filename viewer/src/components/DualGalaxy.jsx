import { useRef, useMemo } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Html } from '@react-three/drei';
import * as THREE from 'three';
import useStore from '../store';

/**
 * DualGalaxy - Renders overlapping Human (MiniLM) and AI (Qwen) concept spaces
 * Cyan spheres = Human understanding
 * Magenta spheres = AI understanding
 * White lines = Semantic drift (tension)
 */
export default function DualGalaxy() {
  const { camera } = useThree();
  const controlsRef = useRef();
  const dualNodes = useStore((state) => state.dualNodes);
  const selectedNode = useStore((state) => state.selectedNode);
  const setSelectedNode = useStore((state) => state.setSelectedNode);
  const setSelectedNodeData = useStore((state) => state.setSelectedNodeData);
  const viewMode = useStore((state) => state.viewMode); // 'human', 'ai', or 'hybrid'
  const topologyMode = useStore((state) => state.topologyMode); // 'sphere' or 'organic'
  const layoutMode = useStore((state) => state.layoutMode); // 'graph' or 'manifold'

  // Track connected nodes for highlighting
  const selectedNodeData = useStore((state) => state.selectedNodeData);
  const connectedNodes = useMemo(() => {
    const connected = new Set();
    if (selectedNodeData && selectedNodeData.relationships) {
      selectedNodeData.relationships.forEach((rel) => {
        connected.add(rel.target);
      });
    }
    return connected;
  }, [selectedNodeData]);

  const handleNodeClick = async (node) => {
    setSelectedNode(node);
    // Clear old connections immediately to prevent stale lines
    setSelectedNodeData(null);

    // Fetch detailed node data to get connections
    try {
      const res = await fetch(`http://localhost:8001/api/node/${node.name}`);
      const data = await res.json();
      setSelectedNodeData(data);
    } catch (err) {
      console.error('Failed to load node data:', err);
    }
  };

  // Validate that data matches current layout mode
  const dataMatchesLayout = useMemo(() => {
    if (!dualNodes || dualNodes.length === 0) return false;

    const firstNode = dualNodes[0];
    if (layoutMode === 'manifold') {
      // Manifold mode requires UMAP coordinates
      return firstNode.pos_human_umap !== undefined && firstNode.pos_ai_umap !== undefined;
    } else {
      // Graph mode requires regular coordinates
      return firstNode.pos_human !== undefined && firstNode.pos_ai !== undefined;
    }
  }, [dualNodes, layoutMode]);

  // Helper: Calculate 3D Euclidean distance
  const calculateDistance3D = (pos1, pos2) => {
    const [x1, y1, z1] = pos1;
    const [x2, y2, z2] = pos2;
    return Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2);
  };

  // Helper: Get distortion color based on percentile (Green -> Yellow -> Red)
  const getDistortionColor = (distance, p50, p80) => {
    if (distance <= p50) {
      // Green zone (0-50th percentile) - local integrity
      const t = distance / p50;
      return `rgb(${Math.floor(0 + t * 100)}, ${Math.floor(255 - t * 100)}, 0)`;
    } else if (distance <= p80) {
      // Yellow zone (50th-80th percentile) - stretching
      const t = (distance - p50) / (p80 - p50);
      return `rgb(${Math.floor(100 + t * 155)}, ${Math.floor(155 - t * 155)}, 0)`;
    } else {
      // Red zone (80th-100th percentile) - wormholes!
      return '#ff0000';
    }
  };

  // Calculate all distances and percentiles for distortion color-coding
  const connectionDistances = useMemo(() => {
    if (!selectedNode || !selectedNodeData || !selectedNodeData.relationships) {
      return { human: [], ai: [], humanP50: 0, humanP80: 0, aiP50: 0, aiP80: 0 };
    }

    const humanDists = [];
    const aiDists = [];

    selectedNodeData.relationships.forEach((rel) => {
      const targetNode = dualNodes.find(n => n.name === rel.target);
      if (!targetNode) return;

      // Get coordinates based on layout mode and topology mode
      let humanPosSource, aiPosSource, humanPosTarget, aiPosTarget;

      if (layoutMode === 'manifold') {
        humanPosSource = selectedNode.pos_human_umap || [0, 0, 0];
        aiPosSource = selectedNode.pos_ai_umap || [0, 0, 0];
        humanPosTarget = targetNode.pos_human_umap || [0, 0, 0];
        aiPosTarget = targetNode.pos_ai_umap || [0, 0, 0];
      } else {
        humanPosSource = topologyMode === 'organic' && selectedNode.pos_human_organic
          ? selectedNode.pos_human_organic
          : selectedNode.pos_human;
        aiPosSource = topologyMode === 'organic' && selectedNode.pos_ai_organic
          ? selectedNode.pos_ai_organic
          : selectedNode.pos_ai;
        humanPosTarget = topologyMode === 'organic' && targetNode.pos_human_organic
          ? targetNode.pos_human_organic
          : targetNode.pos_human;
        aiPosTarget = topologyMode === 'organic' && targetNode.pos_ai_organic
          ? targetNode.pos_ai_organic
          : targetNode.pos_ai;
      }

      humanDists.push(calculateDistance3D(humanPosSource, humanPosTarget));
      aiDists.push(calculateDistance3D(aiPosSource, aiPosTarget));
    });

    // Calculate percentiles
    const percentile = (arr, p) => {
      if (arr.length === 0) return 0;
      const sorted = [...arr].sort((a, b) => a - b);
      const index = Math.ceil(sorted.length * p) - 1;
      return sorted[Math.max(0, index)];
    };

    return {
      human: humanDists,
      ai: aiDists,
      humanP50: percentile(humanDists, 0.5),
      humanP80: percentile(humanDists, 0.8),
      aiP50: percentile(aiDists, 0.5),
      aiP80: percentile(aiDists, 0.8),
    };
  }, [selectedNode, selectedNodeData, dualNodes, layoutMode, topologyMode]);

  // Calculate spatial neighbors (k=5) for the selected node
  const spatialNeighbors = useMemo(() => {
    if (!selectedNode || !dualNodes) return new Set();

    const getPosition = (node) => {
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

    const selectedPos = getPosition(selectedNode);

    const neighbors = dualNodes
      .filter((node) => node.name !== selectedNode.name)
      .map((node) => ({
        name: node.name,
        distance: calculateDistance3D(selectedPos, getPosition(node)),
      }))
      .sort((a, b) => a.distance - b.distance)
      .slice(0, 5)
      .map((n) => n.name);

    return new Set(neighbors);
  }, [selectedNode, dualNodes, layoutMode, topologyMode, viewMode]);

  if (!dualNodes || dualNodes.length === 0 || !dataMatchesLayout) {
    return (
      <group>
        <OrbitControls ref={controlsRef} enableDamping dampingFactor={0.05} />
        <Html center>
          <div className="text-cyber-text font-mono text-sm">
            Loading dual-view galaxy...
          </div>
        </Html>
      </group>
    );
  }

  return (
    <group>
      <OrbitControls ref={controlsRef} enableDamping dampingFactor={0.05} />
      <ambientLight intensity={0.3} />
      <pointLight position={[10, 10, 10]} intensity={0.5} />

      {/* Render connection lines for selected node */}
      {selectedNode && selectedNodeData && selectedNodeData.relationships && (
        <>
          {selectedNodeData.relationships.map((rel, idx) => {
            const targetNode = dualNodes.find(n => n.name === rel.target);
            if (!targetNode) return null;

            // Select coordinates based on layout mode and topology mode
            let humanPosSource, aiPosSource, humanPosTarget, aiPosTarget;

            if (layoutMode === 'manifold') {
              // UMAP manifold coordinates (topology mode doesn't apply)
              humanPosSource = selectedNode.pos_human_umap || [0, 0, 0];
              aiPosSource = selectedNode.pos_ai_umap || [0, 0, 0];
              humanPosTarget = targetNode.pos_human_umap || [0, 0, 0];
              aiPosTarget = targetNode.pos_ai_umap || [0, 0, 0];
            } else {
              // Graph-based coordinates (respect topology mode)
              humanPosSource = topologyMode === 'organic' && selectedNode.pos_human_organic
                ? selectedNode.pos_human_organic
                : selectedNode.pos_human;
              aiPosSource = topologyMode === 'organic' && selectedNode.pos_ai_organic
                ? selectedNode.pos_ai_organic
                : selectedNode.pos_ai;
              humanPosTarget = topologyMode === 'organic' && targetNode.pos_human_organic
                ? targetNode.pos_human_organic
                : targetNode.pos_human;
              aiPosTarget = topologyMode === 'organic' && targetNode.pos_ai_organic
                ? targetNode.pos_ai_organic
                : targetNode.pos_ai;
            }

            const [hx_source, hy_source, hz_source] = humanPosSource;
            const [ax_source, ay_source, az_source] = aiPosSource;
            const [hx_target, hy_target, hz_target] = humanPosTarget;
            const [ax_target, ay_target, az_target] = aiPosTarget;

            // Calculate distances for this connection
            const humanDist = connectionDistances.human[idx] || 0;
            const aiDist = connectionDistances.ai[idx] || 0;

            // Get distortion colors
            const humanColor = getDistortionColor(humanDist, connectionDistances.humanP50, connectionDistances.humanP80);
            const aiColor = getDistortionColor(aiDist, connectionDistances.aiP50, connectionDistances.aiP80);

            return (
              <group key={`${selectedNode.name}-${rel.target}-${idx}`}>
                {/* Human-to-human connection line - color-coded by distortion */}
                {(viewMode === 'human' || viewMode === 'hybrid') && (
                  <line>
                    <bufferGeometry>
                      <bufferAttribute
                        attach="attributes-position"
                        count={2}
                        array={new Float32Array([hx_source, hy_source, hz_source, hx_target, hy_target, hz_target])}
                        itemSize={3}
                      />
                    </bufferGeometry>
                    <lineBasicMaterial
                      color={humanColor}
                      opacity={0.7}
                      transparent
                    />
                  </line>
                )}

                {/* AI-to-AI connection line - color-coded by distortion */}
                {(viewMode === 'ai' || viewMode === 'hybrid') && (
                  <line>
                    <bufferGeometry>
                      <bufferAttribute
                        attach="attributes-position"
                        count={2}
                        array={new Float32Array([ax_source, ay_source, az_source, ax_target, ay_target, az_target])}
                        itemSize={3}
                      />
                    </bufferGeometry>
                    <lineBasicMaterial
                      color={aiColor}
                      opacity={0.7}
                      transparent
                    />
                  </line>
                )}
              </group>
            );
          })}
        </>
      )}

      {/* Render nodes and tension lines */}
      {dualNodes.map((node) => (
        <DualNode
          key={node.name}
          node={node}
          isSelected={selectedNode?.name === node.name}
          isConnected={connectedNodes.has(node.name)}
          isSpatialNeighbor={spatialNeighbors.has(node.name)}
          onSelect={() => handleNodeClick(node)}
          viewMode={viewMode}
          topologyMode={topologyMode}
          layoutMode={layoutMode}
        />
      ))}
    </group>
  );
}

function DualNode({ node, isSelected, isConnected, isSpatialNeighbor, onSelect, viewMode, topologyMode, layoutMode }) {
  const humanMeshRef = useRef();
  const aiMeshRef = useRef();
  const selectedNode = useStore((state) => state.selectedNode);

  // Select coordinates based on layout mode and topology mode
  let humanPos, aiPos, driftValue;

  if (layoutMode === 'manifold') {
    // UMAP manifold coordinates (topology mode doesn't apply)
    humanPos = node.pos_human_umap || [0, 0, 0];
    aiPos = node.pos_ai_umap || [0, 0, 0];
    driftValue = node.drift_umap !== undefined ? node.drift_umap : node.drift || 0;
  } else {
    // Graph-based coordinates (respect topology mode)
    humanPos = topologyMode === 'organic' && node.pos_human_organic
      ? node.pos_human_organic
      : node.pos_human;
    aiPos = topologyMode === 'organic' && node.pos_ai_organic
      ? node.pos_ai_organic
      : node.pos_ai;
    driftValue = node.drift || 0;
  }

  const [hx, hy, hz] = humanPos;
  const [ax, ay, az] = aiPos;

  // Determine visibility based on view mode
  const showHuman = viewMode === 'human' || viewMode === 'hybrid';
  const showAI = viewMode === 'ai' || viewMode === 'hybrid';
  // Only show tension lines for selected or connected nodes in hybrid mode
  const showTension = viewMode === 'hybrid' && (isSelected || isConnected);

  // Dim non-connected/non-spatial nodes when something is selected
  const opacity = selectedNode && !isSelected && !isConnected && !isSpatialNeighbor ? 0.15 : 1.0;

  // Size based on selection, connection, and spatial proximity
  const baseSize = 0.15;
  const size = isSelected
    ? baseSize * 1.5
    : isConnected
      ? baseSize * 1.2
      : isSpatialNeighbor
        ? baseSize * 1.4
        : baseSize;

  // Pulsing animation for selected node
  useFrame((state) => {
    if (isSelected) {
      const pulse = 1 + Math.sin(state.clock.elapsedTime * 3) * 0.2;
      if (humanMeshRef.current) {
        humanMeshRef.current.scale.setScalar(pulse);
      }
      if (aiMeshRef.current) {
        aiMeshRef.current.scale.setScalar(pulse);
      }
    }
  });

  return (
    <group>
      {/* Tension line (drift vector) - THICK when selected */}
      {showTension && (
        <line>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={2}
              array={new Float32Array([hx, hy, hz, ax, ay, az])}
              itemSize={3}
            />
          </bufferGeometry>
          <lineBasicMaterial
            color={isSelected ? "#ffffff" : isConnected ? "#ffffff" : "#ffffff"}
            opacity={(isSelected ? 0.9 : isConnected ? 0.4 : 0.2) * opacity}
            transparent
            linewidth={isSelected ? 3 : isConnected ? 1.5 : 1}
          />
        </line>
      )}

      {/* Human (MiniLM) node - Cyan (or green for spatial neighbors) */}
      {showHuman && (
        <mesh
          ref={humanMeshRef}
          position={[hx, hy, hz]}
          onClick={(e) => {
            e.stopPropagation();
            onSelect();
          }}
        >
          <sphereGeometry args={[size, 16, 16]} />
          <meshStandardMaterial
            color={isSpatialNeighbor ? "#00ff00" : "#00d4ff"}
            emissive={isSpatialNeighbor ? "#00ff00" : "#00d4ff"}
            emissiveIntensity={
              isSelected ? 0.5 :
              isSpatialNeighbor ? 1.5 :
              isConnected ? 0.4 :
              0.2
            }
            opacity={(viewMode === 'hybrid' ? 0.7 : 1.0) * opacity}
            transparent
          />
          {/* Add point light for spatial neighbors to create real glow */}
          {isSpatialNeighbor && (
            <pointLight color="#00ff00" intensity={2} distance={3} decay={2} />
          )}
          {(isSelected || isConnected || isSpatialNeighbor) && (
            <Html distanceFactor={10}>
              <div className={`bg-cyber-panel border px-2 py-1 rounded text-cyber-text font-mono text-xs whitespace-nowrap pointer-events-none ${
                isSpatialNeighbor ? 'border-green-500' : 'border-cyber-blue'
              }`}>
                {node.name} {isSelected ? '(HUMAN)' : isSpatialNeighbor ? '(SPATIAL)' : ''}
              </div>
            </Html>
          )}
        </mesh>
      )}

      {/* AI (Qwen) node - Magenta (or green for spatial neighbors) */}
      {showAI && (
        <mesh
          ref={aiMeshRef}
          position={[ax, ay, az]}
          onClick={(e) => {
            e.stopPropagation();
            onSelect();
          }}
        >
          <sphereGeometry args={[size, 16, 16]} />
          <meshStandardMaterial
            color={isSpatialNeighbor ? "#00ff00" : "#d946ef"}
            emissive={isSpatialNeighbor ? "#00ff00" : "#d946ef"}
            emissiveIntensity={
              isSelected ? 0.5 :
              isSpatialNeighbor ? 1.5 :
              isConnected ? 0.4 :
              0.2
            }
            opacity={(viewMode === 'hybrid' ? 0.7 : 1.0) * opacity}
            transparent
          />
          {/* Add point light for spatial neighbors to create real glow */}
          {isSpatialNeighbor && (
            <pointLight color="#00ff00" intensity={2} distance={3} decay={2} />
          )}
          {(isSelected || isConnected || isSpatialNeighbor) && (
            <Html distanceFactor={10}>
              <div className={`bg-cyber-panel border px-2 py-1 rounded text-cyber-text font-mono text-xs whitespace-nowrap pointer-events-none ${
                isSpatialNeighbor ? 'border-green-500' : 'border-cyber-magenta'
              }`}>
                {node.name} {isSelected ? `(AI) - drift: ${driftValue.toFixed(3)}` : isSpatialNeighbor ? '(SPATIAL)' : ''}
              </div>
            </Html>
          )}
        </mesh>
      )}
    </group>
  );
}
