"use client";

import { type ChatHandler, ChatSection as LlamaIndexChatSection } from "@llamaindex/chat-ui";
import { ChevronLeft, ChevronRight, FileText, GripVertical, Plus, Trash2, Video, X } from "lucide-react";
import { useParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import type { ResearchMode } from "@/components/chat";
import { ChatInputUI } from "@/components/chat/ChatInputGroup";
import { ChatMessagesUI } from "@/components/chat/ChatMessages";
import { DocumentsDataTable } from "@/components/chat/DocumentsDataTable";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { Document } from "@/hooks/use-documents";

interface ChatInterfaceProps {
	handler: ChatHandler;
	onDocumentSelectionChange?: (documents: Document[]) => void;
	selectedDocuments?: Document[];
	youtubeUrls?: string[];
	onYoutubeUrlsChange?: (urls: string[]) => void;
	onConnectorSelectionChange?: (connectorTypes: string[]) => void;
	selectedConnectors?: string[];
	searchMode?: "DOCUMENTS" | "CHUNKS";
	onSearchModeChange?: (mode: "DOCUMENTS" | "CHUNKS") => void;
	researchMode?: ResearchMode;
	onResearchModeChange?: (mode: ResearchMode) => void;
}

export default function ChatInterface({
	handler,
	onDocumentSelectionChange,
	selectedDocuments = [],
	youtubeUrls = [],
	onYoutubeUrlsChange,
	onConnectorSelectionChange,
	selectedConnectors = [],
	searchMode,
	onSearchModeChange,
	researchMode,
	onResearchModeChange,
}: ChatInterfaceProps) {
	const { search_space_id } = useParams();
	const [activeTab, setActiveTab] = useState<string>("documents");
	const [newYoutubeUrl, setNewYoutubeUrl] = useState("");
	const [documentDialogOpen, setDocumentDialogOpen] = useState(false);
	const [panelCollapsed, setPanelCollapsed] = useState(false);

	const totalResources = selectedDocuments.length + youtubeUrls.length;


	const handleRemoveDocument = (docId: number) => {
		const newDocs = selectedDocuments.filter((doc) => doc.id !== docId);
		onDocumentSelectionChange?.(newDocs);
	};

	const handleAddYoutubeUrl = () => {
		if (newYoutubeUrl.trim() && !youtubeUrls.includes(newYoutubeUrl.trim())) {
			onYoutubeUrlsChange?.([...youtubeUrls, newYoutubeUrl.trim()]);
			setNewYoutubeUrl("");
			toast.success("YouTube URL added");
		}
	};

	const handleRemoveYoutubeUrl = (url: string) => {
		onYoutubeUrlsChange?.(youtubeUrls.filter((u) => u !== url));
	};

	const handleDocumentSelection = (documents: Document[]) => {
		onDocumentSelectionChange?.(documents);
	};

	const handleDocumentDone = () => {
		setDocumentDialogOpen(false);
	};

	return (
		<div className="flex h-full w-full relative">
			{/* Main Chat Area */}
			<LlamaIndexChatSection handler={handler} className="flex flex-1 flex-col min-w-0">
				<ChatMessagesUI />
				<div className="border-t p-4">
					<ChatInputUI
						onDocumentSelectionChange={onDocumentSelectionChange}
						selectedDocuments={selectedDocuments}
						onConnectorSelectionChange={onConnectorSelectionChange}
						selectedConnectors={selectedConnectors}
						searchMode={searchMode}
						onSearchModeChange={onSearchModeChange}
						researchMode={researchMode}
						onResearchModeChange={onResearchModeChange}
					/>
				</div>
			</LlamaIndexChatSection>

			{/* Right Side Resource Panel */}
			<div className={`${panelCollapsed ? 'w-12' : 'w-80'} border-l flex flex-col bg-background flex-shrink-0 transition-all duration-200`}>
				<div className="px-4 py-3 border-b">
					<div className="flex items-center justify-between">
						<div className="flex items-center gap-2">
							<FileText className="h-5 w-5 text-primary" />
							{!panelCollapsed && <h3 className="font-semibold">Resources</h3>}
							{!panelCollapsed && <Badge variant="secondary">{totalResources}</Badge>}
						</div>
						<Button
							variant="ghost"
							size="icon"
							className="h-6 w-6"
							onClick={() => setPanelCollapsed(!panelCollapsed)}
						>
							{panelCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
						</Button>
					</div>
				</div>

				{!panelCollapsed && (
					<Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col min-h-0">
					<TabsList className="mx-4 mt-2 grid w-auto grid-cols-2">
						<TabsTrigger value="documents" className="gap-2 text-xs">
							<FileText className="h-3.5 w-3.5" />
							Docs ({selectedDocuments.length})
						</TabsTrigger>
						<TabsTrigger value="youtube" className="gap-2 text-xs">
							<Video className="h-3.5 w-3.5" />
							URLs ({youtubeUrls.length})
						</TabsTrigger>
					</TabsList>

					{/* Documents Tab */}
					<TabsContent value="documents" className="flex-1 px-4 pb-4 mt-2 flex flex-col min-h-0">
						<div className="flex items-center justify-between mb-3">
							<Label className="text-xs font-medium">Selected Documents</Label>
							<Button size="sm" variant="outline" className="h-7 text-xs" onClick={() => setDocumentDialogOpen(true)}>
								<Plus className="h-3 w-3 mr-1" />
								Add
							</Button>
						</div>

						<ScrollArea className="flex-1 border rounded-md">
							{selectedDocuments.length === 0 ? (
								<div className="flex flex-col items-center justify-center h-full text-center p-4">
									<FileText className="h-10 w-10 text-muted-foreground mb-2" />
									<p className="text-xs text-muted-foreground">No documents</p>
									<Button
										size="sm"
										variant="outline"
										className="mt-3 h-7 text-xs"
										onClick={() => setDocumentDialogOpen(true)}
									>
										<Plus className="h-3 w-3 mr-1" />
										Add
									</Button>
								</div>
							) : (
								<div className="p-2 space-y-2">
									{selectedDocuments.map((doc) => (
										<div
											key={doc.id}
											className="flex items-start gap-2 p-2 rounded-md border hover:bg-accent/50 transition-colors group"
										>
											<FileText className="h-3.5 w-3.5 mt-0.5 text-primary flex-shrink-0" />
											<div className="flex-1 min-w-0">
												<p className="font-medium text-xs truncate">{doc.title}</p>
												<Badge variant="outline" className="text-[10px] px-1 py-0 mt-1">
													{doc.document_type}
												</Badge>
											</div>
											<Button
												size="icon"
												variant="ghost"
												className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
												onClick={() => handleRemoveDocument(doc.id)}
											>
												<Trash2 className="h-3 w-3" />
											</Button>
										</div>
									))}
								</div>
							)}
						</ScrollArea>
					</TabsContent>

					{/* YouTube Tab */}
					<TabsContent value="youtube" className="flex-1 px-4 pb-4 mt-2 flex flex-col min-h-0 space-y-3">
						<div className="space-y-2">
							<Label className="text-xs font-medium">Add YouTube URL</Label>
							<div className="flex gap-1">
								<Input
									placeholder="YouTube URL..."
									value={newYoutubeUrl}
									onChange={(e) => setNewYoutubeUrl(e.target.value)}
									onKeyPress={(e) => {
										if (e.key === "Enter") {
											handleAddYoutubeUrl();
										}
									}}
									className="h-8 text-xs"
								/>
								<Button size="icon" onClick={handleAddYoutubeUrl} className="h-8 w-8 flex-shrink-0">
									<Plus className="h-3.5 w-3.5" />
								</Button>
							</div>
						</div>

						<div className="flex-1 min-h-0 flex flex-col">
							<Label className="text-xs font-medium mb-2">Added URLs</Label>
							<ScrollArea className="flex-1 border rounded-md">
								{youtubeUrls.length === 0 ? (
									<div className="flex flex-col items-center justify-center h-full text-center p-4">
										<Video className="h-10 w-10 text-muted-foreground mb-2" />
										<p className="text-xs text-muted-foreground">No URLs added</p>
									</div>
								) : (
									<div className="p-2 space-y-2">
										{youtubeUrls.map((url, index) => (
											<div
												key={index}
												className="flex items-start gap-2 p-2 rounded-md border hover:bg-accent/50 transition-colors group"
											>
												<Video className="h-3.5 w-3.5 mt-0.5 text-primary flex-shrink-0" />
												<div className="flex-1 min-w-0">
													<p className="text-xs truncate">{url}</p>
												</div>
												<Button
													size="icon"
													variant="ghost"
													className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0"
													onClick={() => handleRemoveYoutubeUrl(url)}
												>
													<Trash2 className="h-3 w-3" />
												</Button>
											</div>
										))}
									</div>
								)}
							</ScrollArea>
						</div>
					</TabsContent>
					</Tabs>
				)}
			</div>

			{/* Document Selection Dialog */}
			<Dialog open={documentDialogOpen} onOpenChange={setDocumentDialogOpen}>
				<DialogContent className="max-w-[95vw] md:max-w-5xl h-[90vh] md:h-[85vh] p-0 flex flex-col">
					<div className="flex flex-col h-full">
						<div className="px-4 md:px-6 py-4 border-b flex-shrink-0">
							<DialogTitle className="text-lg md:text-xl">Select Documents</DialogTitle>
							<DialogDescription className="mt-1 text-sm">
								Choose documents to include in your chat
							</DialogDescription>
						</div>

						<div className="flex-1 min-h-0 p-4 md:p-6">
							<DocumentsDataTable
								searchSpaceId={Number(search_space_id)}
								onSelectionChange={handleDocumentSelection}
								onDone={handleDocumentDone}
								initialSelectedDocuments={selectedDocuments}
							/>
						</div>
					</div>
				</DialogContent>
			</Dialog>
		</div>
	);
}
