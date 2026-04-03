const form = document.getElementById("analyze-form");
const fileInput = document.getElementById("file-input");
const fileTypeSelect = document.getElementById("file-type");
const apiKeyInput = document.getElementById("api-key");
const uploadBox = document.getElementById("upload-box");
const submitButton = document.getElementById("submit-button");
const statusPill = document.getElementById("status-pill");
const summaryOutput = document.getElementById("summary-output");
const jsonOutput = document.getElementById("json-output");
const sentimentBadge = document.getElementById("sentiment-badge");
const copyJsonButton = document.getElementById("copy-json");

const entityListIds = {
  names: "names-list",
  dates: "dates-list",
  organizations: "organizations-list",
  amounts: "amounts-list",
};

function setStatus(label, state) {
  statusPill.textContent = label;
  statusPill.className = `status-pill ${state}`;
}

function updateEntityList(key, values) {
  const list = document.getElementById(entityListIds[key]);
  list.innerHTML = "";

  const items = Array.isArray(values) && values.length ? values : ["No data found"];
  items.forEach((value) => {
    const item = document.createElement("li");
    item.textContent = value;
    list.appendChild(item);
  });
}

function setSentimentBadge(sentiment) {
  const value = sentiment || "Neutral";
  sentimentBadge.textContent = value;
  sentimentBadge.className = `sentiment-badge ${value.toLowerCase()}`;
}

function detectFileType(fileName) {
  const lower = fileName.toLowerCase();
  if (lower.endsWith(".pdf")) {
    return "pdf";
  }
  if (lower.endsWith(".docx")) {
    return "docx";
  }
  return "image";
}

function fileToBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || "");
      const parts = result.split(",", 2);
      resolve(parts.length === 2 ? parts[1] : result);
    };
    reader.onerror = () => reject(new Error("Could not read the selected file."));
    reader.readAsDataURL(file);
  });
}

function renderResponse(payload) {
  summaryOutput.textContent = payload.summary || "No summary returned.";
  setSentimentBadge(payload.sentiment);

  const entities = payload.entities || {};
  updateEntityList("names", entities.names);
  updateEntityList("dates", entities.dates);
  updateEntityList("organizations", entities.organizations);
  updateEntityList("amounts", entities.amounts);

  jsonOutput.textContent = JSON.stringify(payload, null, 2);
}

function renderError(message, payload = null) {
  summaryOutput.textContent = message;
  setSentimentBadge("Neutral");
  updateEntityList("names", []);
  updateEntityList("dates", []);
  updateEntityList("organizations", []);
  updateEntityList("amounts", []);
  jsonOutput.textContent = JSON.stringify(
    payload || { status: "error", message },
    null,
    2,
  );
}

["dragenter", "dragover"].forEach((eventName) => {
  uploadBox.addEventListener(eventName, (event) => {
    event.preventDefault();
    uploadBox.classList.add("dragging");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  uploadBox.addEventListener(eventName, (event) => {
    event.preventDefault();
    uploadBox.classList.remove("dragging");
  });
});

fileInput.addEventListener("change", () => {
  const file = fileInput.files?.[0];
  if (!file) {
    return;
  }
  fileTypeSelect.value = detectFileType(file.name);
  setStatus(`Selected ${file.name}`, "idle");
});

copyJsonButton.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(jsonOutput.textContent);
    setStatus("JSON copied", "success");
  } catch {
    setStatus("Copy failed", "error");
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const file = fileInput.files?.[0];
  const apiKey = apiKeyInput.value.trim();
  if (!file) {
    setStatus("Choose a file first", "error");
    return;
  }

  if (!apiKey) {
    setStatus("Enter the API key", "error");
    return;
  }

  submitButton.disabled = true;
  setStatus("Analyzing...", "running");

  try {
    const payload = {
      fileName: file.name,
      fileType: fileTypeSelect.value,
      fileBase64: await fileToBase64(file),
    };

    const response = await fetch("/api/document-analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-api-key": apiKey,
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.message || "Request failed.");
    }

    renderResponse(data);
    setStatus("Analysis complete", "success");
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unexpected error.";
    renderError(message);
    setStatus("Analysis failed", "error");
  } finally {
    submitButton.disabled = false;
  }
});
