import type { TaskPriority, TaskSourceType, TaskStatus } from "@/contracts/enums/task";

export interface Task {
	id: number;
	search_space_id: number;
	user_id: string;
	title: string;
	description?: string;
	source_type: TaskSourceType;
	external_id?: string;
	external_url?: string;
	external_metadata?: any;
	status: TaskStatus;
	priority?: TaskPriority;
	due_date?: string;
	created_at: string;
	updated_at: string;
	completed_at?: string;
	linked_chat_ids?: number[];
	linked_document_ids?: number[];
}

export interface TaskSyncRequest {
	search_space_id: number;
	connector_types: string[];
}

export interface TaskFilterRequest {
	search_space_id: number;
	status?: TaskStatus;
	sort_by_priority?: boolean;
}

export interface TaskCompleteRequest {
	task_id: number;
}

export interface TaskCreate {
	search_space_id: number;
	title: string;
	description?: string;
	priority?: TaskPriority;
	due_date?: string;
}
