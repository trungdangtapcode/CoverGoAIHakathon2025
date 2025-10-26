import type { ReactNode } from "react";

export default function Layout({ children }: { children: ReactNode }) {
	return <div className="min-h-screen">{children}</div>;
}

// Original code commented out until fumadocs source is fixed
/*
import { DocsLayout } from "fumadocs-ui/layouts/docs";
import type { ReactNode } from "react";
import { baseOptions } from "@/app/layout.config";
import { source } from "@/lib/source";

export default function Layout({ children }: { children: ReactNode }) {
	return (
		<DocsLayout tree={source.pageTree} {...baseOptions}>
			{children}
		</DocsLayout>
	);
}
*/
