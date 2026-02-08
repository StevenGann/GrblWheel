<template>
  <div class="app">
    <header class="header">
      <h1>GrblWheel</h1>
      <span class="status" :class="{ connected: serial.connected }">
        {{ serial.connected ? `Connected ${serial.port}` : "Disconnected" }}
      </span>
    </header>

    <section class="connection panel">
      <h2>Connection</h2>
      <div class="row">
        <select v-model="selectedPort" :disabled="serial.connected">
          <option value="">Select port</option>
          <option v-for="p in ports" :key="p.port" :value="p.port">{{ p.port }} – {{ p.description }}</option>
        </select>
        <input v-model.number="baud" type="number" class="baud" placeholder="115200" :disabled="serial.connected" />
      </div>
      <div class="row">
        <button class="btn primary" :disabled="!selectedPort || serial.connected" @click="connect">Connect</button>
        <button class="btn" :disabled="!serial.connected" @click="disconnect">Disconnect</button>
        <button class="btn small" @click="refreshPorts">Refresh</button>
      </div>
    </section>

    <section class="command panel">
      <h2>G-code</h2>
      <div class="row">
        <input
          v-model="command"
          type="text"
          class="command-input"
          placeholder="Type G-code and press Enter"
          :disabled="!serial.connected"
          @keydown.enter="sendCommand"
        />
        <button class="btn primary" :disabled="!serial.connected || !command.trim()" @click="sendCommand">Send</button>
      </div>
      <div v-if="lastResponse" class="response" :class="{ error: lastError }">{{ lastResponse }}</div>
    </section>

    <section class="files panel">
      <h2>G-code files</h2>
      <div class="row">
        <input type="file" ref="fileInput" accept=".gcode,.nc,.ngc,.txt" style="display:none" @change="onFileSelected" />
        <button class="btn small" @click="fileInput?.click()">Upload</button>
        <button class="btn small" @click="refreshFiles">Refresh</button>
      </div>
      <ul class="file-list">
        <li v-for="f in files" :key="f.name" class="file-item" :class="{ selected: selectedFile === f.name }">
          <span class="file-name" @click="selectedFile = f.name">{{ f.name }}</span>
          <span class="file-size">{{ formatSize(f.size) }}</span>
          <button class="btn tiny" :disabled="!serial.connected || job.state === 'running'" @click="startJob(f.name, 1)">Run</button>
          <button class="btn tiny" @click="deleteFile(f.name)">Del</button>
        </li>
        <li v-if="!files.length" class="muted">No files. Upload a .gcode file.</li>
      </ul>
      <div v-if="selectedFile" class="row start-line">
        <label>Start at line:</label>
        <input v-model.number="startLine" type="number" min="1" class="num" />
        <button class="btn primary" :disabled="!serial.connected || job.state === 'running'" @click="startJob(selectedFile, startLine)">Run {{ selectedFile }}</button>
      </div>
    </section>

    <section class="job panel">
      <h2>Job</h2>
      <div class="job-status">
        <span>{{ job.filename || 'Idle' }}</span>
        <span v-if="job.total_lines"> Line {{ job.current_line }} / {{ job.total_lines }}</span>
        <span class="state" :class="job.state"> ({{ job.state }})</span>
        <span v-if="job.error_message" class="error-msg"> {{ job.error_message }}</span>
      </div>
      <div class="button-row">
        <button class="btn primary" :disabled="!serial.connected || job.state === 'running' || !selectedFile" @click="startJob(selectedFile, startLine)">Start</button>
        <button class="btn" :disabled="job.state !== 'running' && job.state !== 'paused'" @click="jobPause">Pause</button>
        <button class="btn" :disabled="job.state !== 'paused'" @click="jobResume">Resume</button>
        <button class="btn" :disabled="job.state !== 'running' && job.state !== 'paused'" @click="jobStop">Stop</button>
      </div>
    </section>

    <section class="quick panel">
      <h2>Quick actions</h2>
      <div class="button-row">
        <button class="btn action" :disabled="!serial.connected" @click="runMacro('zero_xy')">Zero X/Y</button>
        <button class="btn action" :disabled="!serial.connected" @click="runMacro('zero_z')">Zero Z</button>
        <button class="btn action" :disabled="!serial.connected" @click="runMacro('z_probe')">Z Probe</button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";

