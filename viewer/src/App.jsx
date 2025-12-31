import { useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import Galaxy from './components/Galaxy';
import DualGalaxy from './components/DualGalaxy';
import Interface from './components/Interface';
import Inspector from './components/Inspector';
import useStore from './store';

const API_URL = 'http://localhost:8001';

function App() {
  const setGalaxyData = useStore((state) => state.setGalaxyData);
  const setDualGalaxyData = useStore((state) => state.setDualGalaxyData);
  const isDualView = useStore((state) => state.isDualView);
  const layoutMode = useStore((state) => state.layoutMode);

  useEffect(() => {
    // Fetch regular galaxy data
    fetch(`${API_URL}/api/galaxy`)
      .then((res) => res.json())
      .then((data) => {
        setGalaxyData(data.nodes, data.edges);
      })
      .catch((err) => console.error('Failed to load galaxy:', err));

    // Fetch dual-view galaxy data based on layout mode
    const dualEndpoint = layoutMode === 'manifold'
      ? `${API_URL}/api/galaxy/manifold`
      : `${API_URL}/api/galaxy/dual`;

    fetch(dualEndpoint)
      .then((res) => res.json())
      .then((data) => {
        setDualGalaxyData(data);
      })
      .catch((err) => console.error(`Failed to load dual galaxy (${layoutMode}):`, err));
  }, [setGalaxyData, setDualGalaxyData, layoutMode]);

  return (
    <div className="w-screen h-screen overflow-hidden bg-cyber-bg">
      {/* 3D Canvas - Lower z-index so labels appear behind UI panels */}
      <div className="absolute inset-0 z-0">
        <Canvas
          camera={{ position: [0, 0, 30], fov: 75 }}
          gl={{ antialias: true }}
        >
          <color attach="background" args={['#050505']} />
          {isDualView ? <DualGalaxy /> : <Galaxy />}
        </Canvas>
      </div>

      {/* UI Overlay */}
      <Interface />

      {/* Inspector Panel */}
      <Inspector />
    </div>
  );
}

export default App;
