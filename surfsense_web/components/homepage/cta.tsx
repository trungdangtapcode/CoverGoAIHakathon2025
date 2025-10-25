"use client";
import { IconMessageCircleQuestion } from "@tabler/icons-react";
import Link from "next/link";
import type React from "react";
import { cn } from "@/lib/utils";

export function CTAHomepage() {
	return (
		<section className="w-full grid grid-cols-1 md:grid-cols-3 my-20 md:my-20 justify-start relative z-20 max-w-7xl mx-auto bg-gradient-to-br from-gray-100 to-white dark:from-neutral-900 dark:to-neutral-950">
			<GridLineHorizontal className="top-0" offset="200px" />
			<GridLineHorizontal className="bottom-0 top-auto" offset="200px" />
			<GridLineVertical className="left-0" offset="80px" />
			<GridLineVertical className="left-auto right-0" offset="80px" />
			<div className="md:col-span-3 p-8 md:p-14">
				<h2 className="text-center text-neutral-500 dark:text-neutral-200 text-xl md:text-3xl tracking-tight font-medium">
					Transform how your team{" "}
					<span className="font-bold text-black dark:text-white">discovers and collaborates</span>
				</h2>
				<p className="text-center text-neutral-500 mt-4 mx-auto max-w-2xl dark:text-neutral-200 text-xl md:text-3xl tracking-tight font-medium">
					Unite your <span className="text-sky-700">team's knowledge</span> in one collaborative
					space with <span className="text-indigo-700">intelligent search</span>.
				</p>

				<div className="flex items-center justify-center flex-col sm:flex-row sm:gap-4">
					<Link href="/login">
						<button
							type="button"
							className="mt-8 flex space-x-2 items-center group text-base px-6 py-3 rounded-lg bg-black text-white dark:bg-white dark:text-black shadow-[0px_2px_0px_0px_rgba(255,255,255,0.3)_inset]"
						>
							<span>Get Started</span>
						</button>
					</Link>
				</div>
			</div>
		</section>
	);
}

const GridLineHorizontal = ({ className, offset }: { className?: string; offset?: string }) => {
	return (
		<div
			style={
				{
					"--background": "#ffffff",
					"--color": "rgba(0, 0, 0, 0.2)",
					"--height": "1px",
					"--width": "5px",
					"--fade-stop": "90%",
					"--offset": offset || "200px", //-100px if you want to keep the line inside
					"--color-dark": "rgba(255, 255, 255, 0.2)",
					maskComposite: "exclude",
				} as React.CSSProperties
			}
			className={cn(
				"absolute w-[calc(100%+var(--offset))] h-[var(--height)] left-[calc(var(--offset)/2*-1)]",
				"bg-[linear-gradient(to_right,var(--color),var(--color)_50%,transparent_0,transparent)]",
				"[background-size:var(--width)_var(--height)]",
				"[mask:linear-gradient(to_left,var(--background)_var(--fade-stop),transparent),_linear-gradient(to_right,var(--background)_var(--fade-stop),transparent),_linear-gradient(black,black)]",
				"[mask-composite:exclude]",
				"z-30",
				"dark:bg-[linear-gradient(to_right,var(--color-dark),var(--color-dark)_50%,transparent_0,transparent)]",
				className
			)}
		></div>
	);
};

const GridLineVertical = ({ className, offset }: { className?: string; offset?: string }) => {
	return (
		<div
			style={
				{
					"--background": "#ffffff",
					"--color": "rgba(0, 0, 0, 0.2)",
					"--height": "5px",
					"--width": "1px",
					"--fade-stop": "90%",
					"--offset": offset || "150px", //-100px if you want to keep the line inside
					"--color-dark": "rgba(255, 255, 255, 0.2)",
					maskComposite: "exclude",
				} as React.CSSProperties
			}
			className={cn(
				"absolute h-[calc(100%+var(--offset))] w-[var(--width)] top-[calc(var(--offset)/2*-1)]",
				"bg-[linear-gradient(to_bottom,var(--color),var(--color)_50%,transparent_0,transparent)]",
				"[background-size:var(--width)_var(--height)]",
				"[mask:linear-gradient(to_top,var(--background)_var(--fade-stop),transparent),_linear-gradient(to_bottom,var(--background)_var(--fade-stop),transparent),_linear-gradient(black,black)]",
				"[mask-composite:exclude]",
				"z-30",
				"dark:bg-[linear-gradient(to_bottom,var(--color-dark),var(--color-dark)_50%,transparent_0,transparent)]",
				className
			)}
		></div>
	);
};
