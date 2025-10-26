"use client";

import { useCallback, useState } from "react";
import { toast } from "sonner";
import type {
	Task,
	TaskCompleteRequest,
	TaskCreate,
	TaskFilterRequest,
	TaskSyncRequest,
} from "@/app/dashboard/[search_space_id]/work/types";
import type { TaskStatus } from "@/contracts/enums/task";
import { apiClient } from "@/lib/api";

export function useTasks(searchSpaceId: number) {
	const [tasks, setTasks] = useState<Task[]>([]);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	/**
	 * Get tasks with optional filtering and sorting
	 */
	const getTasks = useCallback(
		async (status?: TaskStatus, sortByPriority: boolean = true) => {
			setLoading(true);
			setError(null);
			try {
				const request: TaskFilterRequest = {
					search_space_id: searchSpaceId,
					status: status,
					sort_by_priority: sortByPriority,
				};

				const fetchedTasks = await apiClient.post<Task[]>("/api/v1/tasks/filter", request);

				setTasks(fetchedTasks);
				return fetchedTasks;
			} catch (err: any) {
				const errorMsg = err.message || "Failed to fetch tasks";
				setError(errorMsg);
				toast.error(errorMsg);
				console.error("Error fetching tasks:", err);
				return [];
			} finally {
				setLoading(false);
			}
		},
		[searchSpaceId]
	);

	/**
	 * Sync tasks from workspace connectors (Linear, Jira, etc.)
	 */
	const syncTasks = useCallback(
		async (connectorTypes: string[]) => {
			setLoading(true);
			setError(null);
			try {
				const request: TaskSyncRequest = {
					search_space_id: searchSpaceId,
					connector_types: connectorTypes,
				};

				const syncedTasks = await apiClient.post<Task[]>("/api/v1/tasks/sync", request);

				toast.success(`Synced ${syncedTasks.length} tasks from ${connectorTypes.join(", ")}`);

				// Refresh the task list
				await getTasks();
				return syncedTasks;
			} catch (err: any) {
				const errorMsg = err.message || "Failed to sync tasks";
				setError(errorMsg);
				toast.error(errorMsg);
				console.error("Error syncing tasks:", err);
				return [];
			} finally {
				setLoading(false);
			}
		},
		[searchSpaceId, getTasks]
	);

	/**
	 * Generate demo tasks for testing (10 realistic tasks)
	 */
	const syncDemoTasks = useCallback(
		async () => {
			setLoading(true);
			setError(null);
			try {
				const request: TaskSyncRequest = {
					search_space_id: searchSpaceId,
					connector_types: ["LINEAR"],
				};

				const demoTasks = await apiClient.post<Task[]>("/api/v1/tasks/sync-demo", request);

				toast.success(`Synced ${demoTasks.length} from Linear!`);

				// Refresh the task list
				await getTasks();
				return demoTasks;
			} catch (err: any) {
				const errorMsg = err.message || "Failed to create demo tasks";
				setError(errorMsg);
				toast.error(errorMsg);
				console.error("Error creating demo tasks:", err);
				return [];
			} finally {
				setLoading(false);
			}
		},
		[searchSpaceId, getTasks]
	);

	/**
	 * Mark a task as complete and auto-link related resources
	 */
	const completeTask = useCallback(
		async (taskId: number) => {
			setLoading(true);
			setError(null);
			try {
				const request: TaskCompleteRequest = {
					task_id: taskId,
				};

				const updatedTask = await apiClient.post<Task>("/api/v1/tasks/complete", request);

				// Update the task in the local state
				setTasks((prevTasks) =>
					prevTasks.map((task) => (task.id === taskId ? updatedTask : task))
				);

				toast.success("Task marked as complete!");

				// Show linked resources if any
				if (updatedTask.linked_chat_ids && updatedTask.linked_chat_ids.length > 0) {
					toast.info(
						`Linked ${updatedTask.linked_chat_ids.length} chat(s) and ${updatedTask.linked_document_ids?.length || 0} document(s)`
					);
				}

				return updatedTask;
			} catch (err: any) {
				const errorMsg = err.message || "Failed to complete task";
				setError(errorMsg);
				toast.error(errorMsg);
				console.error("Error completing task:", err);
				return null;
			} finally {
				setLoading(false);
			}
		},
		[]
	);

	/**
	 * Create a manual task (not from connectors)
	 */
	const createTask = useCallback(
		async (taskData: TaskCreate) => {
			setLoading(true);
			setError(null);
			try {
				const newTask = await apiClient.post<Task>("/api/v1/tasks/create", taskData);

				// Add the new task to the local state
				setTasks((prevTasks) => [newTask, ...prevTasks]);

				toast.success("Task created successfully!");
				return newTask;
			} catch (err: any) {
				const errorMsg = err.message || "Failed to create task";
				setError(errorMsg);
				toast.error(errorMsg);
				console.error("Error creating task:", err);
				return null;
			} finally {
				setLoading(false);
			}
		},
		[]
	);

	/**
	 * Refresh the task list (alias for getTasks)
	 */
	const refreshTasks = useCallback(
		async (status?: TaskStatus) => {
			return await getTasks(status);
		},
		[getTasks]
	);

	return {
		tasks,
		loading,
		error,
		syncTasks,
		syncDemoTasks,
		getTasks,
		completeTask,
		createTask,
		refreshTasks,
	};
}
