// Temporarily disable search functionality during build
// TODO: Fix fumadocs search integration
export async function GET() {
	return new Response(JSON.stringify({ results: [] }), {
		headers: { "Content-Type": "application/json" },
	});
}

// import { createFromSource } from "fumadocs-core/search/server";
// import { source } from "@/lib/source";
// export const { GET } = createFromSource(source);
