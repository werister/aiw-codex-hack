"use client";

import { useMemo, useState } from "react";
import {
  AssistantRuntimeProvider,
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useLocalRuntime,
  type ChatModelAdapter,
} from "@assistant-ui/react";
import type { ForecastResponse, HourForecast } from "@/lib/forecast-types";
import { explainForecastQuestion, formatForecastHour, FORECAST_SUGGESTIONS } from "@/lib/forecast-explanation";
import { answerHandoverQuestion, HANDOVER_SUGGESTIONS } from "@/lib/forecast-handover";
import { cx, Panel } from "./ui";

export function ForecastAssistant({
  f,
  h,
}: {
  f: ForecastResponse;
  h: HourForecast | undefined;
}) {
  // A changed forecast or selected hour starts a fresh thread, preventing stale answers.
  const sessionKey = JSON.stringify([
    f.issued_at,
    f.mode,
    f.model_version,
    f.rules_version,
    h,
    f.hours,
    f.next_change,
  ]);
  return <ForecastAssistantSession key={sessionKey} forecast={f} hour={h} />;
}

function ForecastAssistantSession({
  forecast,
  hour,
}: {
  forecast: ForecastResponse;
  hour: HourForecast | undefined;
}) {
  const [copyText, setCopyText] = useState<string | null>(null);
  const [copyStatus, setCopyStatus] = useState("");
  const adapter = useMemo<ChatModelAdapter>(() => ({
    async run({ messages }) {
      const lastUserMessage = [...messages].reverse().find((message) => message.role === "user");
      const question = lastUserMessage?.content
        .filter((part) => part.type === "text")
        .map((part) => part.text)
        .join(" ") ?? "";
      const handover = answerHandoverQuestion(forecast, hour, question);
      if (handover) {
        setCopyText(handover.copyable ? handover.text : null);
        setCopyStatus("");
        return { content: [{ type: "text", text: handover.text }] };
      }
      setCopyText(null);
      setCopyStatus("");
      return {
        content: [{ type: "text", text: explainForecastQuestion(forecast, hour, question) }],
      };
    },
  }), [forecast, hour]);
  const runtime = useLocalRuntime(adapter);

  async function copyHandover() {
    if (!copyText) return;
    try {
      if (!navigator.clipboard?.writeText) throw new Error("Clipboard unavailable");
      await navigator.clipboard.writeText(copyText);
      setCopyStatus("Handover copied.");
    } catch {
      setCopyStatus("Clipboard access failed. Select and copy the handover text below.");
    }
  }

  return (
    <Panel
      title="Forecast guide"
      aside={<span className="text-[13px] text-muted">{hour ? `Selected: ${formatForecastHour(hour)}` : "Select a forecast hour"}</span>}
    >
      <AssistantRuntimeProvider runtime={runtime}>
        <ThreadPrimitive.Root className="flex min-w-0 flex-col gap-3">
          <ThreadPrimitive.Viewport
            autoScroll
            role="log"
            aria-live="polite"
            aria-label="Forecast guide conversation"
            className="max-h-52 min-h-8 space-y-2 overflow-y-auto pr-1"
          >
            <ThreadPrimitive.Messages>
              {({ message }) => (
                <MessagePrimitive.Root
                  className={cx(
                    "w-fit max-w-[92%] rounded-[8px] px-3 py-2 text-[15px] leading-snug [overflow-wrap:anywhere] sm:max-w-[80%]",
                    message.role === "user" ? "ml-auto bg-select text-ink" : "bg-panel-2 text-ink",
                  )}
                >
                  <MessagePrimitive.Parts />
                </MessagePrimitive.Root>
              )}
            </ThreadPrimitive.Messages>
          </ThreadPrimitive.Viewport>

          <p className="text-[13px] text-muted">
            The summary covers up to six consecutive hours, starting at your selection.
          </p>

          <div className="flex flex-wrap gap-2" aria-label="Suggested questions">
            {[...HANDOVER_SUGGESTIONS, ...FORECAST_SUGGESTIONS].map((prompt) => (
              <ThreadPrimitive.Suggestion
                key={prompt}
                prompt={prompt}
                send
                className="min-h-11 rounded-full border border-line px-3 py-1.5 text-left text-[13px] text-ink transition-colors hover:bg-select motion-reduce:transition-none"
              >
                {prompt}
              </ThreadPrimitive.Suggestion>
            ))}
          </div>

          <ComposerPrimitive.Root className="flex items-end gap-2 border-t border-line pt-3">
            <ComposerPrimitive.Input
              aria-label="Ask about the selected forecast hour"
              placeholder="Ask about this hour…"
              rows={1}
              className="min-h-11 min-w-0 flex-1 resize-none rounded-[8px] border border-line bg-panel px-3 py-2 text-[15px] text-ink placeholder:text-muted"
            />
            <ComposerPrimitive.Send className="pill-btn min-h-11 bg-accent text-accent-ink [--btn-ring:var(--accent)] disabled:cursor-not-allowed disabled:opacity-50">
              Explain
            </ComposerPrimitive.Send>
          </ComposerPrimitive.Root>
        </ThreadPrimitive.Root>
      </AssistantRuntimeProvider>
      {copyText && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <button type="button" onClick={copyHandover} className="min-h-11 rounded-full border border-line px-3 py-1.5 text-[13px] text-ink hover:bg-select">
            Copy handover
          </button>
          {copyStatus && <span role={copyStatus.startsWith("Clipboard") ? "alert" : "status"} className="text-[13px] text-muted">{copyStatus}</span>}
          {copyStatus.startsWith("Clipboard") && (
            <textarea
              aria-label="Handover text for manual copying"
              readOnly
              value={copyText}
              onFocus={(event) => event.currentTarget.select()}
              className="min-h-24 w-full rounded-[8px] border border-line bg-panel px-3 py-2 text-[13px] text-ink"
            />
          )}
        </div>
      )}
    </Panel>
  );
}
