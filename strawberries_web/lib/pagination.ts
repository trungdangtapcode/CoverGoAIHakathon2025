/**
 * Pagination utilities for normalizing API responses
 */

export interface PaginatedResponse<T> {
	items: T[];
	total: number;
	page?: number;
	pageSize?: number;
	totalPages?: number;
}

/**
 * Normalize list responses from the API
 * Handles both paginated and non-paginated responses
 */
export function normalizeListResponse<T>(data: any): PaginatedResponse<T> {
	// If data is already an array, wrap it
	if (Array.isArray(data)) {
		return {
			items: data,
			total: data.length,
		};
	}

	// If data has items property (paginated response)
	if (data && typeof data === "object") {
		// Handle different pagination response formats
		const items = data.items || data.results || data.data || [];
		const total = data.total ?? data.count ?? data.total_count ?? items.length;
		const page = data.page ?? data.current_page;
		const pageSize = data.page_size ?? data.limit ?? data.per_page;
		const totalPages = data.total_pages ?? (pageSize ? Math.ceil(total / pageSize) : undefined);

		return {
			items,
			total,
			page,
			pageSize,
			totalPages,
		};
	}

	// Fallback: empty response
	return {
		items: [],
		total: 0,
	};
}

/**
 * Calculate pagination metadata
 */
export function getPaginationInfo(total: number, page: number = 1, pageSize: number = 10) {
	const totalPages = Math.ceil(total / pageSize);
	const hasNextPage = page < totalPages;
	const hasPreviousPage = page > 1;

	return {
		total,
		page,
		pageSize,
		totalPages,
		hasNextPage,
		hasPreviousPage,
	};
}
