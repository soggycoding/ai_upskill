/**
 * WebGL / 3D Restrained Experiment Prototype
 * Section 23 & 45 Compliance: Restrained, evaluated, graceful fallback.
 * Implements a lightweight wireframe geometric cluster node without external libraries.
 */

class WebGLExperiment {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.gl = this.canvas.getContext('webgl') || this.canvas.getContext('experimental-webgl');
    this.animFrame = null;
    this.rotation = 0;
    this.active = false;
    
    // Check if user prefers reduced motion
    const prefersReducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) {
      this.renderFallback('Reduced motion preferred: 3D canvas disabled.');
      return;
    }

    if (!this.gl) {
      this.renderFallback('WebGL not supported: displaying static architectural view.');
      return;
    }

    this.init();
  }

  init() {
    const gl = this.gl;
    // Simple vertex shader
    const vsSource = `
      attribute vec3 aPosition;
      uniform mat4 uModelView;
      uniform mat4 uProjection;
      void main() {
        gl_Position = uProjection * uModelView * vec4(aPosition, 1.0);
      }
    `;

    // Simple fragment shader
    const fsSource = `
      precision mediump float;
      uniform vec4 uColor;
      void main() {
        gl_FragColor = uColor;
      }
    `;

    const shaderProgram = this.createProgram(vsSource, fsSource);
    if (!shaderProgram) {
      this.renderFallback('Shader initialization failed.');
      return;
    }

    this.programInfo = {
      program: shaderProgram,
      attribLocations: {
        position: gl.getAttribLocation(shaderProgram, 'aPosition'),
      },
      uniformLocations: {
        projection: gl.getUniformLocation(shaderProgram, 'uProjection'),
        modelView: gl.getUniformLocation(shaderProgram, 'uModelView'),
        color: gl.getUniformLocation(shaderProgram, 'uColor'),
      },
    };

    this.buffers = this.initBuffers();
    this.active = true;
    this.render();
  }

  createShader(type, source) {
    const gl = this.gl;
    const shader = gl.createShader(type);
    gl.shaderSource(shader, source);
    gl.compileShader(shader);
    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
      gl.deleteShader(shader);
      return null;
    }
    return shader;
  }

  createProgram(vsSource, fsSource) {
    const gl = this.gl;
    const vs = this.createShader(gl.VERTEX_SHADER, vsSource);
    const fs = this.createShader(gl.FRAGMENT_SHADER, fsSource);
    if (!vs || !fs) return null;

    const program = gl.createProgram();
    gl.attachShader(program, vs);
    gl.attachShader(program, fs);
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return null;
    return program;
  }

  initBuffers() {
    const gl = this.gl;
    // Octahedron wireframe vertices representing a 3D cluster node
    const vertices = [
      // Top pyramid
       0.0,  1.0,  0.0,   1.0,  0.0,  0.0,
       0.0,  1.0,  0.0,   0.0,  0.0,  1.0,
       0.0,  1.0,  0.0,  -1.0,  0.0,  0.0,
       0.0,  1.0,  0.0,   0.0,  0.0, -1.0,
      // Equator
       1.0,  0.0,  0.0,   0.0,  0.0,  1.0,
       0.0,  0.0,  1.0,  -1.0,  0.0,  0.0,
      -1.0,  0.0,  0.0,   0.0,  0.0, -1.0,
       0.0,  0.0, -1.0,   1.0,  0.0,  0.0,
      // Bottom pyramid
       0.0, -1.0,  0.0,   1.0,  0.0,  0.0,
       0.0, -1.0,  0.0,   0.0,  0.0,  1.0,
       0.0, -1.0,  0.0,  -1.0,  0.0,  0.0,
       0.0, -1.0,  0.0,   0.0,  0.0, -1.0,
    ];

    const vertexBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(vertices), gl.STATIC_DRAW);

    return {
      vertex: vertexBuffer,
      count: vertices.length / 3
    };
  }

  render() {
    if (!this.active) return;
    const gl = this.gl;

    // Resize canvas display
    const dpr = window.devicePixelRatio || 1;
    const width = this.canvas.clientWidth * dpr;
    const height = this.canvas.clientHeight * dpr;
    if (this.canvas.width !== width || this.canvas.height !== height) {
      this.canvas.width = width;
      this.canvas.height = height;
    }
    gl.viewport(0, 0, gl.canvas.width, gl.canvas.height);

    gl.clearColor(0.0, 0.0, 0.0, 0.0);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    gl.enable(gl.DEPTH_TEST);

    this.rotation += 0.008;

    // Simple orthographic / perspective matrix simulation
    const aspect = gl.canvas.width / gl.canvas.height;
    const projMatrix = this.makePerspective(45 * Math.PI / 180, aspect, 0.1, 100);
    const modelView = this.makeModelView(this.rotation);

    gl.useProgram(this.programInfo.program);

    gl.bindBuffer(gl.ARRAY_BUFFER, this.buffers.vertex);
    gl.vertexAttribPointer(this.programInfo.attribLocations.position, 3, gl.FLOAT, false, 0, 0);
    gl.enableVertexAttribArray(this.programInfo.attribLocations.position);

    gl.uniformMatrix4fv(this.programInfo.uniformLocations.projection, false, projMatrix);
    gl.uniformMatrix4fv(this.programInfo.uniformLocations.modelView, false, modelView);

    // Color adapts to dark/light theme
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const color = isDark ? [0.22, 0.74, 0.97, 0.75] : [0.01, 0.52, 0.78, 0.65];
    gl.uniform4fv(this.programInfo.uniformLocations.color, color);

    gl.drawArrays(gl.LINES, 0, this.buffers.count);

    this.animFrame = requestAnimationFrame(() => this.render());
  }

  makePerspective(fov, aspect, near, far) {
    const f = Math.tan(Math.PI * 0.5 - 0.5 * fov);
    const rangeInv = 1.0 / (near - far);
    return new Float32Array([
      f / aspect, 0, 0, 0,
      0, f, 0, 0,
      0, 0, (near + far) * rangeInv, -1,
      0, 0, near * far * rangeInv * 2, 0
    ]);
  }

  makeModelView(rot) {
    const c = Math.cos(rot);
    const s = Math.sin(rot);
    // Rotate Y and slight X tilt
    return new Float32Array([
      c, 0, -s, 0,
      s * 0.35, 0.94, c * 0.35, 0,
      s, -0.35, c, 0,
      0, 0, -3.2, 1
    ]);
  }

  renderFallback(msg) {
    if (this.canvas) {
      this.canvas.style.display = 'none';
      const fallbackDiv = document.getElementById('webgl-fallback');
      if (fallbackDiv) {
        fallbackDiv.textContent = msg;
        fallbackDiv.style.display = 'block';
      }
    }
  }

  destroy() {
    this.active = false;
    if (this.animFrame) cancelAnimationFrame(this.animFrame);
  }
}

// Export initialization hook
window.initWebGLExperiment = function (canvasId) {
  return new WebGLExperiment(canvasId);
};
