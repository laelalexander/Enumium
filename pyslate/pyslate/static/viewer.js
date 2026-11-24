// Small 3D preview for each part on the quote page: one STL, orbit to look around.
import * as THREE from 'three';
import { STLLoader } from './vendor/three/STLLoader.js';
import { OrbitControls } from './vendor/three/OrbitControls.js';

function mount(el) {
  const w = el.clientWidth || 240;
  const h = el.clientHeight || 200;
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(w, h);
  el.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.add(new THREE.HemisphereLight(0xffffff, 0x8899aa, 2.2));
  const sun = new THREE.DirectionalLight(0xffffff, 1.4);
  sun.position.set(1, 2, 3);
  scene.add(sun);
  const camera = new THREE.PerspectiveCamera(40, w / h, 0.1, 10000);
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;

  new STLLoader().load(el.dataset.src, (geometry) => {
    geometry.computeVertexNormals();
    geometry.center();
    geometry.computeBoundingSphere();
    const r = geometry.boundingSphere.radius || 1;
    const mesh = new THREE.Mesh(geometry, new THREE.MeshStandardMaterial({ color: 0x3b82f6, roughness: 0.55, metalness: 0.05 }));
    mesh.rotation.x = -Math.PI / 2; // models are Z-up; the viewer is Y-up
    scene.add(mesh);
    camera.position.set(r * 1.6, r * 1.2, r * 2.2);
    camera.near = r / 100;
    camera.far = r * 100;
    camera.updateProjectionMatrix();
    controls.update();
  }, undefined, () => { el.textContent = 'Preview unavailable'; });

  (function loop() {
    controls.update();
    renderer.render(scene, camera);
    requestAnimationFrame(loop);
  })();
}

document.querySelectorAll('.viewer[data-src]').forEach(mount);
