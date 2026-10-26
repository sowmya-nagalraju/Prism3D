/**
 * Prism3D - Professional Three.js Viewport Engine
 * Features: OrbitControls, dynamic dark/white background switching, 
 * PBR and stylized materials, real-time lighting, and print bed visualizer.
 */

class PrismViewer {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;
    this.currentModel = null;
    this.demoMesh = null;
    this.gridHelper = null;
    this.groundPlane = null;
    this.hemiLight = null;
    this.dirLight = null;
    this.fillLight = null;
    this.loader = new THREE.GLTFLoader();

    this.currentTheme = "dark";
    this.currentMaterialMode = "color";
    this.autoRotate = false;
    this.originalMaterials = new Map();

    this.init();
  }

  init() {
    const width = this.container.clientWidth || 800;
    const height = this.container.clientHeight || 600;

    // 1. Scene
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x0c101a);

    // 2. Camera
    this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 2000);
    this.camera.position.set(110, 140, 180);

    // 3. WebGL Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
    this.renderer.setSize(width, height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.outputEncoding = THREE.sRGBEncoding;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.15;
    this.container.appendChild(this.renderer.domElement);

    // 4. OrbitControls
    this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.dampingFactor = 0.05;
    this.controls.maxPolarAngle = Math.PI / 2 + 0.15;
    this.controls.minDistance = 10;
    this.controls.maxDistance = 1200;

    // 5. Lighting Setup
    this.setupLighting();

    // 6. Build Plate & Grid (200x200mm)
    this.setupPrintBed();

    // 7. Initial Welcome 3D Demo Object (Smooth 3D Prism Logo)
    this.setupInitialDemo();

    // 8. Event Listeners
    window.addEventListener("resize", () => this.onWindowResize());

    // 9. Animation Loop
    this.animate();
  }

  setupLighting() {
    this.hemiLight = new THREE.HemisphereLight(0xffffff, 0x1e293b, 0.8);
    this.hemiLight.position.set(0, 200, 0);
    this.scene.add(this.hemiLight);

    this.dirLight = new THREE.DirectionalLight(0xffffff, 1.1);
    this.dirLight.position.set(160, 260, 160);
    this.dirLight.castShadow = true;
    this.dirLight.shadow.mapSize.width = 2048;
    this.dirLight.shadow.mapSize.height = 2048;
    this.dirLight.shadow.camera.near = 10;
    this.dirLight.shadow.camera.far = 900;
    const d = 150;
    this.dirLight.shadow.camera.left = -d;
    this.dirLight.shadow.camera.right = d;
    this.dirLight.shadow.camera.top = d;
    this.dirLight.shadow.camera.bottom = -d;
    this.dirLight.shadow.bias = -0.0005;
    this.scene.add(this.dirLight);

    this.fillLight = new THREE.DirectionalLight(0x818cf8, 0.45);
    this.fillLight.position.set(-160, 120, -100);
    this.scene.add(this.fillLight);

    const rimLight = new THREE.DirectionalLight(0x38bdf8, 0.5);
    rimLight.position.set(0, -100, -160);
    this.scene.add(rimLight);
  }

  setupPrintBed() {
    if (this.gridHelper) this.scene.remove(this.gridHelper);
    if (this.groundPlane) this.scene.remove(this.groundPlane);

    const isLight = this.currentTheme === "light";
    const centerColor = isLight ? 0x4f46e5 : 0x6366f1;
    const gridColor = isLight ? 0xcbd5e1 : 0x1e273a;
    const plateColor = isLight ? 0xf8fafc : 0x0f1422;

    this.gridHelper = new THREE.GridHelper(200, 20, centerColor, gridColor);
    this.gridHelper.position.y = -0.05;
    this.scene.add(this.gridHelper);

    const groundGeo = new THREE.PlaneGeometry(200, 200);
    const groundMat = new THREE.MeshStandardMaterial({
      color: plateColor,
      roughness: isLight ? 0.9 : 0.8,
      metalness: 0.1
    });
    this.groundPlane = new THREE.Mesh(groundGeo, groundMat);
    this.groundPlane.rotation.x = -Math.PI / 2;
    this.groundPlane.receiveShadow = true;
    this.scene.add(this.groundPlane);
  }

  setupInitialDemo() {
    // Elegant smooth beveled 3D prism crystal on the bed
    const geo = new THREE.CylinderGeometry(25, 38, 22, 6, 1);
    const mat = new THREE.MeshStandardMaterial({
      color: 0x6366f1,
      roughness: 0.25,
      metalness: 0.7,
      wireframe: false
    });
    this.demoMesh = new THREE.Mesh(geo, mat);
    this.demoMesh.position.set(0, 11, 0);
    this.demoMesh.castShadow = true;
    this.demoMesh.receiveShadow = true;
    this.scene.add(this.demoMesh);

    this.controls.autoRotate = true;
    this.controls.autoRotateSpeed = 1.2;
  }

  setTheme(theme) {
    this.currentTheme = theme;
    const isLight = theme === "light";

    this.scene.background = new THREE.Color(isLight ? 0xe2e8f0 : 0x0c101a);

    if (this.hemiLight) {
      this.hemiLight.color.setHex(0xffffff);
      this.hemiLight.groundColor.setHex(isLight ? 0x94a3b8 : 0x1e293b);
      this.hemiLight.intensity = isLight ? 0.95 : 0.8;
    }

    if (this.fillLight) {
      this.fillLight.color.setHex(isLight ? 0x4f46e5 : 0x818cf8);
      this.fillLight.intensity = isLight ? 0.35 : 0.45;
    }

    this.setupPrintBed();
  }

  loadGLB(url) {
    return new Promise((resolve, reject) => {
      // Remove welcome demo mesh if present
      if (this.demoMesh) {
        this.scene.remove(this.demoMesh);
        this.demoMesh = null;
      }

      this.loader.load(
        url,
        (gltf) => {
          if (this.currentModel) {
            this.scene.remove(this.currentModel);
          }

          this.currentModel = gltf.scene;
          this.originalMaterials.clear();

          this.currentModel.traverse((child) => {
            if (child.isMesh) {
              child.castShadow = true;
              child.receiveShadow = true;
              child.geometry.computeVertexNormals();
              this.originalMaterials.set(child, child.material);
            }
          });

          // Orient upright
          this.currentModel.rotation.x = -Math.PI / 2;

          const box = new THREE.Box3().setFromObject(this.currentModel);
          const center = box.getCenter(new THREE.Vector3());
          const size = box.getSize(new THREE.Vector3());

          this.currentModel.position.x = -center.x;
          this.currentModel.position.z = -center.z;
          this.currentModel.position.y = -box.min.y;

          this.scene.add(this.currentModel);

          this.setMaterialMode(this.currentMaterialMode);
          this.fitCameraToModel(size);

          resolve(gltf);
        },
        undefined,
        (err) => {
          console.error("Error loading GLB:", err);
          reject(err);
        }
      );
    });
  }

  fitCameraToModel(size) {
    const maxDim = Math.max(size.x, size.y, size.z);
    const fov = this.camera.fov * (Math.PI / 180);
    let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2)) * 1.8;
    cameraZ = Math.max(cameraZ, 80);

    this.camera.position.set(cameraZ * 0.7, cameraZ * 0.9, cameraZ * 1.1);
    this.controls.target.set(0, size.y / 2, 0);
    this.controls.update();
  }

  setMaterialMode(mode) {
    this.currentMaterialMode = mode;
    if (!this.currentModel) return;

    this.currentModel.traverse((child) => {
      if (!child.isMesh) return;

      if (mode === "color") {
        if (this.originalMaterials.has(child)) {
          child.material = this.originalMaterials.get(child);
          child.material.wireframe = false;
        }
      } else if (mode === "clay") {
        child.material = new THREE.MeshStandardMaterial({
          color: 0xdfdcd5,
          roughness: 0.65,
          metalness: 0.05,
          wireframe: false
        });
      } else if (mode === "gold") {
        child.material = new THREE.MeshStandardMaterial({
          color: 0xffd166,
          roughness: 0.25,
          metalness: 0.85,
          wireframe: false
        });
      } else if (mode === "slicer") {
        child.material = new THREE.MeshStandardMaterial({
          color: 0x06d6a0,
          roughness: 0.4,
          metalness: 0.1,
          wireframe: false
        });
      } else if (mode === "wireframe") {
        child.material = new THREE.MeshStandardMaterial({
          color: 0x6366f1,
          wireframe: true
        });
      }
    });
  }

  setCameraView(view) {
    const targetY = 10;
    this.controls.target.set(0, targetY, 0);

    if (view === "top") {
      this.camera.position.set(0, 240, 0.01);
    } else if (view === "front") {
      this.camera.position.set(0, 25, 220);
    } else if (view === "isometric") {
      this.camera.position.set(130, 140, 160);
    }
    this.controls.update();
  }

  toggleAutoRotate(enable) {
    this.autoRotate = enable !== undefined ? enable : !this.autoRotate;
    this.controls.autoRotate = this.autoRotate;
    this.controls.autoRotateSpeed = 2.0;
  }

  toggleGrid(visible) {
    if (this.gridHelper) this.gridHelper.visible = visible;
    if (this.groundPlane) this.groundPlane.visible = visible;
  }

  onWindowResize() {
    const width = this.container.clientWidth;
    const height = this.container.clientHeight;
    if (width === 0 || height === 0) return;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    if (this.demoMesh && !this.currentModel) {
      this.demoMesh.rotation.y += 0.01;
    }
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }
}
