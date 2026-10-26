/**
 * Prism3D Pro Studio - Application Controller
 * Handles dual theme switching (Dark & White background), preset loading,
 * drag-and-drop uploads, parameter bindings, 3D conversion, and multi-format exports.
 */

(function () {
  if (window.__PRISM_APP_INITIALIZED__) return;
  window.__PRISM_APP_INITIALIZED__ = true;

  document.addEventListener("DOMContentLoaded", () => {
    // 1. Initialize 3D Viewport
    const viewer = new PrismViewer("three-canvas-container");

    // DOM Elements - Theme
    const themeBtn = document.getElementById("theme-toggle-btn");
    const themeIcon = document.getElementById("theme-icon");
    const themeText = document.getElementById("theme-text");

    // Theme Management
    let currentTheme = localStorage.getItem("prism3d_theme") || "dark";
    applyTheme(currentTheme);

    themeBtn.addEventListener("click", () => {
      currentTheme = currentTheme === "dark" ? "light" : "dark";
      applyTheme(currentTheme);
      localStorage.setItem("prism3d_theme", currentTheme);
    });

    function applyTheme(theme) {
      document.documentElement.setAttribute("data-theme", theme);
      if (theme === "dark") {
        themeIcon.textContent = "☀️";
        themeText.textContent = "Light Mode";
      } else {
        themeIcon.textContent = "🌙";
        themeText.textContent = "Dark Mode";
      }
      viewer.setTheme(theme);
    }

    // DOM Elements - Inputs & Uploads
    const dropzone = document.getElementById("dropzone");
    const fileInput = document.getElementById("file-input");
    const browseBtn = document.getElementById("browse-btn");
    const previewContainer = document.getElementById("preview-container");
    const previewImg = document.getElementById("preview-img");
    const previewName = document.getElementById("preview-name");
    const removeImgBtn = document.getElementById("remove-img-btn");
    const sampleGrid = document.getElementById("sample-grid");
    const convertBtn = document.getElementById("convert-btn");
    const convertBtnText = document.getElementById("convert-btn-text");
    const loadingOverlay = document.getElementById("loading-overlay");
    const loadingSubtext = document.getElementById("loading-subtext");

    // Sliders & Values
    const heightSlider = document.getElementById("slider-height");
    const heightVal = document.getElementById("val-height");
    const baseSlider = document.getElementById("slider-base");
    const baseVal = document.getElementById("val-base");
    const widthSlider = document.getElementById("slider-width");
    const widthVal = document.getElementById("val-width");
    const smoothSlider = document.getElementById("slider-smooth");
    const smoothVal = document.getElementById("val-smooth");
    const resSelect = document.getElementById("select-resolution");
    const toggleInvert = document.getElementById("toggle-invert");
    const toggleDual = document.getElementById("toggle-dual");
    const toggleCurve = document.getElementById("toggle-curve");

    // Stats Elements
    const statStatus = document.getElementById("stat-status");
    const statVertices = document.getElementById("stat-vertices");
    const statTriangles = document.getElementById("stat-triangles");
    const statDims = document.getElementById("stat-dims");
    const statVolume = document.getElementById("stat-volume");

    // State Variables
    let currentFile = null;
    let currentBase64 = null;
    let activeSampleId = null;
    let activeMode = "anime_cartoon";
    let activeModelId = null;

    // 2. Slider Value Sync
    heightSlider.addEventListener("input", (e) => (heightVal.textContent = `${e.target.value}mm`));
    baseSlider.addEventListener("input", (e) => (baseVal.textContent = `${e.target.value}mm`));
    widthSlider.addEventListener("input", (e) => (widthVal.textContent = `${e.target.value}mm`));
    smoothSlider.addEventListener("input", (e) => (smoothVal.textContent = `${e.target.value}x`));

    // 3. Conversion Profile Cards
    const profileCards = document.querySelectorAll(".profile-card");
    profileCards.forEach((card) => {
      card.addEventListener("click", () => {
        profileCards.forEach((c) => c.classList.remove("active"));
        card.classList.add("active");
        activeMode = card.dataset.mode;
      });
    });

    function selectMode(mode) {
      activeMode = mode;
      profileCards.forEach((card) => {
        if (card.dataset.mode === mode) {
          card.classList.add("active");
        } else {
          card.classList.remove("active");
        }
      });
    }

    // 4. Viewport Material Mode Buttons
    const matBtns = document.querySelectorAll(".vp-tool-btn[data-material]");
    matBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        matBtns.forEach((b) => b.classList.remove("active"));
        btn.classList.add("active");
        viewer.setMaterialMode(btn.dataset.material);
      });
    });

    // 5. Camera View Buttons
    const viewBtns = document.querySelectorAll(".vp-tool-btn[data-view]");
    viewBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        viewer.setCameraView(btn.dataset.view);
      });
    });

    // 6. Turntable & Grid Toggles
    const btnTurntable = document.getElementById("btn-turntable");
    btnTurntable.addEventListener("click", () => {
      const isRotating = btnTurntable.classList.toggle("active");
      viewer.toggleAutoRotate(isRotating);
    });

    const btnGrid = document.getElementById("btn-grid");
    btnGrid.addEventListener("click", () => {
      const isGrid = btnGrid.classList.toggle("active");
      viewer.toggleGrid(isGrid);
    });

    // 7. File Upload & Dropzone
    dropzone.addEventListener("click", () => fileInput.click());
    if (browseBtn) {
      browseBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        fileInput.click();
      });
    }

    dropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });

    dropzone.addEventListener("dragleave", () => {
      dropzone.classList.remove("dragover");
    });

    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleUserFile(e.dataTransfer.files[0]);
      }
    });

    fileInput.addEventListener("change", (e) => {
      if (e.target.files && e.target.files[0]) {
        handleUserFile(e.target.files[0]);
      }
    });

    // Paste from clipboard support (Ctrl + V)
    window.addEventListener("paste", (e) => {
      if (e.clipboardData && e.clipboardData.files && e.clipboardData.files.length > 0) {
        const item = e.clipboardData.files[0];
        if (item.type.startsWith("image/")) {
          handleUserFile(item);
        }
      }
    });

    removeImgBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      resetUploadedImage();
    });

    function handleUserFile(file) {
      if (!file.type.startsWith("image/")) {
        alert("Please upload a valid image file (PNG, JPG, WEBP, BMP).");
        return;
      }

      currentFile = file;
      activeSampleId = null;

      // Deselect preset cards
      document.querySelectorAll(".preset-card").forEach((c) => c.classList.remove("active"));

      // Read file both for preview and guaranteed base64 transmission
      const reader = new FileReader();
      reader.onload = (evt) => {
        currentBase64 = evt.target.result;
        previewImg.src = currentBase64;
        if (previewName) previewName.textContent = file.name;
        previewContainer.style.display = "block";
        dropzone.style.display = "none";
        convertBtnText.textContent = "⚡ Generate 3D Model";
      };
      reader.readAsDataURL(file);

      // Smart Profile Auto-Detection
      const fn = file.name.toLowerCase();
      if (fn.includes("blueprint") || fn.includes("plan") || fn.includes("cad") || fn.includes("schematic")) {
        selectMode("blueprint");
      } else if (fn.includes("sketch") || fn.includes("pencil") || fn.includes("drawing") || fn.includes("line")) {
        selectMode("sketch_lineart");
      } else if (fn.includes("anime") || fn.includes("cartoon") || fn.includes("chibi") || fn.includes("manga")) {
        selectMode("anime_cartoon");
      }
    }

    function resetUploadedImage() {
      currentFile = null;
      currentBase64 = null;
      activeSampleId = null;
      fileInput.value = "";
      previewImg.src = "";
      previewContainer.style.display = "none";
      dropzone.style.display = "block";
      document.querySelectorAll(".preset-card").forEach((c) => c.classList.remove("active"));
      convertBtnText.textContent = "⚡ Select or Upload Image to Convert";
    }

    // 8. Built-in Preset Showcase (NO auto-conversion on page load!)
    async function loadPresets() {
      try {
        const res = await fetch("/api/samples");
        const samples = await res.json();

        sampleGrid.innerHTML = "";
        samples.forEach((sample) => {
          const card = document.createElement("div");
          card.className = "preset-card";

          card.innerHTML = `
            <div class="preset-thumb-wrap">
              <img class="preset-thumb" src="${sample.image}" alt="${sample.name}">
            </div>
            <div class="preset-title">${sample.name}</div>
            <div class="preset-category">${sample.category}</div>
          `;

          card.addEventListener("click", () => {
            document.querySelectorAll(".preset-card").forEach((c) => c.classList.remove("active"));
            card.classList.add("active");

            activeSampleId = sample.id;
            currentFile = null;

            previewImg.src = sample.image;
            if (previewName) previewName.textContent = sample.name;
            previewContainer.style.display = "block";
            dropzone.style.display = "none";

            selectMode(sample.mode);
            heightSlider.value = sample.height;
            heightVal.textContent = `${sample.height}mm`;
            baseSlider.value = sample.base;
            baseVal.textContent = `${sample.base}mm`;
            widthSlider.value = sample.width;
            widthVal.textContent = `${sample.width}mm`;
            smoothSlider.value = sample.smoothness;
            smoothVal.textContent = `${sample.smoothness}x`;

            convertBtnText.textContent = `⚡ Generate 3D (${sample.name})`;
            performConversion();
          });

          sampleGrid.appendChild(card);
        });

      } catch (err) {
        console.error("Failed to load presets:", err);
      }
    }

    // 9. Convert Execution
    convertBtn.addEventListener("click", () => performConversion());

    async function performConversion() {
      if (!currentFile && !activeSampleId) {
        alert("Please upload an image first using the box above, or click one of the quick presets!");
        return;
      }

      loadingOverlay.style.display = "flex";
      convertBtn.classList.add("loading");
      loadingSubtext.textContent = "Estimating depth, smoothing surfaces, and constructing watertight solid...";

      const formData = new FormData();
      if (currentFile) {
        formData.append("file", currentFile);
      }
      if (currentBase64) {
        formData.append("image_base64", currentBase64);
      }
      if (activeSampleId) {
        formData.append("sample_id", activeSampleId);
      }

      formData.append("mode", activeMode);
      formData.append("width_mm", widthSlider.value);
      formData.append("max_height_mm", heightSlider.value);
      formData.append("base_thickness_mm", baseSlider.value);
      formData.append("smoothness", smoothSlider.value);
      formData.append("resolution", resSelect.value);
      formData.append("invert", toggleInvert.checked);
      formData.append("dual_sided", toggleDual.checked);
      formData.append("curve_arc_deg", toggleCurve.checked ? 60.0 : 0.0);

      try {
        const res = await fetch("/api/convert", {
          method: "POST",
          body: formData
        });

        if (!res.ok) {
          const errorData = await res.json();
          throw new Error(errorData.detail || "Conversion failed");
        }

        const data = await res.json();
        activeModelId = data.model_id;

        // Diagnostics Card Update
        statStatus.innerHTML = `
          <span class="health-badge">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
            100% Watertight
          </span>`;
        statVertices.textContent = data.stats.vertices.toLocaleString();
        statTriangles.textContent = data.stats.triangles.toLocaleString();
        statDims.textContent = `${data.stats.width_mm} × ${data.stats.length_mm} × ${data.stats.height_mm} mm`;
        statVolume.textContent = `${data.stats.volume_cm3} cm³`;

        // Load 3D Model into Viewport
        loadingSubtext.textContent = "Loading 3D model into interactive viewport...";
        await viewer.loadGLB(data.glb_url);

      } catch (err) {
        console.error("Conversion error:", err);
        alert(`Error during 3D conversion: ${err.message}`);
      } finally {
        loadingOverlay.style.display = "none";
        convertBtn.classList.remove("loading");
      }
    }

    // 10. Multi-Format Downloads
    const exportBtns = document.querySelectorAll(".export-card-btn[data-format]");
    exportBtns.forEach((btn) => {
      btn.addEventListener("click", () => {
        if (!activeModelId) {
          alert("Please generate a 3D model first by uploading an image!");
          return;
        }
        const fmt = btn.dataset.format;
        window.location.href = `/api/download/${activeModelId}/${fmt}`;
      });
    });

    // Start preset list (without auto-converting!)
    loadPresets();
  });
})();
