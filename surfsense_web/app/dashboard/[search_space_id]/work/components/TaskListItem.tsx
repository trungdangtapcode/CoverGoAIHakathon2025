"use client";

import { Check, ExternalLink } from "lucide-react";
import { format, isPast, parseISO } from "date-fns";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { Task } from "../types";
import type { TaskPriority } from "@/contracts/enums/task";

interface TaskListItemProps {
	task: Task;
	isSelected: boolean;
	onClick: () => void;
	onComplete: () => void;
}

const getPriorityConfig = (priority?: TaskPriority) => {
	switch (priority) {
		case "URGENT":
			return {
				icon: "🔴",
				label: "URGENT",
				className: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400 border-red-500/20",
			};
		case "HIGH":
			return {
				icon: "🟠",
				label: "HIGH",
				className:
					"bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400 border-orange-500/20",
			};
		case "MEDIUM":
			return {
				icon: "🟡",
				label: "MEDIUM",
				className:
					"bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400 border-yellow-500/20",
			};
		case "LOW":
			return {
				icon: "🟢",
				label: "LOW",
				className:
					"bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 border-green-500/20",
			};
		default:
			return {
				icon: "",
				label: "NO PRIORITY",
				className: "bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400",
			};
	}
};

export function TaskListItem({ task, isSelected, onClick, onComplete }: TaskListItemProps) {
	const priorityConfig = getPriorityConfig(task.priority);

	// Check if task is overdue
	const isOverdue = task.due_date && task.status === "UNDONE" && isPast(parseISO(task.due_date));

	return (
		<div
			className={cn(
				"p-3 border-b cursor-pointer transition-colors hover:bg-accent",
				isSelected && "bg-accent border-l-4 border-l-primary"
			)}
			onClick={onClick}
		>
			{/* Priority Badge */}
			<Badge variant="outline" className={cn("text-xs", priorityConfig.className)}>
				{priorityConfig.icon} {priorityConfig.label}
			</Badge>

			{/* Task Title */}
			<h3 className="font-medium mt-2 line-clamp-2">{task.title}</h3>

			{/* Description (truncated) */}
			{task.description && (
				<p className="text-sm text-muted-foreground mt-1 line-clamp-2">{task.description}</p>
			)}

			{/* Footer: Due date + Source + Complete button */}
			<div className="flex items-center justify-between mt-3 gap-2">
				<div className="flex flex-col gap-1 text-xs text-muted-foreground">
					{/* Due Date */}
					{task.due_date && (
						<span className={cn(isOverdue && "text-red-500 font-medium")}>
							Due: {format(parseISO(task.due_date), "MMM d, yyyy")}
							{isOverdue && " (Overdue)"}
						</span>
					)}
					{/* Source Type */}
					<span className="capitalize">{task.source_type.toLowerCase()}</span>
				</div>

				{/* Action Buttons */}
				<div className="flex items-center gap-1">
					{/* External Link */}
					{task.external_url && (
						<Button
							size="icon"
							variant="ghost"
							className="h-7 w-7"
							onClick={(e) => {
								e.stopPropagation();
								window.open(task.external_url, "_blank");
							}}
							title="View in Linear"
						>
							<ExternalLink className="h-3.5 w-3.5" />
						</Button>
					)}

					{/* Complete Button */}
					{task.status === "UNDONE" && (
						<Button
							size="icon"
							variant="ghost"
							className="h-7 w-7 hover:bg-green-500/10 hover:text-green-600"
							onClick={(e) => {
								e.stopPropagation();
								onComplete();
							}}
							title="Mark as complete"
						>
							<Check className="h-4 w-4" />
						</Button>
					)}

					{/* Completed Badge */}
					{task.status === "DONE" && (
						<Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
							<Check className="h-3 w-3 mr-1" />
							Done
						</Badge>
					)}
				</div>
			</div>
		</div>
	);
}
