"use client";

import { type ChatHandler, ChatSection as LlamaIndexChatSection } from "@llamaindex/chat-ui";
import { ChevronLeft, ChevronRight, FileText, GripVertical, Plus, RefreshCw, Trash2, Upload, Video, X } from "lucide-react";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
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
	const [uploadingFiles, setUploadingFiles] = useState<File[]>([]);
	const [isUploading, setIsUploading] = useState(false);
	const [uploadProgress, setUploadProgress] = useState(0);
	const fileInputRef = useRef<HTMLInputElement>(null);

	// Manual fetch function that returns documents directly
	const manualFetchDocuments = useCallback(async () => {
		try {
			const token = localStorage.getItem("surfsense_bearer_token");
			const params = new URLSearchParams({
				search_space_id: search_space_id as string,
				page_size: "100",
			});

			const response = await fetch(
				`${process.env.NEXT_PUBLIC_FASTAPI_BACKEND_URL}/api/v1/documents/?${params}`,
				{
					headers: {
						Authorization: `Bearer ${token}`,
					},
				}
			);

			if (!response.ok) {
				throw new Error("Failed to fetch documents");
			}

			const data = await response.json();
			return data.items || [];
		} catch (error) {
			console.error("Error fetching documents:", error);
			return [];
		}
	}, [search_space_id]);

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

	const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
		const files = Array.from(event.target.files || []);
		if (files.length > 0) {
			setUploadingFiles(files);
			handleFileUpload(files);
		}
	};

	const handleFileUpload = async (files: File[]) => {
		if (files.length === 0) return;

		const fileCount = files.length;
		setIsUploading(true);
		setUploadProgress(0);

		const formData = new FormData();
		files.forEach((file) => {
			formData.append("files", file);
		});
		formData.append("search_space_id", search_space_id as string);

		try {
			// Simulate progress for better UX
			const progressInterval = setInterval(() => {
				setUploadProgress((prev) => {
					if (prev >= 90) return prev;
					return prev + Math.random() * 10;
				});
			}, 200);

			const token = localStorage.getItem("surfsense_bearer_token");
			const response = await fetch(
				`${process.env.NEXT_PUBLIC_FASTAPI_BACKEND_URL}/api/v1/documents/fileupload`,
				{
					method: "POST",
					headers: {
						Authorization: `Bearer ${token}`,
					},
					body: formData,
				}
			);

			clearInterval(progressInterval);
			setUploadProgress(100);

			if (!response.ok) {
				throw new Error("Upload failed");
			}

			await response.json();

			// Reset upload state
			setUploadingFiles([]);
			setUploadProgress(0);

			// Poll for documents to appear and auto-select them
			let pollAttempts = 0;
			const maxPollAttempts = 30; // Increased attempts
			let foundNewDocs = false;
			const beforeUploadDocIds = new Set(selectedDocuments.map(doc => doc.id));
			const uploadedFileNames = files.map(f => f.name.toLowerCase());
			
			console.log(`🔍 Starting to poll for new documents. Before upload IDs:`, Array.from(beforeUploadDocIds));
			console.log(`📁 Looking for files with names:`, uploadedFileNames);
			
			while (pollAttempts < maxPollAttempts && !foundNewDocs) {
				// Wait before polling (exponential backoff, capped at 3 seconds)
				const waitTime = Math.min(1000 * Math.pow(1.3, pollAttempts), 3000);
				await new Promise(resolve => setTimeout(resolve, waitTime));
				
				// Manually fetch documents
				const fetchedDocs = await manualFetchDocuments();
				
				console.log(`🔍 Poll attempt ${pollAttempts + 1}: Fetched ${fetchedDocs?.length || 0} documents`);
				
				if (fetchedDocs && fetchedDocs.length > 0) {
					// Find new documents by comparing IDs AND by matching file names
					const newDocs = fetchedDocs.filter((doc: Document) => {
						const isNewById = !beforeUploadDocIds.has(doc.id);
						const isNewByName = uploadedFileNames.some(uploadName => 
							doc.title.toLowerCase().includes(uploadName.replace(/\.[^/.]+$/, "")) // Remove extension for comparison
						);
						return isNewById && isNewByName;
					});
					
					console.log(`🔍 Found ${newDocs.length} new documents by ID and name:`, newDocs.map((doc: Document) => ({ id: doc.id, title: doc.title })));
					
					// If no documents found by name matching, try just by ID (fallback)
					if (newDocs.length === 0) {
						const newDocsById = fetchedDocs.filter((doc: Document) => !beforeUploadDocIds.has(doc.id));
						console.log(`🔍 Fallback: Found ${newDocsById.length} new documents by ID only:`, newDocsById.map((doc: Document) => ({ id: doc.id, title: doc.title })));
						
						if (newDocsById.length > 0) {
							// Auto-select the newly uploaded documents
							const updatedSelectedDocs = [...selectedDocuments, ...newDocsById];
							onDocumentSelectionChange?.(updatedSelectedDocs);
							
							console.log(`✅ Successfully added ${newDocsById.length} new documents to selection (by ID)`);
							toast.success(`${fileCount} file(s) uploaded and added to selection!`);
							foundNewDocs = true;
							break;
						}
					} else {
						// Auto-select the newly uploaded documents
						const updatedSelectedDocs = [...selectedDocuments, ...newDocs];
						onDocumentSelectionChange?.(updatedSelectedDocs);
						
						console.log(`✅ Successfully added ${newDocs.length} new documents to selection (by name match)`);
						toast.success(`${fileCount} file(s) uploaded and added to selection!`);
						foundNewDocs = true;
						break;
					}
				}
				
				pollAttempts++;
			}

			if (!foundNewDocs) {
				console.log(`⚠️ Polling completed but no new documents found after ${maxPollAttempts} attempts`);
				console.log(`📊 Final state - Selected docs: ${selectedDocuments.length}, Before upload IDs: ${beforeUploadDocIds.size}`);
				toast.info(`${fileCount} file(s) uploaded. They will appear once processing completes.`);
			}
			
			// Clear the file input
			if (fileInputRef.current) {
				fileInputRef.current.value = "";
			}
		} catch (error: any) {
			toast.error(`Upload failed: ${error.message}`);
		} finally {
			setIsUploading(false);
		}
	};

	const handleUploadClick = () => {
		fileInputRef.current?.click();
	};

	const handleRefreshDocuments = async () => {
		console.log(`🔄 Manually refreshing documents...`);
		console.log(`📊 Current selected documents:`, selectedDocuments.map(doc => ({ id: doc.id, title: doc.title })));
		
		const fetchedDocs = await manualFetchDocuments();
		console.log(`📄 Fetched ${fetchedDocs?.length || 0} documents:`, fetchedDocs?.map((doc: Document) => ({ id: doc.id, title: doc.title })));
		
		if (fetchedDocs && fetchedDocs.length > 0) {
			// Find documents that aren't currently selected
			const currentDocIds = new Set(selectedDocuments.map(doc => doc.id));
			const newDocs = fetchedDocs.filter((doc: Document) => !currentDocIds.has(doc.id));
			
			if (newDocs.length > 0) {
				console.log(`🆕 Found ${newDocs.length} unselected documents:`, newDocs.map((doc: Document) => ({ id: doc.id, title: doc.title })));
				
				// Auto-select the unselected documents
				const updatedSelectedDocs = [...selectedDocuments, ...newDocs];
				onDocumentSelectionChange?.(updatedSelectedDocs);
				
				console.log(`✅ Auto-selected ${newDocs.length} new documents`);
				toast.success(`Found and selected ${newDocs.length} new documents!`);
			} else {
				console.log(`✅ All documents are already selected`);
				toast.info(`All available documents are already selected.`);
			}
		}
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
							<Label className="text-xs font-medium">Selected Documents ({selectedDocuments.length})</Label>
							<Button
								size="sm"
								variant="ghost"
								className="h-6 w-6 p-0"
								onClick={handleRefreshDocuments}
								title="Refresh and auto-select new documents"
							>
								<RefreshCw className="h-3 w-3" />
							</Button>
						</div>

						<ScrollArea className="flex-1 border rounded-md">
							{selectedDocuments.length === 0 ? (
								<div className="flex flex-col items-center justify-center h-full text-center p-4">
									<FileText className="h-10 w-10 text-muted-foreground mb-2" />
									<p className="text-xs text-muted-foreground">No documents</p>
									<div className="flex flex-col gap-2 mt-3">
										<Button
											size="sm"
											variant="outline"
											className="h-7 text-xs"
											onClick={handleUploadClick}
											disabled={isUploading}
										>
											<Upload className="h-3 w-3 mr-1" />
											{isUploading ? "Uploading..." : "Upload Files"}
										</Button>
										<Button
											size="sm"
											variant="ghost"
											className="h-7 text-xs"
											onClick={() => setDocumentDialogOpen(true)}
										>
											<Plus className="h-3 w-3 mr-1" />
											Select Existing
										</Button>
									</div>
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

			{/* Hidden file input */}
			<input
				ref={fileInputRef}
				type="file"
				multiple
				accept=".pdf,.doc,.docx,.txt,.md,.rtf,.odt,.html,.htm,.xml,.json,.csv,.xlsx,.xls,.pptx,.ppt"
				onChange={handleFileSelect}
				className="hidden"
			/>

			{/* Upload progress indicator */}
			{isUploading && (
				<div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
					<div className="bg-background p-6 rounded-lg shadow-lg max-w-sm w-full mx-4">
						<div className="text-center space-y-4">
							<div className="animate-spin h-8 w-8 border-2 border-primary border-t-transparent rounded-full mx-auto" />
							<div>
								<h3 className="font-semibold">Uploading Files</h3>
								<p className="text-sm text-muted-foreground">
									{uploadingFiles.length} file(s) being processed...
								</p>
							</div>
							<div className="w-full bg-secondary rounded-full h-2">
								<div
									className="bg-primary h-2 rounded-full transition-all duration-300"
									style={{ width: `${uploadProgress}%` }}
								/>
							</div>
							<p className="text-xs text-muted-foreground">
								{Math.round(uploadProgress)}% complete
							</p>
						</div>
					</div>
				</div>
			)}
		</div>
	);
}
