const messages = document.getElementById("messages");
const form = document.getElementById("chat-form");
const question = document.getElementById("question");
const latencyEl = document.getElementById("latency");
const healthIndicator = document.getElementById("health-indicator");
const healthText = document.getElementById("health-text");
const ingestBtn = document.getElementById("ingest-btn");
const ingestDir = document.getElementById("ingest-dir");
const ingestOutput = document.getElementById("ingest-output");

const appendMessage = (role, text, sources = []) => {
  const wrapper = document.createElement("article");
  wrapper.className = `message ${role}`;
  const body = document.createElement("div");
  body.className = "body";
  body.innerText = text;
  wrapper.appendChild(body);

  if (sources.length > 0) {
    const list = document.createElement("ul");
    list.className = "sources";
    sources.forEach((src) => {
      const item = document.createElement("li");
      item.innerText = `${src.rank}. ${src.file} (page ${src.page})`;
      list.appendChild(item);
    });
    wrapper.appendChild(list);
  }

  messages.appendChild(wrapper);
  messages.scrollTop = messages.scrollHeight;
};

const setHealth = (isHealthy, env = "local") => {
  healthIndicator.className = `indicator ${isHealthy ? "ok" : "ko"}`;
  healthText.innerText = isHealthy ? `Service online (${env})` : "Service unavailable";
};

const checkHealth = async () => {
  try {
    const res = await fetch("/health");
    if (!res.ok) throw new Error("failed");
    const data = await res.json();
    setHealth(true, data.environment);
  } catch (error) {
    setHealth(false);
  }
};

const sendQuestion = async (event) => {
  event.preventDefault();
  const content = question.value.trim();
  if (!content) return;

  appendMessage("user", content);
  question.value = "";
  question.disabled = true;

  const start = performance.now();
  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: content }),
    });
    const duration = performance.now() - start;
    latencyEl.innerText = `${duration.toFixed(0)} ms`;
    if (!response.ok) {
      const error = await response.json();
      appendMessage("assistant", `Error: ${error.detail ?? "Unknown error"}`);
    } else {
      const data = await response.json();
      appendMessage("assistant", data.answer, data.sources);
    }
  } catch (error) {
    appendMessage("assistant", `Network error: ${error.message}`);
  } finally {
    question.disabled = false;
    question.focus();
  }
};

const runIngestion = async () => {
  ingestBtn.disabled = true;
  ingestOutput.innerText = "Ingesting...";
  try {
    const payload = { source_dir: ingestDir.value.trim() || null };
    const res = await fetch("/ingest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) {
      ingestOutput.innerText = `Error: ${data.detail}`;
    } else {
      ingestOutput.innerText = JSON.stringify(data.metrics, null, 2);
    }
  } catch (error) {
    ingestOutput.innerText = `Network error: ${error.message}`;
  } finally {
    ingestBtn.disabled = false;
  }
};

form.addEventListener("submit", sendQuestion);
ingestBtn.addEventListener("click", runIngestion);

checkHealth();
