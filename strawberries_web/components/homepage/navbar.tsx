"use client";
import { IconMenu2, IconX } from "@tabler/icons-react";
import { AnimatePresence, motion } from "motion/react";
import Link from "next/link";
import React, { useEffect, useState } from "react";
import { Logo } from "@/components/Logo";
import { ThemeTogglerComponent } from "@/components/theme/theme-toggle";
import { cn } from "@/lib/utils";

export const Navbar = () => {
	const [isScrolled, setIsScrolled] = useState(false);

	const navItems = [
		{ name: "Home", link: "/" },
		{ name: "Sign In", link: "/login" },
	];

	useEffect(() => {
		const handleScroll = () => {
			setIsScrolled(window.scrollY > 20);
		};

		window.addEventListener("scroll", handleScroll);
		return () => window.removeEventListener("scroll", handleScroll);
	}, []);

	return (
		<div className="fixed top-1 left-0 right-0 z-[60] w-full">
			<DesktopNav navItems={navItems} isScrolled={isScrolled} />
			<MobileNav navItems={navItems} isScrolled={isScrolled} />
		</div>
	);
};

const DesktopNav = ({ navItems, isScrolled }: any) => {
	const [hovered, setHovered] = useState<number | null>(null);
	return (
		<motion.div
			onMouseLeave={() => {
				setHovered(null);
			}}
			className={cn(
				"mx-auto hidden w-full max-w-7xl flex-row items-center justify-between self-start rounded-full px-4 py-2 lg:flex transition-all duration-300",
				isScrolled
					? "bg-white/80 backdrop-blur-md border border-white/20 shadow-lg dark:bg-neutral-950/80 dark:border-neutral-800/50"
					: "bg-transparent border border-transparent"
			)}
		>
			<div className="flex flex-row items-center gap-2">
				<Logo className="h-8 w-8 rounded-md" />
				<span className="dark:text-white/90 text-gray-800 text-lg font-bold">Strawberries</span>
			</div>
			<div className="hidden flex-1 flex-row items-center justify-center space-x-2 text-sm font-medium text-zinc-600 transition duration-200 hover:text-zinc-800 lg:flex lg:space-x-2">
				{navItems.map((navItem: any, idx: number) => (
					<Link
						onMouseEnter={() => setHovered(idx)}
						className="relative px-4 py-2 text-neutral-600 dark:text-neutral-300"
						key={`link=${idx}`}
						href={navItem.link}
					>
						{hovered === idx && (
							<motion.div
								layoutId="hovered"
								className="absolute inset-0 h-full w-full rounded-full bg-gray-100 dark:bg-neutral-800"
							/>
						)}
						<span className="relative z-20">{navItem.name}</span>
					</Link>
				))}
			</div>
			<div className="flex items-center gap-2">
				<ThemeTogglerComponent />
			</div>
		</motion.div>
	);
};

const MobileNav = ({ navItems, isScrolled }: any) => {
	const [open, setOpen] = useState(false);

	return (
		<>
			<motion.div
				animate={{ borderRadius: open ? "4px" : "2rem" }}
				key={String(open)}
				className={cn(
					"mx-auto flex w-full max-w-[calc(100vw-2rem)] flex-col items-center justify-between px-4 py-2 lg:hidden transition-all duration-300",
					isScrolled
						? "bg-white/80 backdrop-blur-md border border-white/20 shadow-lg dark:bg-neutral-950/80 dark:border-neutral-800/50"
						: "bg-transparent border border-transparent"
				)}
			>
				<div className="flex w-full flex-row items-center justify-between">
					<div className="flex flex-row items-center gap-2">
						<Logo className="h-8 w-8 rounded-md" />
						<span className="dark:text-white/90 text-gray-800 text-lg font-bold">Strawberries</span>
					</div>
					<button
						type="button"
						onClick={() => setOpen(!open)}
						className="relative z-50 flex items-center justify-center p-2 -mr-2 rounded-lg hover:bg-gray-100 dark:hover:bg-neutral-800 transition-colors touch-manipulation"
						aria-label={open ? "Close menu" : "Open menu"}
					>
						{open ? (
							<IconX className="h-6 w-6 text-black dark:text-white" />
						) : (
							<IconMenu2 className="h-6 w-6 text-black dark:text-white" />
						)}
					</button>
				</div>

				<AnimatePresence>
					{open && (
						<motion.div
							initial={{ opacity: 0 }}
							animate={{ opacity: 1 }}
							exit={{ opacity: 0 }}
							className="absolute inset-x-0 top-16 z-20 flex w-full flex-col items-start justify-start gap-4 rounded-lg bg-white/80 backdrop-blur-md border border-white/20 shadow-lg px-4 py-8 dark:bg-neutral-950/80 dark:border-neutral-800/50"
						>
							{navItems.map((navItem: any, idx: number) => (
								<Link
									key={`link=${idx}`}
									href={navItem.link}
									className="relative text-neutral-600 dark:text-neutral-300"
								>
									<motion.span className="block">{navItem.name} </motion.span>
								</Link>
							))}
							<div className="flex w-full items-center gap-2 pt-2">
								<ThemeTogglerComponent />
							</div>
						</motion.div>
					)}
				</AnimatePresence>
			</motion.div>
		</>
	);
};
