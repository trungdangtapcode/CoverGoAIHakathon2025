"use client";

import { useChat } from "@ai-sdk/react";
import { FileText } from "lucide-react";
import { useMemo } from "react";
import ChatInterface from "@/components/chat/ChatInterface";
import { useChatState } from "@/hooks/use-chat";
import type { Task } from "../types";

interface TaskChatPanelProps {
	selectedTask: Task | null;
	searchSpaceId: string;
}

export function TaskChatPanel({ selectedTask, searchSpaceId }: TaskChatPanelProps) {
	const { token } = useChatState({
		search_space_id: searchSpaceId,
	});

	// Memoize task context to avoid re-creating on every render
	const taskContext = useMemo(() => {
		if (!selectedTask) return null;
		const context = {
			task_id: selectedTask.id,
			task_title: selectedTask.title,
			task_description: selectedTask.description || "",
			task_priority: selectedTask.priority || "",
			task_due_date: selectedTask.due_date || "",
		};
		console.log("🎯 TaskChatPanel - Task Context:", context);
		return context;
	}, [selectedTask]);

	// Chat handler with task context
	const handler = useChat({
		api: `${process.env.NEXT_PUBLIC_FASTAPI_BACKEND_URL}/api/v1/chat`,
		streamProtocol: "data",
		initialMessages: [],
		headers: {
			...(token && { Authorization: `Bearer ${token}` }),
		},
		body: {
			data: {
				search_space_id: searchSpaceId,
				research_mode: "QNA",
				search_mode: "CHUNKS",
				selected_connectors: [],
				document_ids_to_add_in_context: [],
				// Pass task context to the backend
				task_context: taskContext,
			},
		},
		onError: (error) => {
			console.error("Chat error:", error);
		},
	});

	// Empty state when no task is selected
	if (!selectedTask) {
		return (
			<div className="flex items-center justify-center h-full bg-muted/20">
				<div className="text-center max-w-md px-6">
					<FileText className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
					<h3 className="text-xl font-semibold mb-2">No task selected</h3>
					<p className="text-muted-foreground">
						Select a task from the list to get AI assistance. The AI will help you brainstorm solutions,
						debug issues, and guide you through implementation.
					</p>
				</div>
			</div>
		);
	}

	return (
		<div className="flex flex-col h-full">
			{/* Task Header */}
			<div className="p-4 border-b bg-muted/50 space-y-2">
				<div className="flex items-start justify-between gap-3">
					<div className="flex-1 min-w-0">
						<h3 className="font-semibold text-lg line-clamp-2">{selectedTask.title}</h3>
						{selectedTask.description && (
							<p className="text-sm text-muted-foreground mt-1 line-clamp-2">
								{selectedTask.description}
							</p>
						)}
					</div>
				</div>

				{/* Task metadata */}
				<div className="flex items-center gap-4 text-xs text-muted-foreground">
					{selectedTask.priority && (
						<span className="capitalize">
							Priority: <span className="font-medium">{selectedTask.priority}</span>
						</span>
					)}
					{selectedTask.due_date && (
						<span>
							Due: <span className="font-medium">{new Date(selectedTask.due_date).toLocaleDateString()}</span>
						</span>
					)}
					<span className="capitalize">Source: {selectedTask.source_type.toLowerCase()}</span>
				</div>
			</div>

			{/* Chat Interface */}
			<div className="flex-1 overflow-hidden">
				<ChatInterface
					handler={handler}
					selectedDocuments={[]}
					selectedConnectors={[]}
					searchMode="CHUNKS"
					researchMode="QNA"
					// Disable document/connector selection for work mode
					onDocumentSelectionChange={undefined}
					onConnectorSelectionChange={undefined}
					onSearchModeChange={undefined}
					onResearchModeChange={undefined}
				/>
			</div>
		</div>
	);
}
