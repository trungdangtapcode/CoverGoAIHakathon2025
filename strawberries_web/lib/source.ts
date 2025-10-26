import { loader } from "fumadocs-core/source";
import type { InferPageType } from "fumadocs-core/source";
import { docs } from "@/.source";

// Use the built-in method to convert to Fumadocs source
const fumadocsSource = docs.toFumadocsSource();

export const source = loader({
	baseUrl: "/docs",
	source: fumadocsSource,
});

export type Page = InferPageType<typeof source>;
