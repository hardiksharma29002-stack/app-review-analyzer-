"use client";

import { useRef, useMemo } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { Environment, Float, Sphere, MeshDistortMaterial } from "@react-three/drei";

function CursorLight() {
  const lightRef = useRef<THREE.PointLight>(null);
  const { viewport, pointer } = useThree();

  useFrame(() => {
    if (lightRef.current) {
      // Lerp light position to cursor
      const x = (pointer.x * viewport.width) / 2;
      const y = (pointer.y * viewport.height) / 2;
      lightRef.current.position.lerp(new THREE.Vector3(x, y, 2), 0.1);
    }
  });

  return (
    <pointLight
      ref={lightRef}
      distance={15}
      intensity={80}
      color="#00D09C"
    />
  );
}

function FloatingBlobs() {
  return (
    <group>
      <Float speed={2} rotationIntensity={1.5} floatIntensity={2}>
        <Sphere args={[1, 64, 64]} position={[-3, 1, -5]} scale={1.5}>
          <MeshDistortMaterial
            color="#00D09C"
            envMapIntensity={1}
            clearcoat={1}
            clearcoatRoughness={0.1}
            metalness={0.8}
            roughness={0.1}
            distort={0.4}
            speed={2}
          />
        </Sphere>
      </Float>
      
      <Float speed={1.5} rotationIntensity={2} floatIntensity={1.5}>
        <Sphere args={[1, 64, 64]} position={[4, -2, -6]} scale={2}>
          <MeshDistortMaterial
            color="#2A2A33"
            envMapIntensity={1}
            clearcoat={0.8}
            metalness={0.9}
            roughness={0.2}
            distort={0.5}
            speed={1.5}
          />
        </Sphere>
      </Float>
    </group>
  );
}

function Particles() {
  const count = 500;
  const mesh = useRef<THREE.InstancedMesh>(null);
  const dummy = useMemo(() => new THREE.Object3D(), []);

  const particles = useMemo(() => {
    const temp = [];
    for (let i = 0; i < count; i++) {
      const t = Math.random() * 100;
      const factor = 20 + Math.random() * 100;
      const speed = 0.01 + Math.random() / 200;
      const xFactor = -50 + Math.random() * 100;
      const yFactor = -50 + Math.random() * 100;
      const zFactor = -50 + Math.random() * 100;
      temp.push({ t, factor, speed, xFactor, yFactor, zFactor, mx: 0, my: 0 });
    }
    return temp;
  }, [count]);

  const { pointer } = useThree();

  useFrame((state) => {
    particles.forEach((particle, i) => {
      let { t, factor, speed, xFactor, yFactor, zFactor } = particle;
      
      // Interaction with pointer
      particle.t += speed / 2;
      const a = Math.cos(particle.t) + Math.sin(particle.t * 1) / 10;
      const b = Math.sin(particle.t) + Math.cos(particle.t * 2) / 10;
      const s = Math.cos(particle.t);

      // Magnetic effect towards pointer
      particle.mx += (pointer.x * 20 - particle.mx) * 0.02;
      particle.my += (pointer.y * 20 - particle.my) * 0.02;

      dummy.position.set(
        (particle.mx / 10) + a + xFactor + Math.cos((particle.t / 10) * factor) + (Math.sin(particle.t * 1) * factor) / 10,
        (particle.my / 10) + b + yFactor + Math.sin((particle.t / 10) * factor) + (Math.cos(particle.t * 2) * factor) / 10,
        (particle.my / 10) + b + zFactor + Math.cos((particle.t / 10) * factor) + (Math.sin(particle.t * 3) * factor) / 10
      );

      dummy.scale.set(s, s, s);
      dummy.rotation.set(s * 5, s * 5, s * 5);
      dummy.updateMatrix();
      
      if (mesh.current) {
        mesh.current.setMatrixAt(i, dummy.matrix);
      }
    });
    if (mesh.current) {
      mesh.current.instanceMatrix.needsUpdate = true;
    }
  });

  return (
    <instancedMesh ref={mesh} args={[undefined, undefined, count]}>
      <dodecahedronGeometry args={[0.2, 0]} />
      <meshStandardMaterial color="#00D09C" transparent opacity={0.6} roughness={0.1} metalness={0.8} />
    </instancedMesh>
  );
}

export default function Canvas3D() {
  return (
    <div className="fixed inset-0 z-[-1]">
      <Canvas camera={{ position: [0, 0, 15], fov: 60 }} dpr={[1, 2]}>
        <ambientLight intensity={0.5} />
        <CursorLight />
        
        <FloatingBlobs />
        <Particles />
        
        <Environment preset="city" />
      </Canvas>
    </div>
  );
}
