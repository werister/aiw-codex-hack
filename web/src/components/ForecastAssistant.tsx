"use client";

import { useMemo } from "react";
import {
  AssistantRuntimeProvider,
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useLocalRuntime,
  type ChatModelAdapter,
} from "@assistant-ui/react";
import type { ForecastResponse, HourForecast } from "@/lib/forecast-types";
import { explainForecastQuestion, FORECAST_SUGGESTIONS } from "@/lib/forecast-explanation";
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
  const adapter = useMemo<ChatModelAdapter>(() => ({
    async run({ messages }) {
      const lastUserMessage = [...messages].reverse().find((message) => message.role === "user");
      const question = lastUserMessage?.content
        .filter((part) => part.type === "text")
        .map((part) => part.text)
        .join(" ") ?? "";
      return {
        content: [{ type: "text", text: explainForecastQuestion(forecast, hour, question) }],
      };
    },
  }), [forecast, hour]);
  const runtime = useLocalRuntime(adapter);

  return (
    <Panel
      title="Forecast guide"
      aside={<span className="text-[13px] text-muted">Answers from the selected forecast data.</span>}
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

          <div className="flex flex-wrap gap-2" aria-label="Suggested questions">
            {FORECAST_SUGGESTIONS.map((prompt) => (
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
    </Panel>
  );
}
