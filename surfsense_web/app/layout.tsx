import type { Metadata } from "next";
import "./globals.css";
import { RootProvider } from "fumadocs-ui/provider";
import { Roboto } from "next/font/google";
import { ThemeProvider } from "@/components/theme/theme-provider";
import { Toaster } from "@/components/ui/sonner";
import { cn } from "@/lib/utils";

const roboto = Roboto({
	subsets: ["latin"],
	weight: ["400", "500", "700"],
	display: "swap",
	variable: "--font-roboto",
});

export const metadata: Metadata = {
	title: "Strawberries – AI Workspace for Team Collaboration",
	description:
		"Strawberries is an AI-powered workspace that integrates with your tools to help you efficiently manage, search, and collaborate with your team. Connect any LLM to your internal knowledge sources and chat in real time.",
	keywords: [
		"Strawberries",
		"AI workspace",
		"team collaboration",
		"AI knowledge management",
		"AI assistant",
		"hybrid search",
		"vector search",
		"RAG",
		"LLM apps",
		"knowledge management AI",
		"AI-powered search",
		"team workspace",
		"AI collaboration tools",
		"knowledge base",
	],
	icons: {
		icon: [
			{ url: "/logo.png", sizes: "32x32", type: "image/png" },
			{ url: "/logo.png", sizes: "16x16", type: "image/png" },
		],
		shortcut: "/logo.png",
		apple: "/logo.png",
	},
	openGraph: {
		title: "Strawberries – AI Workspace Built for Teams",
		description:
			"Connect any LLM to your internal knowledge sources and chat with it in real time alongside your team.",
		url: "https://strawberries.app",
		siteName: "Strawberries",
		type: "website",
		locale: "en_US",
	},
	twitter: {
		card: "summary_large_image",
		title: "Strawberries – AI Workspace for Team Collaboration",
		description:
			"Connect any LLM to your internal knowledge sources and collaborate with your team in real time.",
		creator: "https://strawberries.app",
		site: "https://strawberries.app",
	},
};

export default async function RootLayout({
	children,
}: Readonly<{
	children: React.ReactNode;
}>) {
	return (
		<html lang="en" suppressHydrationWarning>
			<head>
				<link rel="icon" href="/logo.png" type="image/png" />
				<link rel="shortcut icon" href="/logo.png" type="image/png" />
			</head>
			<body className={cn(roboto.className, "bg-white dark:bg-black antialiased h-full w-full")}>
				<ThemeProvider
					attribute="class"
					enableSystem
					disableTransitionOnChange
					defaultTheme="light"
				>
					<RootProvider>
						{children}
						<Toaster />
					</RootProvider>
				</ThemeProvider>
			</body>
		</html>
	);
}
