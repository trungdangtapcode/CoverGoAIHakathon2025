"use client";

import { type LucideIcon } from "lucide-react";
import { useMemo } from "react";

import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import {
	SidebarGroup,
	SidebarGroupLabel,
	SidebarMenu,
	SidebarMenuAction,
	SidebarMenuButton,
	SidebarMenuItem,
	SidebarMenuSub,
	SidebarMenuSubButton,
	SidebarMenuSubItem,
} from "@/components/ui/sidebar";

interface NavItem {
	title: string;
	url: string;
	icon: LucideIcon;
	isActive?: boolean;
	items?: {
		title: string;
		url: string;
	}[];
}

export function NavMain({ items }: { items: NavItem[] }) {
	// Memoize items to prevent unnecessary re-renders
	const memoizedItems = useMemo(() => items, [items]);

	return (
		<SidebarGroup>
			<SidebarGroupLabel>Platform</SidebarGroupLabel>
			<SidebarMenu>
				{memoizedItems.map((item, index) => (
					<Collapsible key={`${item.title}-${index}`} asChild defaultOpen={item.isActive}>
						<SidebarMenuItem>
							{item.items?.length ? (
								<>
									<CollapsibleTrigger asChild>
										<SidebarMenuButton
											tooltip={item.title}
											isActive={item.isActive}
											aria-label={`${item.title} with submenu`}
											className="w-full"
										>
											<item.icon />
											<span>{item.title}</span>
										</SidebarMenuButton>
									</CollapsibleTrigger>
									<CollapsibleContent className="data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:slide-out-to-top-2 data-[state=open]:slide-in-from-top-2 duration-200">
										<SidebarMenuSub>
											{item.items?.map((subItem, subIndex) => (
												<SidebarMenuSubItem key={`${subItem.title}-${subIndex}`}>
													<SidebarMenuSubButton asChild aria-label={subItem.title}>
														<a href={subItem.url}>
															<span>{subItem.title}</span>
														</a>
													</SidebarMenuSubButton>
												</SidebarMenuSubItem>
											))}
										</SidebarMenuSub>
									</CollapsibleContent>
								</>
							) : (
								<SidebarMenuButton
									asChild
									tooltip={item.title}
									isActive={item.isActive}
									aria-label={item.title}
								>
									<a href={item.url}>
										<item.icon />
										<span>{item.title}</span>
									</a>
								</SidebarMenuButton>
							)}
						</SidebarMenuItem>
					</Collapsible>
				))}
			</SidebarMenu>
		</SidebarGroup>
	);
}
