import { existsSync, readdirSync, readFileSync } from "node:fs";
import { spawn } from "node:child_process";
import os from "node:os";
import path from "node:path";
import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";

type AutoContinueState = {
  enabled: boolean;
  prompt: string;
  inFlight: boolean;
  consecutiveAutoContinues: number;
  lastDecision: string;
  hfPublishInFlight: boolean;
  hfPublishPending: boolean;
};

let scheduledContinuation: ReturnType<typeof setTimeout> | null = null;

const STATE_TYPE = "auto-continue-state";
const HF_WORKSPACE = ".pi/hf-sessions";
const HF_CURRENT_SESSION_WORKSPACE = ".pi/hf-sessions-current";

const state: AutoContinueState = {
  enabled: true,
  prompt:
    "Continue the work. Resume the most useful unfinished thread and take the next concrete step that improves understanding, evidence, or progress. Treat failed attempts as information, not as the end of the work.",
  inFlight: false,
  consecutiveAutoContinues: 0,
  lastDecision: "not checked yet",
  hfPublishInFlight: false,
  hfPublishPending: false,
};

function setDecision(reason: string) {
  state.lastDecision = `${new Date().toLocaleTimeString()} · ${reason}`;
}

function persist(pi: ExtensionAPI) {
  pi.appendEntry(STATE_TYPE, {
    enabled: state.enabled,
    prompt: state.prompt,
  });
}

function getHfWorkspacePath() {
  return path.resolve(process.cwd(), HF_WORKSPACE);
}

function getCurrentSessionWorkspacePath() {
  return path.resolve(process.cwd(), HF_CURRENT_SESSION_WORKSPACE);
}

function isHfConfigured() {
  return existsSync(path.join(getHfWorkspacePath(), "workspace.json"));
}

function readWorkspaceConfig(workspacePathValue: string) {
  const configPath = path.join(workspacePathValue, "workspace.json");
  if (!existsSync(configPath)) return null;
  return JSON.parse(readFileSync(configPath, "utf-8")) as {
    cwd?: string;
    repo?: string;
    noImages?: boolean;
  };
}

function findLatestSessionFile() {
  const sessionsRoot = path.join(os.homedir(), ".pi", "agent", "sessions");
  if (!existsSync(sessionsRoot)) return null;

  const files: string[] = [];
  const walk = (dir: string) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const fullPath = path.join(dir, entry.name);
      if (entry.isDirectory()) walk(fullPath);
      else if (entry.isFile() && entry.name.endsWith(".jsonl")) files.push(fullPath);
    }
  };
  walk(sessionsRoot);
  if (files.length === 0) return null;

  files.sort((a, b) => path.basename(a).localeCompare(path.basename(b)));
  return files[files.length - 1] ?? null;
}

function runCommand(command: string, args: string[], cwd: string) {
  return new Promise<void>((resolve, reject) => {
    const child = spawn(command, args, {
      cwd,
      stdio: "ignore",
    });

    child.on("error", reject);
    child.on("exit", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`${command} ${args.join(" ")} exited with code ${code ?? "unknown"}`));
    });
  });
}

function runShell(command: string, cwd: string) {
  return new Promise<void>((resolve, reject) => {
    const child = spawn("sh", ["-lc", command], {
      cwd,
      stdio: "ignore",
    });

    child.on("error", reject);
    child.on("exit", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`sh -lc ${JSON.stringify(command)} exited with code ${code ?? "unknown"}`));
    });
  });
}

function getContextFiles(cwd: string) {
  const candidates = ["README.md", "AGENTS.md"];
  return candidates.filter((name) => existsSync(path.join(cwd, name)));
}

function getDenyFile(cwd: string) {
  const candidates = ["pi-share-hf.deny.txt", ".pi-share-hf.deny.txt", "deny.txt"];
  return candidates.find((name) => existsSync(path.join(cwd, name))) ?? null;
}

