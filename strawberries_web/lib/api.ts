/**
 * API client utilities for making authenticated requests
 */

export class ApiError extends Error {
	constructor(
		message: string,
		public status?: number,
		public data?: any
	) {
		super(message);
		this.name = "ApiError";
	}
}

/**
 * Get the authorization token from localStorage
 */
function getAuthToken(): string | null {
	if (typeof window === "undefined") return null;
	return localStorage.getItem("surfsense_bearer_token");
}

/**
 * Get the base URL for API requests
 */
function getBaseUrl(): string {
	return process.env.NEXT_PUBLIC_FASTAPI_BACKEND_URL || "";
}

/**
 * Make an authenticated API request
 */
async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
	const token = getAuthToken();
	const baseUrl = getBaseUrl();

	// Ensure endpoint starts with /
	const normalizedEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
	const url = `${baseUrl}${normalizedEndpoint}`;

	const headers: Record<string, string> = {
		"Content-Type": "application/json",
	};

	// Add any additional headers from options
	if (options.headers) {
		const optionHeaders =
			options.headers instanceof Headers
				? Object.fromEntries(options.headers.entries())
				: Array.isArray(options.headers)
					? Object.fromEntries(options.headers)
					: options.headers;
		Object.assign(headers, optionHeaders);
	}

	if (token) {
		headers.Authorization = `Bearer ${token}`;
	}

	try {
		const response = await fetch(url, {
			...options,
			headers,
		});

		// Handle non-JSON responses
		const contentType = response.headers.get("content-type");
		const isJson = contentType?.includes("application/json");

		if (!response.ok) {
			let errorData: any = {};
			if (isJson) {
				try {
					errorData = await response.json();
				} catch (e) {
					// Ignore JSON parse errors
				}
			}

			throw new ApiError(
				errorData.detail || errorData.message || `HTTP ${response.status}`,
				response.status,
				errorData
			);
		}

		// Return empty object for 204 No Content responses
		if (response.status === 204) {
			return {} as T;
		}

		// Parse JSON response
		if (isJson) {
			return await response.json();
		}

		// Return empty object if no content
		return {} as T;
	} catch (error) {
		if (error instanceof ApiError) {
			throw error;
		}

		// Handle network errors
		if (error instanceof TypeError && error.message.includes("fetch")) {
			throw new ApiError("Network error. Please check your connection.", undefined, error);
		}

		throw new ApiError(
			error instanceof Error ? error.message : "An unknown error occurred",
			undefined,
			error
		);
	}
}

/**
 * API client with common HTTP methods
 */
export const apiClient = {
	/**
	 * Make a GET request
	 */
	async get<T>(endpoint: string, options?: RequestInit): Promise<T> {
		return request<T>(endpoint, {
			...options,
			method: "GET",
		});
	},

	/**
	 * Make a POST request
	 */
	async post<T>(endpoint: string, data?: any, options?: RequestInit): Promise<T> {
		return request<T>(endpoint, {
			...options,
			method: "POST",
			body: data ? JSON.stringify(data) : undefined,
		});
	},

	/**
	 * Make a PUT request
	 */
	async put<T>(endpoint: string, data?: any, options?: RequestInit): Promise<T> {
		return request<T>(endpoint, {
			...options,
			method: "PUT",
			body: data ? JSON.stringify(data) : undefined,
		});
	},

	/**
	 * Make a PATCH request
	 */
	async patch<T>(endpoint: string, data?: any, options?: RequestInit): Promise<T> {
		return request<T>(endpoint, {
			...options,
			method: "PATCH",
			body: data ? JSON.stringify(data) : undefined,
		});
	},

	/**
	 * Make a DELETE request
	 */
	async delete<T>(endpoint: string, options?: RequestInit): Promise<T> {
		return request<T>(endpoint, {
			...options,
			method: "DELETE",
		});
	},
};
