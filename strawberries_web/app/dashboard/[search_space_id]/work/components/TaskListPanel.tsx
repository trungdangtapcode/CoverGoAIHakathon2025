"use client";

import { RefreshCw, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { Task } from "../types";
import type { TaskStatus } from "@/contracts/enums/task";
import { TaskListItem } from "./TaskListItem";
import { Skeleton } from "@/components/ui/skeleton";

interface TaskListPanelProps {
	tasks: Task[];
	selectedTask: Task | null;
	onSelectTask: (task: Task) => void;
	onSyncTasks: () => void;
	onCompleteTask: (taskId: number) => void;
	statusFilter: TaskStatus;
	onStatusFilterChange: (status: TaskStatus) => void;
	loading?: boolean;
	onCreateTask?: () => void;
}

export function TaskListPanel({
	tasks,
	selectedTask,
	onSelectTask,
	onSyncTasks,
	onCompleteTask,
	statusFilter,
	onStatusFilterChange,
	loading = false,
	onCreateTask,
}: TaskListPanelProps) {
	// Filter tasks based on status
	const filteredTasks = tasks.filter((task) => task.status === statusFilter);

	return (
		<div className="flex flex-col h-full">
			{/* Header */}
			<div className="p-4 border-b space-y-3">
				<div className="flex items-center justify-between">
					<h2 className="text-lg font-semibold">Work Mode</h2>
				</div>

				{/* Action Buttons */}
				<div className="flex gap-2">
					<Button onClick={onSyncTasks} variant="outline" size="sm" className="flex-1" disabled={loading}>
						<RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
						Sync Linear
					</Button>
					{onCreateTask && (
						<Button onClick={onCreateTask} variant="default" size="sm" disabled={loading}>
							<Plus className="h-4 w-4" />
						</Button>
					)}
				</div>

				{/* Task Count */}
				<div className="text-sm text-muted-foreground">
					{filteredTasks.length} {filteredTasks.length === 1 ? "task" : "tasks"}
				</div>
			</div>

			{/* Status Tabs */}
			<Tabs
				value={statusFilter}
				onValueChange={(value) => onStatusFilterChange(value as TaskStatus)}
				className="w-full"
			>
				<div className="px-4 pt-3 border-b">
					<TabsList className="grid w-full grid-cols-2">
						<TabsTrigger value="UNDONE">Undone</TabsTrigger>
						<TabsTrigger value="DONE">Done</TabsTrigger>
					</TabsList>
				</div>

				{/* Task List */}
				<TabsContent value={statusFilter} className="mt-0 flex-1 overflow-hidden">
					<ScrollArea className="h-[calc(100vh-16rem)]">
						{loading ? (
							// Loading state
							<div className="space-y-2 p-2">
								{[1, 2, 3, 4, 5].map((i) => (
									<div key={i} className="p-3 border-b space-y-2">
										<Skeleton className="h-5 w-20" />
										<Skeleton className="h-4 w-full" />
										<Skeleton className="h-3 w-3/4" />
									</div>
								))}
							</div>
						) : filteredTasks.length === 0 ? (
							// Empty state
							<div className="flex flex-col items-center justify-center h-64 text-center p-4">
								<div className="text-4xl mb-2">
									{statusFilter === "UNDONE" ? "✅" : "🎉"}
								</div>
								<h3 className="font-medium mb-1">
									{statusFilter === "UNDONE" ? "No tasks to do" : "No completed tasks yet"}
								</h3>
								<p className="text-sm text-muted-foreground">
									{statusFilter === "UNDONE"
										? "Sync tasks from Linear or create a new task"
										: "Complete tasks to see them here"}
								</p>
							</div>
						) : (
							// Task list
							filteredTasks.map((task) => (
								<TaskListItem
									key={task.id}
									task={task}
									isSelected={selectedTask?.id === task.id}
									onClick={() => onSelectTask(task)}
									onComplete={() => onCompleteTask(task.id)}
								/>
							))
						)}
					</ScrollArea>
				</TabsContent>
			</Tabs>
		</div>
	);
}
