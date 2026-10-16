import { useEffect, useRef } from "react";
import * as THREE from "three";

/** Slow-floating glossy 3D shapes behind the page. Pauses when the tab is hidden. */
export default function Background3D({ theme }: { theme: "light" | "dark" }) {
  const host = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = host.current;
    if (!el) return;
    let renderer: THREE.WebGLRenderer;
    try {
      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "low-power" });
    } catch {
      return; // no WebGL: the page still works, just without the shapes
    }
    const dark = theme === "dark";
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    el.appendChild(renderer.domElement);

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(42, window.innerWidth / window.innerHeight, 0.1, 100);
    camera.position.set(0, 0, 14);

    scene.add(new THREE.HemisphereLight(0xffffff, dark ? 0x0a0a0a : 0xdfe7e3, dark ? 0.9 : 1.4));
    const key = new THREE.DirectionalLight(0xffffff, dark ? 2.2 : 2.6);
    key.position.set(5, 8, 10);
    scene.add(key);
    const rim = new THREE.PointLight(0xe0115f, dark ? 40 : 18, 30);
    rim.position.set(-8, -4, 6);
    scene.add(rim);

    const seaGreen = new THREE.MeshPhysicalMaterial({ color: 0x2e8b57, metalness: 0.35, roughness: 0.22, clearcoat: 1, clearcoatRoughness: 0.15 });
    const ruby = new THREE.MeshPhysicalMaterial({ color: 0x9b111e, metalness: 0.4, roughness: 0.2, clearcoat: 1, clearcoatRoughness: 0.1 });
    const mono = new THREE.MeshPhysicalMaterial({ color: dark ? 0x2a2a2a : 0xffffff, metalness: 0.15, roughness: 0.35, clearcoat: 0.8 });
    const glass = new THREE.MeshPhysicalMaterial({ color: 0x3cb371, transmission: 0.9, thickness: 1.2, roughness: 0.08, ior: 1.4, transparent: true, opacity: 0.85 });

    type Shape = { mesh: THREE.Mesh; spin: THREE.Vector3; base: THREE.Vector3; phase: number };
    const shapes: Shape[] = [];
    const add = (geo: THREE.BufferGeometry, mat: THREE.Material, pos: [number, number, number], scale: number) => {
      const mesh = new THREE.Mesh(geo, mat);
      mesh.position.set(...pos);
      mesh.scale.setScalar(scale);
      mesh.rotation.set(Math.random() * 3, Math.random() * 3, 0);
      scene.add(mesh);
      shapes.push({
        mesh,
        base: mesh.position.clone(),
        phase: Math.random() * Math.PI * 2,
        spin: new THREE.Vector3(0.1 + Math.random() * 0.15, 0.12 + Math.random() * 0.15, 0),
      });
    };

    add(new THREE.TorusKnotGeometry(1, 0.32, 160, 24), seaGreen, [8.6, 3.9, -4], 0.9);
    add(new THREE.IcosahedronGeometry(1.2, 0), ruby, [-9.4, -3.6, -3], 0.75);
    add(new THREE.TorusGeometry(1, 0.34, 32, 80), mono, [-9.6, 5.1, -6], 0.75);
    add(new THREE.SphereGeometry(1, 48, 48), glass, [8.2, -4.8, -4], 0.7);
    add(new THREE.OctahedronGeometry(0.8, 0), seaGreen, [-1, -7, -9], 0.7);
    add(new THREE.SphereGeometry(0.45, 32, 32), ruby, [3.8, 6.4, -8], 0.8);

    const mouse = { x: 0, y: 0 };
    const onMove = (e: PointerEvent) => {
      mouse.x = e.clientX / window.innerWidth - 0.5;
      mouse.y = e.clientY / window.innerHeight - 0.5;
    };
    const onResize = () => {
      camera.aspect = window.innerWidth / window.innerHeight;
      // narrow screens: pull the camera back so shapes stay at the edges
      camera.position.z = window.innerWidth < 700 ? 19 : 14;
      camera.updateProjectionMatrix();
      renderer.setSize(window.innerWidth, window.innerHeight);
    };
    onResize();
    window.addEventListener("pointermove", onMove);
    window.addEventListener("resize", onResize);

    const clock = new THREE.Clock();
    let frame = 0;
    const render = () => {
      const t = clock.getElapsedTime();
      for (const s of shapes) {
        s.mesh.rotation.x += s.spin.x * 0.01;
        s.mesh.rotation.y += s.spin.y * 0.01;
        s.mesh.position.y = s.base.y + Math.sin(t * 0.5 + s.phase) * 0.35;
      }
      camera.position.x += (mouse.x * 1.2 - camera.position.x) * 0.03;
      camera.position.y += (-mouse.y * 0.8 - camera.position.y) * 0.03;
      camera.lookAt(0, 0, 0);
      renderer.render(scene, camera);
      frame = requestAnimationFrame(render);
    };
    const onVisibility = () => {
      cancelAnimationFrame(frame);
      if (!document.hidden && !reduce) frame = requestAnimationFrame(render);
    };
    document.addEventListener("visibilitychange", onVisibility);
    if (reduce) renderer.render(scene, camera);
    else frame = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("resize", onResize);
      document.removeEventListener("visibilitychange", onVisibility);
      scene.traverse((o) => {
        if (o instanceof THREE.Mesh) o.geometry.dispose();
      });
      [seaGreen, ruby, mono, glass].forEach((m) => m.dispose());
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, [theme]);

  return <div className="bg3d" ref={host} aria-hidden="true" />;
}