const API = "/api";
const WS_BASE = (location.origin.replace(/^http/, "ws") + API).replace("/api", "") + API;

const ports = ref([]);
const selectedPort = ref("");
const baud = ref(115200);
const serial = ref({ connected: false, port: null });
const command = ref("");
const lastResponse = ref("");
const lastError = ref(false);
const files = ref([]);
const fileInput = ref(null);
const selectedFile = ref("");
const startLine = ref(1);
const job = ref({ state: "idle", filename: "", current_line: 0, total_lines: 0, error_message: "" });
let jobWs = null;

async function refreshPorts() {
  const r = await fetch(`${API}/serial/ports`);
  const d = await r.json();
  ports.value = d.ports || [];
}

async function fetchState() {
  const r = await fetch(`${API}/serial/state`);
  const d = await r.json();
  serial.value = {
    connected: d.connected,
    port: d.port,
    baud: d.baud,
  };
  lastResponse.value = d.last_error || d.last_response || "";
  lastError.value = !!d.last_error;
}

async function connect() {
  await fetch(`${API}/serial/connect`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ port: selectedPort.value, baud: baud.value || 115200 }),
  });
  await fetchState();
}

async function disconnect() {
  await fetch(`${API}/serial/disconnect`, { method: "POST" });
  await fetchState();
}

async function sendCommand() {
  const cmd = command.value.trim();
  if (!cmd) return;
  const r = await fetch(`${API}/serial/send`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ command: cmd }),
  });
  const d = await r.json();
  lastResponse.value = d.response ?? d.error ?? "";
  lastError.value = !d.ok;
  if (d.ok) command.value = "";
  await fetchState();
}

async function runMacro(name) {
  const r = await fetch(`${API}/macros/${name}/run`, { method: "POST" });
  const d = await r.json().catch(() => ({}));
  lastResponse.value = d.message ?? (r.ok ? "OK" : "Error");
  lastError.value = !r.ok;
  await fetchState();
}

async function refreshFiles() {
  const r = await fetch(`${API}/files`);
  const d = await r.json();
  files.value = d.files || [];
}

async function onFileSelected(ev) {
  const file = ev.target?.files?.[0];
  if (!file) return;
  const form = new FormData();
  form.append("file", file);
  const r = await fetch(`${API}/files/upload`, { method: "POST", body: form });
  if (r.ok) await refreshFiles();
  ev.target.value = "";
}

function formatSize(n) {
  if (n < 1024) return n + " B";
  if (n < 1024 * 1024) return (n / 1024).toFixed(1) + " KB";
  return (n / (1024 * 1024)).toFixed(1) + " MB";
}

