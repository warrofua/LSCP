import { useRef, useEffect } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Html } from '@react-three/drei';
import * as THREE from 'three';
import useStore from '../store';

function Node({ node, onClick, connectedNodes }) {
  const meshRef = useRef();
  const selectedNode = useStore((state) => state.selectedNode);
  const isSelected = selectedNode?.id === node.id;
  const isConnected = connectedNodes.has(node.name);

  // Color based on avgDistance (blue = low/human, red = high/alien)
  const color = new THREE.Color().lerpColors(
    new THREE.Color('#00d4ff'), // Cyan (human)
    new THREE.Color('#ff006e'), // Magenta (alien)
    node.avgDistance
  );

  // Pulse animation for high-delta nodes or connected nodes
  useFrame((state) => {
    if (meshRef.current && (node.avgDistance > 0.55 || isConnected)) {
      const scale = 1 + Math.sin(state.clock.elapsedTime * 2) * 0.1;
      meshRef.current.scale.setScalar(scale);
    }
  });

  // Dim non-connected nodes when something is selected
  const opacity = selectedNode && !isSelected && !isConnected ? 0.2 : 1.0;
  const size = isSelected ? 0.5 : isConnected ? 0.35 : 0.3;

  return (
    <group position={node.position}>
      <mesh
        ref={meshRef}
        onClick={(e) => {
          e.stopPropagation();
          onClick(node);
        }}
        onPointerOver={(e) => {
          e.stopPropagation();
          document.body.style.cursor = 'pointer';
        }}
        onPointerOut={() => {
          document.body.style.cursor = 'default';
        }}
      >
        <sphereGeometry args={[size, 16, 16]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={isSelected ? 0.8 : isConnected ? 0.6 : 0.4}
          opacity={opacity}
          transparent
        />
      </mesh>

      {/* Label for selected and connected nodes */}
      {(isSelected || isConnected) && (
        <Html distanceFactor={10}>
          <div className="px-2 py-1 bg-black/80 text-cyber-blue text-xs rounded border border-cyber-blue/30 whitespace-nowrap">
            {node.name}
          </div>
        </Html>
      )}
    </group>
  );
}

function Edge({ edge, nodes }) {
  const selectedNode = useStore((state) => state.selectedNode);
  const sourceNode = nodes.find((n) => n.name === edge.source);
  const targetNode = nodes.find((n) => n.name === edge.target);

  if (!sourceNode || !targetNode) return null;

  const points = [
    new THREE.Vector3(...sourceNode.position),
    new THREE.Vector3(...targetNode.position),
  ];

  const geometry = new THREE.BufferGeometry().setFromPoints(points);

  // Check if this edge is connected to the selected node
  const isConnected = selectedNode &&
    (edge.source === selectedNode.name || edge.target === selectedNode.name);

  // Color and opacity based on selection
  const opacity = isConnected
    ? 0.8
    : selectedNode
      ? 0.02
      : Math.max(0.05, 1 - edge.distance);

  const color = isConnected ? '#00d4ff' : '#ffffff';

  return (
    <line geometry={geometry}>
      <lineBasicMaterial
        color={color}
        opacity={opacity}
        transparent
        linewidth={isConnected ? 2 : 1}
      />
    </line>
  );
}

export default function Galaxy() {
  const { nodes, edges, selectNode, setSelectedNodeData, loading, selectedNode } = useStore();
  const { camera } = useThree();
  const controlsRef = useRef();

  const handleNodeClick = async (node) => {
    selectNode(node);

    // Fetch detailed node data
    try {
      const res = await fetch(`http://localhost:8001/api/node/${node.name}`);
      const data = await res.json();
      setSelectedNodeData(data);
    } catch (err) {
      console.error('Failed to load node data:', err);
    }
  };

  // Get connected node names for highlighting
  const connectedNodes = new Set();
  if (selectedNode) {
    edges.forEach((edge) => {
      if (edge.source === selectedNode.name) {
        connectedNodes.add(edge.target);
      } else if (edge.target === selectedNode.name) {
        connectedNodes.add(edge.source);
      }
    });
  }

  // Zoom to selected node and its neighborhood
  useEffect(() => {
    if (selectedNode && selectedNode.position && controlsRef.current) {
      const [x, y, z] = selectedNode.position;

      // Calculate bounding sphere of connected nodes
      let minX = x, maxX = x, minY = y, maxY = y, minZ = z, maxZ = z;

      connectedNodes.forEach((nodeName) => {
        const node = nodes.find((n) => n.name === nodeName);
        if (node) {
          const [nx, ny, nz] = node.position;
          minX = Math.min(minX, nx);
          maxX = Math.max(maxX, nx);
          minY = Math.min(minY, ny);
          maxY = Math.max(maxY, ny);
          minZ = Math.min(minZ, nz);
          maxZ = Math.max(maxZ, nz);
        }
      });

      // Calculate center and size of the group
      const centerX = (minX + maxX) / 2;
      const centerY = (minY + maxY) / 2;
      const centerZ = (minZ + maxZ) / 2;
      const size = Math.max(maxX - minX, maxY - minY, maxZ - minZ);
      const distance = Math.max(size * 2, 10); // Zoom distance based on group size

      // Smoothly animate camera
      const startPos = camera.position.clone();
      const endPos = new THREE.Vector3(centerX, centerY, centerZ + distance);
      const startTarget = controlsRef.current.target.clone();
      const endTarget = new THREE.Vector3(centerX, centerY, centerZ);

      let progress = 0;
      const animate = () => {
        progress += 0.05;
        if (progress < 1) {
          camera.position.lerpVectors(startPos, endPos, progress);
          controlsRef.current.target.lerpVectors(startTarget, endTarget, progress);
          controlsRef.current.update();
          requestAnimationFrame(animate);
        } else {
          camera.position.copy(endPos);
          controlsRef.current.target.copy(endTarget);
          controlsRef.current.update();
        }
      };
      animate();
    }
  }, [selectedNode, camera, nodes, connectedNodes]);

  if (loading) {
    return null;
  }

  return (
    <>
      <ambientLight intensity={0.3} />
      <pointLight position={[10, 10, 10]} intensity={0.5} />

      <OrbitControls
        ref={controlsRef}
        enableDamping
        dampingFactor={0.05}
        rotateSpeed={0.5}
        zoomSpeed={0.8}
        minDistance={5}
        maxDistance={100}
      />

      {/* Render edges first (so they appear behind nodes) */}
      {edges.slice(0, 200).map((edge, i) => (
        <Edge key={i} edge={edge} nodes={nodes} />
      ))}

      {/* Render nodes */}
      {nodes.map((node) => (
        <Node
          key={node.id}
          node={node}
          onClick={handleNodeClick}
          connectedNodes={connectedNodes}
        />
      ))}
    </>
  );
}
