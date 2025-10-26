/**
 * Authentication error handling utilities
 */

export interface AuthErrorDetails {
	title: string;
	description: string;
	shouldRetry?: boolean;
}

/**
 * Check if an error is a network error
 */
export function isNetworkError(error: unknown): boolean {
	if (error instanceof TypeError && error.message.includes("fetch")) {
		return true;
	}
	if (error instanceof Error) {
		return (
			error.message.includes("network") ||
			error.message.includes("Failed to fetch") ||
			error.message.includes("NetworkError")
		);
	}
	return false;
}

/**
 * Check if an error should trigger a retry
 */
export function shouldRetry(errorCode: string): boolean {
	const retryableErrors = [
		"NETWORK_ERROR",
		"TIMEOUT_ERROR",
		"SERVER_ERROR",
		"HTTP 500",
		"HTTP 502",
		"HTTP 503",
		"HTTP 504",
	];

	return retryableErrors.some((retryable) => errorCode.includes(retryable));
}

/**
 * Get detailed error information based on error code
 */
export function getAuthErrorDetails(errorCode: string): AuthErrorDetails {
	// Network errors
	if (isNetworkError(errorCode) || errorCode.includes("NETWORK_ERROR")) {
		return {
			title: "Connection Error",
			description: "Unable to connect to the server. Please check your internet connection.",
			shouldRetry: true,
		};
	}

	// Authentication errors
	if (errorCode.includes("401") || errorCode.includes("Unauthorized")) {
		return {
			title: "Invalid Credentials",
			description: "The username or password you entered is incorrect.",
			shouldRetry: false,
		};
	}

	// Invalid credentials from FastAPI
	if (errorCode.includes("LOGIN_BAD_CREDENTIALS")) {
		return {
			title: "Invalid Credentials",
			description: "The username or password you entered is incorrect.",
			shouldRetry: false,
		};
	}

	// User not found
	if (errorCode.includes("LOGIN_USER_NOT_VERIFIED")) {
		return {
			title: "Email Not Verified",
			description: "Please verify your email address before logging in.",
			shouldRetry: false,
		};
	}

	// Rate limiting
	if (errorCode.includes("429") || errorCode.includes("Too Many Requests")) {
		return {
			title: "Too Many Attempts",
			description: "Too many login attempts. Please try again later.",
			shouldRetry: false,
		};
	}

	// Server errors
	if (errorCode.includes("500") || errorCode.includes("502") || errorCode.includes("503")) {
		return {
			title: "Server Error",
			description: "The server is experiencing issues. Please try again later.",
			shouldRetry: true,
		};
	}

	// Timeout errors
	if (errorCode.includes("timeout") || errorCode.includes("TIMEOUT")) {
		return {
			title: "Request Timeout",
			description: "The request took too long. Please try again.",
			shouldRetry: true,
		};
	}

	// User already exists (registration)
	if (errorCode.includes("REGISTER_USER_ALREADY_EXISTS")) {
		return {
			title: "Account Already Exists",
			description: "An account with this email already exists. Please login instead.",
			shouldRetry: false,
		};
	}

	// Invalid email format
	if (errorCode.includes("value_error.email")) {
		return {
			title: "Invalid Email",
			description: "Please enter a valid email address.",
			shouldRetry: false,
		};
	}

	// Password validation errors
	if (errorCode.includes("password")) {
		return {
			title: "Invalid Password",
			description: "Password must meet the required criteria.",
			shouldRetry: false,
		};
	}

	// Default error
	return {
		title: "Login Failed",
		description: errorCode || "An unexpected error occurred. Please try again.",
		shouldRetry: false,
	};
}
