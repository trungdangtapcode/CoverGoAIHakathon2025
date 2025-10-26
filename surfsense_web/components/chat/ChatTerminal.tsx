"use client";

import { getAnnotationData, type Message } from "@llamaindex/chat-ui";
import { Brain } from "lucide-react";

export default function TerminalDisplay({ message, open }: { message: Message; open: boolean }) {
	// Get the last assistant message that's not being typed
	if (!message) {
		return null;
	}

	interface TerminalInfo {
		id: number;
		text: string;
		type: string;
	}

	const events = getAnnotationData(message, "TERMINAL_INFO") as TerminalInfo[];

	// Show thinking indicator only if there are events and the message is still being processed
	if (events.length === 0 || !open) {
		return null;
	}

	// Get the latest event text
	const latestEvent = events[events.length - 1];
	const thinkingText = latestEvent?.text || "Thinking...";

	return (
		<div className="flex items-center gap-2 text-muted-foreground text-sm py-2">
			<Brain className="h-4 w-4 animate-pulse" />
			<span className="animate-pulse">{thinkingText}</span>
		</div>
	);
}