async function startJob(filename, line) {
  if (!filename) return;
  const r = await fetch(`${API}/job/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ filename, start_line: line ?? startLine.value ?? 1 }),
  });
  const d = await r.json();
  if (!d.ok) lastResponse.value = d.error || "Failed";
}

async function deleteFile(name) {
  if (!confirm(`Delete ${name}?`)) return;
  await fetch(`${API}/files/${encodeURIComponent(name)}`, { method: "DELETE" });
  await refreshFiles();
  if (selectedFile.value === name) selectedFile.value = "";
}

async function jobPause() {
  await fetch(`${API}/job/pause`, { method: "POST" });
}
async function jobResume() {
  await fetch(`${API}/job/resume`, { method: "POST" });
}
async function jobStop() {
  await fetch(`${API}/job/stop`, { method: "POST" });
}

function connectJobWs() {
  const proto = location.protocol === "https:" ? "wss:" : "ws:";
  const url = `${proto}//${location.host}${API}/job/ws`;
  jobWs = new WebSocket(url);
  jobWs.onmessage = (e) => {
    try {
      const d = JSON.parse(e.data);
      if (d.type === "progress") {
        job.value = {
          state: d.state || "idle",
          filename: d.filename || "",
          current_line: d.current_line ?? 0,
          total_lines: d.total_lines ?? 0,
          error_message: d.error_message || "",
        };
      }
    } catch (_) {}
  };
  jobWs.onclose = () => {
    setTimeout(connectJobWs, 3000);
  };
}

onMounted(async () => {
  await refreshPorts();
  await fetchState();
  await refreshFiles();
  const r = await fetch(`${API}/job/status`);
  const d = await r.json();
  job.value = { state: d.state || "idle", filename: d.filename || "", current_line: d.current_line ?? 0, total_lines: d.total_lines ?? 0, error_message: d.error_message || "" };
  connectJobWs();
});
onUnmounted(() => {
  if (jobWs) jobWs.close();
});
</script>

<style scoped>
.app {
  padding: 12px;
  max-width: 854px;
  margin: 0 auto;
  min-height: 100vh;
}
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #333;
}
.header h1 { margin: 0; font-size: 1.5rem; }
.status { font-size: 0.9rem; color: #888; }
.status.connected { color: #6b9; }
.panel {
  background: #252525;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}
.panel h2 { margin: 0 0 10px 0; font-size: 1rem; color: #aaa; }
.row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: 8px; }
.row:last-child { margin-bottom: 0; }
select { flex: 1; min-width: 180px; padding: 10px 12px; font-size: 1rem; background: #1a1a1a; color: #e0e0e0; border: 1px solid #444; border-radius: 6px; }
.baud { width: 90px; padding: 10px; font-size: 1rem; background: #1a1a1a; color: #e0e0e0; border: 1px solid #444; border-radius: 6px; }
.command-input { flex: 1; min-width: 200px; padding: 12px; font-size: 1rem; font-family: monospace; background: #1a1a1a; color: #e0e0e0; border: 1px solid #444; border-radius: 6px; }
.btn {
  padding: 10px 16px;
  font-size: 1rem;
  background: #333;
  color: #e0e0e0;
  border: 1px solid #555;
  border-radius: 6px;
  cursor: pointer;
  min-height: 44px;
}
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn.primary { background: #2a5; color: #111; border-color: #3b6; }
.btn.small { padding: 8px 12px; font-size: 0.9rem; min-height: 36px; }
.btn.action { min-width: 100px; }
.button-row { display: flex; gap: 8px; flex-wrap: wrap; }
.response { margin-top: 8px; padding: 8px; font-family: monospace; font-size: 0.9rem; background: #1a1a1a; border-radius: 4px; color: #8c8; }
.response.error { color: #c66; }
.file-list { list-style: none; margin: 0; padding: 0; }
.file-item { display: flex; align-items: center; gap: 8px; padding: 6px 0; border-bottom: 1px solid #333; }
.file-item.selected .file-name { color: #6b9; }
.file-name { flex: 1; overflow: hidden; text-overflow: ellipsis; cursor: pointer; }
.file-size { color: #888; font-size: 0.9rem; }
.btn.tiny { padding: 4px 8px; font-size: 0.8rem; min-height: 28px; }
.muted { color: #666; padding: 8px 0; }
.start-line { margin-top: 8px; }
.num { width: 70px; padding: 8px; }
.job-status { margin-bottom: 8px; font-family: monospace; }
.job-status .state.running { color: #6b9; }
.job-status .state.paused { color: #c96; }
.job-status .state.error { color: #c66; }
.job-status .state.done { color: #8c8; }
.error-msg { color: #c66; }
</style>
