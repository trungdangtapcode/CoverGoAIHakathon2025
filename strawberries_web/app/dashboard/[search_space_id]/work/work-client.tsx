"use client";

import { motion } from "motion/react";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import type { Task } from "./types";
import type { TaskStatus } from "@/contracts/enums/task";
import { useTasks } from "@/hooks/use-tasks";
import { TaskListPanel } from "./components/TaskListPanel";
import { TaskChatPanel } from "./components/TaskChatPanel";

const pageVariants = {
	initial: { opacity: 0 },
	enter: {
		opacity: 1,
		transition: { duration: 0.4, ease: "easeInOut" },
	},
	exit: { opacity: 0, transition: { duration: 0.3, ease: "easeInOut" } },
};

export default function WorkModeClient() {
	const { search_space_id } = useParams();
	const searchSpaceId = Number(search_space_id);

	const { tasks, loading, syncTasks, syncDemoTasks, getTasks, completeTask } = useTasks(searchSpaceId);

	const [selectedTask, setSelectedTask] = useState<Task | null>(null);
	const [statusFilter, setStatusFilter] = useState<TaskStatus>("UNDONE");

	// Load tasks on mount
	useEffect(() => {
		if (searchSpaceId) {
			getTasks(statusFilter);
		}
	}, [searchSpaceId, getTasks]);

	// Refresh tasks when status filter changes
	useEffect(() => {
		if (searchSpaceId) {
			getTasks(statusFilter);
		}
	}, [statusFilter, searchSpaceId, getTasks]);

	const handleSyncTasks = async () => {
		// Use demo tasks for now (change to syncTasks(["LINEAR"]) for real Linear integration)
		await syncDemoTasks();
		// Refresh with current filter
		await getTasks(statusFilter);
	};

	const handleCompleteTask = async (taskId: number) => {
		const updatedTask = await completeTask(taskId);
		if (updatedTask) {
			// Update selected task if it's the one that was completed
			if (selectedTask?.id === taskId) {
				setSelectedTask(updatedTask);
			}
			// Refresh the task list
			await getTasks(statusFilter);
		}
	};

	const handleStatusFilterChange = (status: TaskStatus) => {
		setStatusFilter(status);
		// Clear selection when switching tabs
		setSelectedTask(null);
	};

	return (
		<motion.div
			className="flex h-[calc(100vh-4rem)] w-full"
			initial="initial"
			animate="enter"
			exit="exit"
			variants={pageVariants}
		>
			{/* LEFT PANEL: Task List */}
			<div className="w-[400px] border-r flex flex-col bg-background">
				<TaskListPanel
					tasks={tasks}
					selectedTask={selectedTask}
					onSelectTask={setSelectedTask}
					onSyncTasks={handleSyncTasks}
					onCompleteTask={handleCompleteTask}
					statusFilter={statusFilter}
					onStatusFilterChange={handleStatusFilterChange}
					loading={loading}
				/>
			</div>

			{/* RIGHT PANEL: AI Chat */}
			<div className="flex-1 bg-background">
				<TaskChatPanel selectedTask={selectedTask} searchSpaceId={search_space_id as string} />
			</div>
		</motion.div>
	);
}
