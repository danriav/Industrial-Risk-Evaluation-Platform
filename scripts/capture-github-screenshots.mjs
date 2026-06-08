import { Buffer } from "node:buffer";
import { spawn } from "node:child_process";
import { mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const assetsDir = resolve(root, "docs", "assets");
const chromePath = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const userDataDir = join(tmpdir(), `mero-captures-${Date.now()}`);
const debuggingPort = 9224;
const viewport = { width: 1365, height: 768, deviceScaleFactor: 1, mobile: false };

const files = {
  dashboard: "dashboard.png",
  heatmap: "heatmap.png",
  maintenance: "maintenance-log.png",
  apiDocs: "api-docs.png",
  grafana: "grafana.png",
};

function parseEnv(text) {
  return Object.fromEntries(
    text
      .split(/\r?\n/)
      .filter((line) => /^[^#=]+=/.test(line))
      .map((line) => {
        const index = line.indexOf("=");
        return [line.slice(0, index).trim(), line.slice(index + 1).trim()];
      }),
  );
}

function wait(ms) {
  return new Promise((resolveWait) => setTimeout(resolveWait, ms));
}

async function waitForJson(url, attempts = 80) {
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    try {
      const response = await fetch(url);
      if (response.ok) return response.json();
    } catch {
      // Chrome is still starting.
    }
    await wait(250);
  }
  throw new Error(`Timed out waiting for ${url}`);
}

class CdpClient {
  constructor(wsUrl) {
    this.ws = new WebSocket(wsUrl);
    this.nextId = 1;
    this.pending = new Map();
    this.events = new Map();
  }

  async open() {
    await new Promise((resolveOpen, rejectOpen) => {
      this.ws.addEventListener("open", resolveOpen, { once: true });
      this.ws.addEventListener("error", rejectOpen, { once: true });
    });
    this.ws.addEventListener("message", (event) => {
      const payload = JSON.parse(event.data);
      if (payload.id && this.pending.has(payload.id)) {
        const { resolveCommand, rejectCommand } = this.pending.get(payload.id);
        this.pending.delete(payload.id);
        if (payload.error) rejectCommand(new Error(payload.error.message));
        else resolveCommand(payload.result);
        return;
      }
      const listeners = this.events.get(payload.method) ?? [];
      for (const listener of listeners) listener(payload.params);
    });
  }

  send(method, params = {}) {
    const id = this.nextId;
    this.nextId += 1;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolveCommand, rejectCommand) => {
      this.pending.set(id, { resolveCommand, rejectCommand });
    });
  }

  once(method, timeoutMs = 15000) {
    return new Promise((resolveEvent, rejectEvent) => {
      const timer = setTimeout(() => {
        this.events.set(
          method,
          (this.events.get(method) ?? []).filter((listener) => listener !== handler),
        );
        rejectEvent(new Error(`Timed out waiting for ${method}`));
      }, timeoutMs);
      const handler = (params) => {
        clearTimeout(timer);
        this.events.set(
          method,
          (this.events.get(method) ?? []).filter((listener) => listener !== handler),
        );
        resolveEvent(params);
      };
      this.events.set(method, [...(this.events.get(method) ?? []), handler]);
    });
  }

  close() {
    this.ws.close();
  }
}

async function startChrome() {
  const chrome = spawn(chromePath, [
    "--headless=new",
    `--remote-debugging-port=${debuggingPort}`,
    `--user-data-dir=${userDataDir}`,
    "--hide-scrollbars",
    "--disable-gpu",
    "--no-first-run",
    "--no-default-browser-check",
    `--window-size=${viewport.width},${viewport.height}`,
    "about:blank",
  ]);
  chrome.stderr?.on("data", () => {});
  await waitForJson(`http://127.0.0.1:${debuggingPort}/json/version`);
  return chrome;
}

async function newPage() {
  const targetResponse = await fetch(`http://127.0.0.1:${debuggingPort}/json/new?about:blank`, {
    method: "PUT",
  });
  if (!targetResponse.ok) throw new Error("Unable to create Chrome target");
  const target = await targetResponse.json();
  const client = new CdpClient(target.webSocketDebuggerUrl);
  await client.open();
  await client.send("Page.enable");
  await client.send("Runtime.enable");
  await client.send("Emulation.setDeviceMetricsOverride", viewport);
  return client;
}

async function navigate(client, url, waitMs = 1000) {
  const loaded = client.once("Page.loadEventFired", 20000).catch(() => undefined);
  await client.send("Page.navigate", { url });
  await loaded;
  await wait(waitMs);
}

