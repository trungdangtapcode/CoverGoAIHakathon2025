import { notFound } from "next/navigation";

// Temporary placeholder - Fumadocs MDX integration needs fixing
// TODO: Fix fumadocs source integration issue
export default async function Page(props: { params: Promise<{ slug?: string[] }> }) {
	const params = await props.params;
	
	return (
		<div className="container mx-auto py-8">
			<h1 className="text-3xl font-bold mb-4">Documentation</h1>
			<p>Documentation is currently being updated. Please check back soon.</p>
		</div>
	);
}

export async function generateStaticParams() {
	return [];
}

export async function generateMetadata(props: { params: Promise<{ slug?: string[] }> }) {
	return {
		title: "Documentation",
		description: "Surfsense Documentation",
	};
}

// Original code commented out until fumadocs source is fixed
/*
import { DocsBody, DocsDescription, DocsPage, DocsTitle } from "fumadocs-ui/page";
import { source } from "@/lib/source";
import { getMDXComponents } from "@/mdx-components";

const page = source.getPage(params.slug);
if (!page) notFound();

const MDX = page.data.body;

return (
	<DocsPage toc={page.data.toc} full={page.data.full}>
		<DocsTitle>{page.data.title}</DocsTitle>
		<DocsDescription>{page.data.description}</DocsDescription>
		<DocsBody>
			<MDX components={getMDXComponents()} />
		</DocsBody>
	</DocsPage>
);
*/
