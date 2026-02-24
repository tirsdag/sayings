const listEl = document.getElementById("list");
const statusEl = document.getElementById("status");
const template = document.getElementById("itemTemplate");
const createForm = document.getElementById("createForm");
const sayingInput = document.getElementById("sayingInput");
const promptInput = document.getElementById("promptInput");
const exportBtn = document.getElementById("exportBtn");
const importFile = document.getElementById("importFile");

const api = {
  async getSayings() {
    return fetch("/api/sayings").then((r) => r.json());
  },
  async create(payload) {
    return fetch("/api/sayings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then((r) => r.json());
  },
  async update(id, payload) {
    return fetch(`/api/sayings/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then((r) => r.json());
  },
  async remove(id) {
    return fetch(`/api/sayings/${id}`, { method: "DELETE" });
  },
  async generate(id) {
    return fetch(`/api/sayings/${id}/generate`, { method: "POST" }).then((r) => r.json());
  },
  async exportData() {
    return fetch("/api/export").then((r) => r.json());
  },
  async importData(payload) {
    return fetch("/api/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then((r) => r.json());
  },
};

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.style.color = isError ? "#8f3030" : "#2f7f5f";
}

function renderItem(item) {
  const node = template.content.firstElementChild.cloneNode(true);
  const sayingEl = node.querySelector(".edit-saying");
  const promptEl = node.querySelector(".edit-prompt");
  const saveBtn = node.querySelector(".save-btn");
  const genBtn = node.querySelector(".gen-btn");
  const delBtn = node.querySelector(".del-btn");
  const previewEl = node.querySelector(".preview");
  const downloadBtn = node.querySelector(".download-btn");

  sayingEl.value = item.saying;
  promptEl.value = item.prompt;

  const applyImage = (path) => {
    if (!path) {
      previewEl.style.display = "none";
      downloadBtn.style.display = "none";
      return;
    }
    const src = `${path}?t=${Date.now()}`;
    previewEl.src = src;
    previewEl.style.display = "block";
    downloadBtn.href = src;
    downloadBtn.download = "saying.png";
    downloadBtn.textContent = "Download";
    downloadBtn.style.display = "inline-block";
  };

  applyImage(item.image_path);

  saveBtn.addEventListener("click", async () => {
    try {
      const updated = await api.update(item.id, {
        saying: sayingEl.value.trim(),
        prompt: promptEl.value.trim(),
      });
      item = updated;
      setStatus(`Saved #${item.id}`);
    } catch {
      setStatus("Save failed", true);
    }
  });

  genBtn.addEventListener("click", async () => {
    try {
      genBtn.disabled = true;
      const updated = await api.generate(item.id);
      item = updated;
      applyImage(item.image_path);
      setStatus(`Generated image for #${item.id}`);
    } catch {
      setStatus("Generation failed", true);
    } finally {
      genBtn.disabled = false;
    }
  });

  delBtn.addEventListener("click", async () => {
    try {
      await api.remove(item.id);
      node.remove();
      setStatus(`Deleted #${item.id}`);
    } catch {
      setStatus("Delete failed", true);
    }
  });

  return node;
}

async function refresh() {
  listEl.innerHTML = "";
  const items = await api.getSayings();
  for (const item of items) {
    listEl.append(renderItem(item));
  }
}

createForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await api.create({
      saying: sayingInput.value.trim(),
      prompt: promptInput.value.trim(),
    });
    sayingInput.value = "";
    promptInput.value = "";
    await refresh();
    setStatus("Created saying");
  } catch {
    setStatus("Create failed", true);
  }
});

exportBtn.addEventListener("click", async () => {
  try {
    const payload = await api.exportData();
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "sayings-export.json";
    a.click();
    URL.revokeObjectURL(url);
    setStatus("Exported sayings");
  } catch {
    setStatus("Export failed", true);
  }
});

importFile.addEventListener("change", async () => {
  const file = importFile.files?.[0];
  if (!file) return;

  try {
    const text = await file.text();
    const payload = JSON.parse(text);
    if (!Array.isArray(payload.sayings)) {
      throw new Error("Invalid format");
    }
    await api.importData(payload);
    await refresh();
    setStatus("Imported sayings");
  } catch {
    setStatus("Import failed", true);
  } finally {
    importFile.value = "";
  }
});

refresh();