async function ensureCurrentSessionWorkspace(cwd: string) {
  const sourceConfig = readWorkspaceConfig(getHfWorkspacePath());
  const repo = sourceConfig?.repo;
  if (!repo) throw new Error(`missing repo in ${path.join(getHfWorkspacePath(), "workspace.json")}`);

  const currentWorkspace = getCurrentSessionWorkspacePath();
  const currentConfig = readWorkspaceConfig(currentWorkspace);
  if (currentConfig?.repo === repo && currentConfig?.cwd === cwd) {
    return currentWorkspace;
  }

  await runCommand("pi-share-hf", [
    "init",
    "--cwd",
    cwd,
    "--repo",
    repo,
    "--workspace",
    currentWorkspace,
  ], cwd);

  return currentWorkspace;
}

async function triggerHfPublish(ctx: { ui: { notify(message: string, level: string): void } }) {
  if (!isHfConfigured()) return;

  if (state.hfPublishInFlight) {
    state.hfPublishPending = true;
    return;
  }

  const cwd = process.cwd();
  const contextFiles = getContextFiles(cwd);
  if (contextFiles.length === 0) {
    ctx.ui.notify("pi-share-hf skipped: no README.md or AGENTS.md in project root", "warning");
    return;
  }
  const denyFile = getDenyFile(cwd);

  const sessionFile = findLatestSessionFile();
  if (!sessionFile) {
    ctx.ui.notify("pi-share-hf skipped: no current session file found", "warning");
    return;
  }

  state.hfPublishInFlight = true;

  try {
    do {
      state.hfPublishPending = false;
      const workspace = await ensureCurrentSessionWorkspace(cwd);
      const collectCommand = [
        `printf "y\\n" | pi-share-hf collect --workspace ${JSON.stringify(workspace)} --session ${JSON.stringify(path.basename(sessionFile))}`,
        ...(denyFile ? [`--deny ${JSON.stringify(denyFile)}`] : []),
        ...contextFiles.map((file) => JSON.stringify(file)),
      ].join(" ");
      await runShell(collectCommand, cwd);
      await runCommand("pi-share-hf", ["upload", "--workspace", workspace], cwd);
    } while (state.hfPublishPending);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    ctx.ui.notify(`pi-share-hf publish failed: ${message}`, "error");
  } finally {
    state.hfPublishInFlight = false;
  }
}

export default function (pi: ExtensionAPI) {
  pi.on("session_start", async (_event, ctx) => {
    for (const entry of ctx.sessionManager.getBranch()) {
      if (entry.type === "custom" && entry.customType === STATE_TYPE && entry.data) {
        const data = entry.data as Partial<AutoContinueState>;
        if (typeof data.enabled === "boolean") state.enabled = data.enabled;
        if (typeof data.prompt === "string") state.prompt = data.prompt;
      }
    }
  });

  pi.on("agent_end", async (_event, ctx) => {
    if (!state.enabled) {
      setDecision("skipped: disabled");
      return;
    }
    if (state.inFlight || scheduledContinuation) {
      setDecision("skipped: continuation already scheduled/in flight");
      return;
    }
    if (ctx.hasPendingMessages()) {
      setDecision("skipped: pending messages already exist");
      return;
    }

    state.inFlight = true;
    state.consecutiveAutoContinues += 1;
    setDecision(`scheduling auto-continue #${state.consecutiveAutoContinues}`);
    ctx.ui.notify(`Auto-continue triggered (#${state.consecutiveAutoContinues})`, "info");
    void triggerHfPublish(ctx);

    scheduledContinuation = setTimeout(async () => {
      scheduledContinuation = null;
      try {
        await pi.sendUserMessage(state.prompt);
        setDecision(`sent auto-continue #${state.consecutiveAutoContinues}`);
      } catch (error) {
        state.consecutiveAutoContinues = Math.max(0, state.consecutiveAutoContinues - 1);
        const message = error instanceof Error ? error.message : String(error);
        setDecision(`send failed: ${message}`);
        ctx.ui.notify(`Auto-continue failed: ${message}`, "error");
      } finally {
        state.inFlight = false;
      }
    }, 300);
  });

  pi.on("input", async (event) => {
    if (event.source !== "extension") {
      state.consecutiveAutoContinues = 0;
      setDecision(`counter reset by ${event.source} input`);
    }
    return undefined;
  });

  pi.on("session_shutdown", async () => {
    state.inFlight = false;
    state.hfPublishPending = false;
    if (scheduledContinuation) {
      clearTimeout(scheduledContinuation);
      scheduledContinuation = null;
    }
  });
}