async function evaluate(client, expression) {
  const result = await client.send("Runtime.evaluate", {
    expression,
    awaitPromise: true,
    returnByValue: true,
  });
  if (result.exceptionDetails) {
    throw new Error(
      `${result.exceptionDetails.text ?? "Runtime evaluation failed"} ${
        result.exceptionDetails.exception?.description ?? ""
      }`.trim(),
    );
  }
  return result.result.value;
}

async function screenshot(client, filename, clip) {
  const result = await client.send("Page.captureScreenshot", {
    format: "png",
    fromSurface: true,
    captureBeyondViewport: false,
    ...(clip ? { clip } : {}),
  });
  await writeFile(resolve(assetsDir, filename), Buffer.from(result.data, "base64"));
}

async function visibleText(client) {
  return evaluate(client, "document.body ? document.body.innerText : ''");
}

async function maskFrontendCredentials(client) {
  await evaluate(
    client,
    `(() => {
      let style = document.getElementById("github-screenshot-secret-mask");
      if (!style) {
        style = document.createElement("style");
        style.id = "github-screenshot-secret-mask";
        style.textContent = 'input[autocomplete="username"], input[autocomplete="current-password"] { color: transparent !important; caret-color: transparent !important; text-shadow: none !important; }';
        document.head.appendChild(style);
      }
    })()`,
  );
}

async function assertNoSecrets(client, env, label) {
  const text = await visibleText(client);
  const forbidden = [
    env.BASIC_AUTH_PASSWORD,
    env.POSTGRES_PASSWORD,
    env.GRAFANA_ADMIN_PASSWORD,
    env.DATABASE_URL,
    "CHANGE_ME",
  ].filter(Boolean);
  const found = forbidden.find((secret) => text.includes(secret));
  if (found) throw new Error(`Sensitive value visible before ${label} capture`);
}

async function loadFrontend(client, env) {
  await navigate(client, "http://127.0.0.1:3000/");
  await evaluate(
    client,
    `(() => {
      const setValue = (input, value) => {
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
        setter.call(input, value);
        input.dispatchEvent(new Event("input", { bubbles: true }));
      };
      const inputs = [...document.querySelectorAll("input")];
      setValue(inputs[0], ${JSON.stringify(env.BASIC_AUTH_USERNAME ?? "")});
      setValue(inputs[1], ${JSON.stringify(env.BASIC_AUTH_PASSWORD ?? "")});
      [...document.querySelectorAll("button")].find((button) => button.textContent.includes("Actualizar")).click();
    })()`,
  );
  await wait(2500);
  await evaluate(
    client,
    `(() => {
      const clearVisibleValue = (input) => {
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set;
        setter.call(input, "");
      };
      [...document.querySelectorAll("input")].forEach(clearVisibleValue);
    })()`,
  );
  await wait(300);
}

async function captureFrontend(client, env) {
  await loadFrontend(client, env);
  await maskFrontendCredentials(client);
  await assertNoSecrets(client, env, "dashboard");
  await screenshot(client, files.dashboard);
  await screenshot(client, files.heatmap, { x: 0, y: 260, width: 920, height: 480, scale: 1 });

  await evaluate(
    client,
    `[...document.querySelectorAll("button")].find((button) => button.textContent.includes("Bitacora")).click()`,
  );
  await wait(500);
  await maskFrontendCredentials(client);
  await assertNoSecrets(client, env, "maintenance");
  await screenshot(client, files.maintenance);
}

async function captureApiDocs(client, env) {
  await navigate(client, "http://127.0.0.1:8080/docs", 1500);
  await assertNoSecrets(client, env, "api-docs");
  await screenshot(client, files.apiDocs);
}

async function captureGrafana(client, env) {
  await navigate(client, "http://127.0.0.1:3001/login", 1500);
  await evaluate(
    client,
    `fetch("/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user: ${JSON.stringify(env.GRAFANA_ADMIN_USER ?? "")},
        password: ${JSON.stringify(env.GRAFANA_ADMIN_PASSWORD ?? "")}
      })
    }).then((response) => response.ok)`,
  );
  await navigate(client, "http://127.0.0.1:3001/d/mero-platform-overview/mero-platform-overview?orgId=1", 2500);
  await assertNoSecrets(client, env, "grafana");
  await screenshot(client, files.grafana);
}

async function main() {
  await mkdir(assetsDir, { recursive: true });
  const env = parseEnv(await readFile(resolve(root, ".env"), "utf8"));
  const chrome = await startChrome();
  let client;
  try {
    client = await newPage();
    await captureFrontend(client, env);
    await captureApiDocs(client, env);
    await captureGrafana(client, env);
    console.log(JSON.stringify({ assetsDir, files }, null, 2));
  } finally {
    client?.close();
    chrome.kill();
    await wait(1000);
    await rm(userDataDir, { recursive: true, force: true }).catch(() => undefined);
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
