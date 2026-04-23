import type { ExtensionAPI } from "@mariozechner/pi-coding-agent";
import { Box, Container, Spacer, Text } from "@mariozechner/pi-tui";

const SYSTEM_PROMPT_TYPE = "inspector-system-prompt";

const COLLAPSED_PREVIEW_LINES = 8;
const EXPANDED_MAX_CHARS = 40000;
const PREVIEW_MAX_CHARS = 4000;

let systemPromptSeq = 0;
let lastSystemPrompt = "";

function timestamp(): string {
  return new Date().toLocaleTimeString();
}

function limitChars(text: string, maxChars: number): string {
  if (text.length <= maxChars) return text;
  return `${text.slice(0, maxChars)}\n...[truncated ${text.length - maxChars} chars]`;
}

function firstLines(text: string, count: number): string[] {
  return text.split("\n").slice(0, count);
}

function buildPreview(text: string): string {
  const limited = limitChars(text, PREVIEW_MAX_CHARS);
  const lines = firstLines(limited, COLLAPSED_PREVIEW_LINES);
  return lines.join("\n");
}

function buildBox(title: string, subtitle: string, body: string, hint: string, theme: any) {
  const lines = [
    theme.fg("accent", theme.bold(title)),
    theme.fg("dim", subtitle),
    "",
    body,
    "",
    theme.fg("dim", hint),
  ].join("\n");

  const box = new Box(1, 1, (t: string) => theme.bg("customMessageBg", t));
  box.addChild(new Text(lines, 0, 0));

  const container = new Container();
  container.addChild(box);
  container.addChild(new Spacer(1));
  return container;
}

function renderSnapshotMessage(message: { content: string; details?: unknown }, expanded: boolean, theme: any) {
  const details = (message.details ?? {}) as {
    title?: string;
    subtitle?: string;
    preview?: string;
    full?: string;
  };

  const title = details.title ?? message.content;
  const subtitle = details.subtitle ?? "";
  const body = expanded
    ? limitChars(details.full ?? details.preview ?? "", EXPANDED_MAX_CHARS)
    : details.preview ?? "";
  const hint = expanded ? "Ctrl+O to collapse details" : "Ctrl+O to expand details";

  return buildBox(title, subtitle, body, hint, theme);
}

export default function (pi: ExtensionAPI) {
  pi.registerMessageRenderer(SYSTEM_PROMPT_TYPE, (message, { expanded }, theme) => {
    return renderSnapshotMessage(message, expanded, theme);
  });

  pi.on("context", async (event) => {
    return {
      messages: event.messages.filter((m) => {
        const msg = m as { customType?: string };
        return msg.customType !== SYSTEM_PROMPT_TYPE;
      }),
    };
  });

  pi.on("session_start", async (event, ctx) => {
    const prompt = ctx.getSystemPrompt();
    lastSystemPrompt = prompt;
    systemPromptSeq += 1;

    pi.sendMessage({
      customType: SYSTEM_PROMPT_TYPE,
      content: "System prompt snapshot",
      display: true,
      details: {
        title: `System Prompt Snapshot #${systemPromptSeq}`,
        subtitle: `${timestamp()} · ${prompt.length} chars · reason=${event.reason}`,
        preview: buildPreview(prompt),
        full: prompt,
      },
    }, { triggerTurn: false });

  });

  pi.on("session_shutdown", async () => {});
}
