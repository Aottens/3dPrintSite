"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { Canvas, useLoader, useThree } from "@react-three/fiber";
import { OrbitControls, Center, Environment, Grid } from "@react-three/drei";
import { STLLoader } from "three-stdlib";
import * as THREE from "three";

interface ModelProps {
  url: string;
}

function Model({ url }: ModelProps) {
  const geometry = useLoader(STLLoader, url);
  const meshRef = useRef<THREE.Mesh>(null);
  const { camera } = useThree();

  useEffect(() => {
    if (meshRef.current && geometry) {
      // Center the geometry
      geometry.center();

      // Compute bounding box for camera positioning
      geometry.computeBoundingBox();
      const bbox = geometry.boundingBox;

      if (bbox) {
        const size = new THREE.Vector3();
        bbox.getSize(size);
        const maxDim = Math.max(size.x, size.y, size.z);

        // Position camera to fit the model
        const fov = 50;
        const aspect = 1;
        const distance = maxDim / (2 * Math.tan((fov * Math.PI) / 360));

        camera.position.set(distance * 1.5, distance * 1.5, distance * 1.5);
        camera.lookAt(0, 0, 0);
        camera.updateProjectionMatrix();
      }
    }
  }, [geometry, camera]);

  return (
    <Center>
      <mesh ref={meshRef} geometry={geometry}>
        <meshStandardMaterial
          color="#10B981"
          metalness={0.1}
          roughness={0.6}
          flatShading={false}
        />
      </mesh>
    </Center>
  );
}

function LoadingIndicator() {
  return (
    <mesh>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial color="#9CA3AF" wireframe />
    </mesh>
  );
}

interface ModelViewerProps {
  fileUrl?: string;
  fileBlob?: Blob;
  className?: string;
}

export function ModelViewer({ fileUrl, fileBlob, className = "" }: ModelViewerProps) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (fileBlob) {
      const url = URL.createObjectURL(fileBlob);
      setBlobUrl(url);
      return () => URL.revokeObjectURL(url);
    }
    return undefined;
  }, [fileBlob]);

  const modelUrl = blobUrl || fileUrl;

  if (!modelUrl) {
    return (
      <div className={`flex items-center justify-center bg-slate-100 rounded-lg ${className}`}>
        <p className="text-sm text-brand-muted">No model to display</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center bg-slate-100 rounded-lg ${className}`}>
        <p className="text-sm text-red-500">{error}</p>
      </div>
    );
  }

  return (
    <div className={`bg-slate-900 rounded-lg overflow-hidden ${className}`}>
      <Canvas
        camera={{ position: [100, 100, 100], fov: 50 }}
        gl={{ antialias: true }}
        onCreated={({ gl }) => {
          gl.setClearColor("#1a1a2e");
        }}
      >
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} intensity={1} />
        <directionalLight position={[-10, -10, -5]} intensity={0.5} />

        <Suspense fallback={<LoadingIndicator />}>
          <Model url={modelUrl} />
        </Suspense>

        <OrbitControls
          enablePan={true}
          enableZoom={true}
          enableRotate={true}
          minDistance={10}
          maxDistance={500}
        />

        <Grid
          position={[0, -50, 0]}
          args={[200, 200]}
          cellSize={10}
          cellColor="#4a4a6a"
          sectionSize={50}
          sectionColor="#6a6a8a"
          fadeDistance={300}
          infiniteGrid
        />
      </Canvas>
    </div>
  );
}

export default ModelViewer;
