/**
 * Connector utilities and helper functions
 */

/**
 * Get connector type display name
 */
export function getConnectorTypeDisplay(type: string): string {
	const typeMap: Record<string, string> = {
		// Search Connectors
		SERPER_API: "Serper API",
		TAVILY_API: "Tavily API",
		SEARXNG_API: "SearxNG",

		// Workspace Connectors
		GITHUB_CONNECTOR: "GitHub",
		NOTION_CONNECTOR: "Notion",
		SLACK_CONNECTOR: "Slack",
		LINEAR_CONNECTOR: "Linear",
		JIRA_CONNECTOR: "Jira",
		CONFLUENCE_CONNECTOR: "Confluence",
		CLICKUP_CONNECTOR: "ClickUp",
		DISCORD_CONNECTOR: "Discord",
		GOOGLE_CALENDAR_CONNECTOR: "Google Calendar",
		GOOGLE_GMAIL_CONNECTOR: "Gmail",
		AIRTABLE_CONNECTOR: "Airtable",
		LUMA_CONNECTOR: "Luma",
		ELASTICSEARCH_CONNECTOR: "Elasticsearch",

		// File types
		FILE: "File",
		EXTENSION: "Extension",
		CRAWLED_URL: "Crawled URL",
		YOUTUBE_VIDEO: "YouTube Video",
	};

	return typeMap[type] || type.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
}

/**
 * Check if a connector type is a workspace connector
 */
export function isWorkspaceConnector(type: string): boolean {
	const workspaceConnectors = [
		"GITHUB_CONNECTOR",
		"NOTION_CONNECTOR",
		"SLACK_CONNECTOR",
		"LINEAR_CONNECTOR",
		"JIRA_CONNECTOR",
		"CONFLUENCE_CONNECTOR",
		"CLICKUP_CONNECTOR",
		"DISCORD_CONNECTOR",
		"GOOGLE_CALENDAR_CONNECTOR",
		"GOOGLE_GMAIL_CONNECTOR",
		"AIRTABLE_CONNECTOR",
		"LUMA_CONNECTOR",
		"ELASTICSEARCH_CONNECTOR",
	];

	return workspaceConnectors.includes(type);
}

/**
 * Check if a connector type is a search connector
 */
export function isSearchConnector(type: string): boolean {
	const searchConnectors = ["SERPER_API", "TAVILY_API", "SEARXNG_API"];

	return searchConnectors.includes(type);
}

/**
 * Get the connector category
 */
export function getConnectorCategory(type: string): "search" | "workspace" | "file" | "other" {
	if (isSearchConnector(type)) return "search";
	if (isWorkspaceConnector(type)) return "workspace";
	if (["FILE", "EXTENSION", "CRAWLED_URL", "YOUTUBE_VIDEO"].includes(type)) return "file";
	return "other";
}

/**
 * Validate connector configuration
 */
export function validateConnectorConfig(
	type: string,
	config: Record<string, any>
): { valid: boolean; errors: string[] } {
	const errors: string[] = [];

	// Common validations based on connector type
	switch (type) {
		case "SERPER_API":
			if (!config.api_key) {
				errors.push("API key is required for Serper API");
			}
			break;

		case "TAVILY_API":
			if (!config.api_key) {
				errors.push("API key is required for Tavily API");
			}
			break;

		case "SEARXNG_API":
			if (!config.url) {
				errors.push("URL is required for SearxNG");
			}
			break;

		case "GITHUB_CONNECTOR":
			if (!config.access_token) {
				errors.push("Access token is required for GitHub");
			}
			break;

		case "NOTION_CONNECTOR":
			if (!config.access_token) {
				errors.push("Access token is required for Notion");
			}
			break;

		case "SLACK_CONNECTOR":
			if (!config.bot_token) {
				errors.push("Bot token is required for Slack");
			}
			break;

		case "LINEAR_CONNECTOR":
			if (!config.api_key) {
				errors.push("API key is required for Linear");
			}
			break;

		case "JIRA_CONNECTOR":
			if (!config.email || !config.api_token || !config.domain) {
				errors.push("Email, API token, and domain are required for Jira");
			}
			break;

		// Add more validations as needed
	}

	return {
		valid: errors.length === 0,
		errors,
	};
}
