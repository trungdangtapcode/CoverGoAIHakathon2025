"use client";

import { format } from "date-fns";
import {
	Calendar,
	CheckCircle,
	Circle,
	ExternalLink,
	FileText,
	MessageCircleMore,
	MoreHorizontal,
	Plus,
	Podcast,
	Search,
	Tag,
	Trash2,
	Upload,
	Video,
	X,
	Cable,
} from "lucide-react";
import { AnimatePresence, motion, type Variants } from "motion/react";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import {
	Dialog,
	DialogContent,
	DialogDescription,
	DialogFooter,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/dialog";
import {
	DropdownMenu,
	DropdownMenuContent,
	DropdownMenuItem,
	DropdownMenuSeparator,
	DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
// UI Components
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
	Pagination,
	PaginationContent,
	PaginationItem,
	PaginationLink,
	PaginationNext,
	PaginationPrevious,
} from "@/components/ui/pagination";
import {
	Select,
	SelectContent,
	SelectGroup,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { useDocuments, type Document } from "@/hooks/use-documents";
import { useSearchSourceConnectors } from "@/hooks/use-search-source-connectors";
import { getConnectorIcon } from "@/contracts/enums/connectorIcons";

interface Chat {
	created_at: string;
	id: number;
	type: string;
	title: string;
	search_space_id: number;
}

interface ChatsPageClientProps {
	searchSpaceId: string;
}

const pageVariants: Variants = {
	initial: { opacity: 0 },
	enter: { opacity: 1, transition: { duration: 0.3, ease: "easeInOut" } },
	exit: { opacity: 0, transition: { duration: 0.3, ease: "easeInOut" } },
};

const chatCardVariants: Variants = {
	initial: { y: 20, opacity: 0 },
	animate: { y: 0, opacity: 1 },
	exit: { y: -20, opacity: 0 },
};

const MotionCard = motion(Card);

export default function ChatsPageClient({ searchSpaceId }: ChatsPageClientProps) {
	const router = useRouter();
	const [chats, setChats] = useState<Chat[]>([]);
	const [filteredChats, setFilteredChats] = useState<Chat[]>([]);
	const [isLoading, setIsLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);
	const [searchQuery, setSearchQuery] = useState("");
	const [currentPage, setCurrentPage] = useState(1);
	const [totalPages, setTotalPages] = useState(1);
	const [selectedType, setSelectedType] = useState<string>("all");
	const [sortOrder, setSortOrder] = useState<string>("newest");
	const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
	const [chatToDelete, setChatToDelete] = useState<{ id: number; title: string } | null>(null);
	const [isDeleting, setIsDeleting] = useState(false);

	// New state for podcast generation
	const [selectedChats, setSelectedChats] = useState<number[]>([]);
	const [selectionMode, setSelectionMode] = useState(false);
	const [podcastDialogOpen, setPodcastDialogOpen] = useState(false);
	const [podcastTitle, setPodcastTitle] = useState("");
	const [isGeneratingPodcast, setIsGeneratingPodcast] = useState(false);

	// New state for individual podcast generation
	const [currentChatIndex, setCurrentChatIndex] = useState(0);
	const [podcastTitles, setPodcastTitles] = useState<{ [key: number]: string }>({});
	const [processingChat, setProcessingChat] = useState<Chat | null>(null);

	// New state for chat creation
	const [createChatDialogOpen, setCreateChatDialogOpen] = useState(false);
	const [newChatTitle, setNewChatTitle] = useState("");
	const [selectedDocuments, setSelectedDocuments] = useState<number[]>([]);
	const [newChatYoutubeUrls, setNewChatYoutubeUrls] = useState<string[]>([]);
	const [newYoutubeInput, setNewYoutubeInput] = useState("");
	const [selectedConnectors, setSelectedConnectors] = useState<string[]>([]);
	const [isCreatingChat, setIsCreatingChat] = useState(false);
	
	// Document/URL/Connector picker dialogs
	const [documentPickerOpen, setDocumentPickerOpen] = useState(false);
	const [urlPickerOpen, setUrlPickerOpen] = useState(false);
	const [connectorPickerOpen, setConnectorPickerOpen] = useState(false);
	const [documentSearchQuery, setDocumentSearchQuery] = useState("");
	const [showUploadSection, setShowUploadSection] = useState(false);
	const [uploadingFiles, setUploadingFiles] = useState<File[]>([]);
	const [isUploading, setIsUploading] = useState(false);
	const [uploadProgress, setUploadProgress] = useState(0);
	const [processingDocuments, setProcessingDocuments] = useState<{id: number, name: string}[]>([]);
	const [activeTab, setActiveTab] = useState<string>("existing");
	const [localDocuments, setLocalDocuments] = useState<Document[]>([]);
	
	// Use documents hook for fetching
	const {
		documents: availableDocuments,
		loading: documentsLoading,
		searchDocuments: searchAvailableDocuments,
	} = useDocuments(parseInt(searchSpaceId), { lazy: true, pageSize: 100 });

	// Connector hook - get actual configured connectors
	const { connectors, isLoading: connectorsLoading, fetchConnectors } = useSearchSourceConnectors(false, parseInt(searchSpaceId));

	// Manual fetch function that updates local state
	const manualFetchDocuments = useCallback(async () => {
		try {
			const token = localStorage.getItem("surfsense_bearer_token");
			const params = new URLSearchParams({
				search_space_id: searchSpaceId,
				page_size: "100",
			});

			const response = await fetch(
				`${process.env.NEXT_PUBLIC_FASTAPI_BACKEND_URL}/api/v1/documents?${params.toString()}`,
				{
					headers: {
						Authorization: `Bearer ${token}`,
					},
					method: "GET",
				}
			);

			if (response.ok) {
				const data = await response.json();
				// Handle both array and paginated response formats
				const docs = Array.isArray(data) ? data : (data.items || []);
				setLocalDocuments(docs);
				return docs;
			}
		} catch (error) {
			console.error('Error fetching documents:', error);
		}
		return null;
	}, [searchSpaceId]);

	// Sync local documents with hook documents when hook updates
	useEffect(() => {
		if (availableDocuments.length > 0 && localDocuments.length === 0) {
			setLocalDocuments(availableDocuments);
		}
	}, [availableDocuments, localDocuments.length]);

	// Use local documents if available, otherwise use hook documents
	const displayDocuments = localDocuments.length > 0 ? localDocuments : availableDocuments;

	const chatsPerPage = 9;
	const searchParams = useSearchParams();

	// Get initial page from URL params if it exists
	useEffect(() => {
		const pageParam = searchParams.get("page");
		if (pageParam) {
			const pageNumber = parseInt(pageParam, 10);
			if (!Number.isNaN(pageNumber) && pageNumber > 0) {
				setCurrentPage(pageNumber);
			}
		}
	}, [searchParams]);

	// Fetch chats from API
	useEffect(() => {
		const fetchChats = async () => {
			try {
				setIsLoading(true);

				// Get token from localStorage
				const token = localStorage.getItem("surfsense_bearer_token");

				if (!token) {
					setError("Authentication token not found. Please log in again.");
					setIsLoading(false);
					return;
				}

				// Fetch all chats for this search space
				const response = await fetch(
					`${process.env.NEXT_PUBLIC_FASTAPI_BACKEND_URL}/api/v1/chats/?search_space_id=${searchSpaceId}`,
					{
						headers: {
							Authorization: `Bearer ${token}`,
							"Content-Type": "application/json",
						},
						cache: "no-store",
					}
				);

				if (!response.ok) {
					const errorData = await response.json().catch(() => null);
					throw new Error(`Failed to fetch chats: ${response.status} ${errorData?.error || ""}`);
				}

				const data: Chat[] = await response.json();
				setChats(data);
				setFilteredChats(data);
				setError(null);
			} catch (error) {
				console.error("Error fetching chats:", error);
				setError(error instanceof Error ? error.message : "Unknown error occurred");
				setChats([]);
				setFilteredChats([]);
			} finally {
				setIsLoading(false);
			}
		};

		fetchChats();
	}, [searchSpaceId]);

	// Filter and sort chats based on search query, type, and sort order
	useEffect(() => {
		let result = [...chats];

		// Filter by search term
		if (searchQuery) {
			const query = searchQuery.toLowerCase();
			result = result.filter((chat) => chat.title.toLowerCase().includes(query));
		}

		// Filter by type
		if (selectedType !== "all") {
			result = result.filter((chat) => chat.type === selectedType);
		}

		// Sort chats
		result.sort((a, b) => {
			const dateA = new Date(a.created_at).getTime();
			const dateB = new Date(b.created_at).getTime();

			return sortOrder === "newest" ? dateB - dateA : dateA - dateB;
		});

		setFilteredChats(result);
		setTotalPages(Math.max(1, Math.ceil(result.length / chatsPerPage)));

		// Reset to first page when filters change
		if (currentPage !== 1 && (searchQuery || selectedType !== "all" || sortOrder !== "newest")) {
			setCurrentPage(1);
		}
	}, [chats, searchQuery, selectedType, sortOrder, currentPage]);

	// Function to handle chat deletion
	const handleDeleteChat = async () => {
		if (!chatToDelete) return;

		setIsDeleting(true);
		try {
			const token = localStorage.getItem("surfsense_bearer_token");
			if (!token) {
				setIsDeleting(false);
				return;
			}

			const response = await fetch(
				`${process.env.NEXT_PUBLIC_FASTAPI_BACKEND_URL}/api/v1/chats/${chatToDelete.id}`,
				{
					method: "DELETE",
					headers: {
						Authorization: `Bearer ${token}`,
						"Content-Type": "application/json",
					},
				}
			);

			if (!response.ok) {
				throw new Error(`Failed to delete chat: ${response.statusText}`);
			}

			// Close dialog and refresh chats
			setDeleteDialogOpen(false);
			setChatToDelete(null);

			// Update local state by removing the deleted chat
			setChats((prevChats) => prevChats.filter((chat) => chat.id !== chatToDelete.id));
		} catch (error) {
			console.error("Error deleting chat:", error);
		} finally {
			setIsDeleting(false);
		}
	};

	// Calculate pagination
	const indexOfLastChat = currentPage * chatsPerPage;
	const indexOfFirstChat = indexOfLastChat - chatsPerPage;
	const currentChats = filteredChats.slice(indexOfFirstChat, indexOfLastChat);

	// Get unique chat types for filter dropdown
	const chatTypes = ["all", ...Array.from(new Set(chats.map((chat) => chat.type)))];

	// Generate individual podcasts from selected chats
	const handleGeneratePodcast = async () => {
		if (selectedChats.length === 0) {
			toast.error("Please select at least one chat");
			return;
		}

		const currentChatId = selectedChats[currentChatIndex];
		const currentTitle = podcastTitles[currentChatId] || podcastTitle;

		if (!currentTitle.trim()) {
			toast.error("Please enter a podcast title");
			return;
		}

		setIsGeneratingPodcast(true);
		try {
			const token = localStorage.getItem("surfsense_bearer_token");
			if (!token) {
				toast.error("Authentication error. Please log in again.");
				setIsGeneratingPodcast(false);
				return;
			}

			// Create payload for single chat
			const payload = {
				type: "CHAT",
				ids: [currentChatId], // Single chat ID
				search_space_id: parseInt(searchSpaceId),
				podcast_title: currentTitle,
			};

			const response = await fetch(
				`${process.env.NEXT_PUBLIC_FASTAPI_BACKEND_URL}/api/v1/podcasts/generate/`,
				{
					method: "POST",
					headers: {
						Authorization: `Bearer ${token}`,
						"Content-Type": "application/json",
					},
					body: JSON.stringify(payload),
				}
			);

			if (!response.ok) {
				const errorData = await response.json().catch(() => ({}));
				throw new Error(errorData.detail || "Failed to generate podcast");
			}

			const _data = await response.json();
			toast.success(`Podcast "${currentTitle}" generation started!`);

			// Move to the next chat or finish
			if (currentChatIndex < selectedChats.length - 1) {
				// Set up for next chat
				setCurrentChatIndex(currentChatIndex + 1);

				// Find the next chat from the chats array
				const nextChatId = selectedChats[currentChatIndex + 1];
				const nextChat = chats.find((chat) => chat.id === nextChatId) || null;
				setProcessingChat(nextChat);

				// Default title for the next chat
				if (!podcastTitles[nextChatId]) {
					setPodcastTitle(nextChat?.title || `Podcast from Chat ${nextChatId}`);
				} else {
					setPodcastTitle(podcastTitles[nextChatId]);
				}

				setIsGeneratingPodcast(false);
			} else {
				// All done
				finishPodcastGeneration();
			}
		} catch (error) {
			console.error("Error generating podcast:", error);
			toast.error(error instanceof Error ? error.message : "Failed to generate podcast");
			setIsGeneratingPodcast(false);
		}
	};

	// Helper to finish the podcast generation process
	const finishPodcastGeneration = () => {
		toast.success("All podcasts are being generated! Check the logs tab to see their status.");
		setPodcastDialogOpen(false);
		setSelectedChats([]);
		setSelectionMode(false);
		setCurrentChatIndex(0);
		setPodcastTitles({});
		setProcessingChat(null);
		setPodcastTitle("");
		setIsGeneratingPodcast(false);
	};

	// Start podcast generation flow
	const startPodcastGeneration = () => {
		if (selectedChats.length === 0) {
			toast.error("Please select at least one chat");
			return;
		}

		// Reset the state for podcast generation
		setCurrentChatIndex(0);
		setPodcastTitles({});

		// Set up for the first chat
		const firstChatId = selectedChats[0];
		const firstChat = chats.find((chat) => chat.id === firstChatId) || null;
		setProcessingChat(firstChat);

		// Set default title for the first chat
		setPodcastTitle(firstChat?.title || `Podcast from Chat ${firstChatId}`);
		setPodcastDialogOpen(true);
	};

	// Update the title for the current chat
	const updateCurrentChatTitle = (title: string) => {
		const currentChatId = selectedChats[currentChatIndex];
		setPodcastTitle(title);
		setPodcastTitles((prev) => ({
			...prev,
			[currentChatId]: title,
		}));
	};

	// Skip generating a podcast for the current chat
	const skipCurrentChat = () => {
		if (currentChatIndex < selectedChats.length - 1) {
			// Move to the next chat
			setCurrentChatIndex(currentChatIndex + 1);

			// Find the next chat
			const nextChatId = selectedChats[currentChatIndex + 1];
			const nextChat = chats.find((chat) => chat.id === nextChatId) || null;
			setProcessingChat(nextChat);

			// Set default title for the next chat
			if (!podcastTitles[nextChatId]) {
				setPodcastTitle(nextChat?.title || `Podcast from Chat ${nextChatId}`);
			} else {
				setPodcastTitle(podcastTitles[nextChatId]);
			}
		} else {
			// All done (all skipped)
			finishPodcastGeneration();
		}
	};

	// Toggle chat selection
	const toggleChatSelection = (chatId: number) => {
		setSelectedChats((prev) =>
			prev.includes(chatId) ? prev.filter((id) => id !== chatId) : [...prev, chatId]
		);
	};

	// Select all visible chats
	const selectAllVisibleChats = () => {
		const visibleChatIds = currentChats.map((chat) => chat.id);
		setSelectedChats((prev) => {
			const allSelected = visibleChatIds.every((id) => prev.includes(id));
			return allSelected
				? prev.filter((id) => !visibleChatIds.includes(id)) // Deselect all visible if all are selected
				: [...new Set([...prev, ...visibleChatIds])]; // Add all visible, ensuring no duplicates
		});
	};

	// Cancel selection mode
	const cancelSelectionMode = () => {
		setSelectionMode(false);
		setSelectedChats([]);
	};

	// Handle creating a new chat
	const handleCreateChat = async () => {
		if (!newChatTitle.trim()) {
			toast.error("Please enter a chat title");
			return;
		}

		setIsCreatingChat(true);
		try {
			const token = localStorage.getItem("surfsense_bearer_token");
			if (!token) {
				toast.error("Authentication error. Please log in again.");
				setIsCreatingChat(false);
				return;
			}

			const response = await fetch(
				`${process.env.NEXT_PUBLIC_FASTAPI_BACKEND_URL}/api/v1/chats/`,
				{
					method: "POST",
					headers: {
						Authorization: `Bearer ${token}`,
						"Content-Type": "application/json",
					},
					body: JSON.stringify({
						type: "QNA",
						title: newChatTitle,
						initial_connectors: selectedConnectors,
						messages: [],
						search_space_id: parseInt(searchSpaceId),
						document_ids: selectedDocuments,
						youtube_urls: newChatYoutubeUrls,
					}),
				}
			);

			if (!response.ok) {
				let errorMessage = "Failed to create chat";
				try {
					const errorData = await response.json();
					// Ensure we have a string error message
					if (errorData.detail) {
						errorMessage = typeof errorData.detail === 'string' ? errorData.detail : JSON.stringify(errorData.detail);
					} else if (errorData.message) {
						errorMessage = typeof errorData.message === 'string' ? errorData.message : JSON.stringify(errorData.message);
					} else if (errorData.error) {
						errorMessage = typeof errorData.error === 'string' ? errorData.error : JSON.stringify(errorData.error);
					}
				} catch (parseError) {
					// If we can't parse the error response, use the status text
					errorMessage = response.statusText || errorMessage;
				}
				console.error("Chat creation error:", errorMessage);
				throw new Error(errorMessage);
			}

			const data = await response.json();
			toast.success("Chat created successfully!");
			
			// Store chat state in localStorage for the new chat
			const chatState = {
				selectedDocuments: displayDocuments.filter(doc => selectedDocuments.includes(doc.id)),
				youtubeUrls: newChatYoutubeUrls,
				selectedConnectors: selectedConnectors,
			};
			localStorage.setItem(`chat_initial_state_${data.id}`, JSON.stringify(chatState));
			
			// Reset form
			setCreateChatDialogOpen(false);
			setNewChatTitle("");
			setSelectedDocuments([]);
			setNewChatYoutubeUrls([]);
			setNewYoutubeInput("");
			setSelectedConnectors([]);
			
			// Navigate to the new chat
			router.push(`/dashboard/${searchSpaceId}/researcher/${data.id}`);
		} catch (error) {
			console.error("Error creating chat:", error);
			toast.error(error instanceof Error ? error.message : "Failed to create chat");
		} finally {
			setIsCreatingChat(false);
		}
	};

	// Remove document from selection
	const removeDocument = (docId: number) => {
		setSelectedDocuments(selectedDocuments.filter(id => id !== docId));
	};

	// Add YouTube URL to new chat
	const addYoutubeUrl = () => {
		if (newYoutubeInput.trim() && !newChatYoutubeUrls.includes(newYoutubeInput.trim())) {
			setNewChatYoutubeUrls([...newChatYoutubeUrls, newYoutubeInput.trim()]);
			setNewYoutubeInput("");
		}
	};

	// Remove YouTube URL from new chat
	const removeYoutubeUrl = (url: string) => {
		setNewChatYoutubeUrls(newChatYoutubeUrls.filter(u => u !== url));
	};

	// Add connector to new chat
	const addConnector = (connectorType: string) => {
		if (!selectedConnectors.includes(connectorType)) {
			setSelectedConnectors([...selectedConnectors, connectorType]);
		}
	};

	// Remove connector from new chat
	const removeConnector = (connectorType: string) => {
		setSelectedConnectors(selectedConnectors.filter(c => c !== connectorType));
	};

	// Handle file upload in document picker
	const handleFileUpload = async () => {
		if (uploadingFiles.length === 0) return;

		const fileCount = uploadingFiles.length;
		const tempDocs = uploadingFiles.map((file, index) => ({
			id: -1 - index,
			name: file.name,
		}));
		
		setProcessingDocuments(tempDocs);
		setActiveTab("existing");
		
		await new Promise(resolve => setTimeout(resolve, 100));

		setIsUploading(true);
		setUploadProgress(0);

		const formData = new FormData();
		uploadingFiles.forEach((file) => {
			formData.append("files", file);
		});
		formData.append("search_space_id", searchSpaceId);

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

			const uploadResult = await response.json();

			// Reset upload state
			setUploadingFiles([]);
			setShowUploadSection(false);
			setUploadProgress(0);

			// Keep showing loading state and switch tab
			setActiveTab("existing");
			
			// Poll for documents to appear using manual fetch
			let pollAttempts = 0;
			const maxPollAttempts = 20; // Poll for up to 20 attempts (about 30-40 seconds)
			let foundNewDocs = false;
			const beforeUploadDocIds = new Set(localDocuments.map(doc => doc.id));
			
			while (pollAttempts < maxPollAttempts && !foundNewDocs) {
				// Wait before polling (exponential backoff, capped at 3 seconds)
				const waitTime = Math.min(1000 * Math.pow(1.3, pollAttempts), 3000);
				await new Promise(resolve => setTimeout(resolve, waitTime));
				
				// Manually fetch documents
				const fetchedDocs = await manualFetchDocuments();
				
				if (fetchedDocs && fetchedDocs.length > 0) {
					// Find new documents by comparing IDs
					const newDocs = fetchedDocs.filter((doc: any) => !beforeUploadDocIds.has(doc.id));
					
					// Check if new documents appeared
					if (newDocs.length > 0) {
						foundNewDocs = true;
						
						// Auto-select the newly uploaded documents
						const newDocIds = newDocs.map((doc: any) => doc.id);
						setSelectedDocuments((prev) => [...new Set([...prev, ...newDocIds])]);
						break;
					}
				}
				
				pollAttempts++;
			}

			// Clear processing state
			setProcessingDocuments([]);
			
			if (foundNewDocs) {
				toast.success(`${fileCount} file(s) uploaded and ready!`);
			} else {
				toast.info(`${fileCount} file(s) uploaded. They will appear once processing completes.`);
			}
		} catch (error: any) {
			toast.error(`Error uploading files: ${error.message}`);
			// Clear processing state on error
			setProcessingDocuments([]);
		} finally {
			setIsUploading(false);
		}
	};

	// Remove file from upload list
	const removeUploadFile = (index: number) => {
		setUploadingFiles((prev) => prev.filter((_, i) => i !== index));
	};

	// Format file size
	const formatFileSize = (bytes: number) => {
		if (bytes === 0) return "0 Bytes";
		const k = 1024;
		const sizes = ["Bytes", "KB", "MB", "GB"];
		const i = Math.floor(Math.log(bytes) / Math.log(k));
		return `${parseFloat((bytes / k ** i).toFixed(2))} ${sizes[i]}`;
	};

	return (
		<motion.div
			className="container p-6 mx-auto"
			initial="initial"
			animate="enter"
			exit="exit"
			variants={pageVariants}
		>
			<div className="flex flex-col space-y-4 md:space-y-6">
				<div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-2 md:space-y-0">
					<div>
						<h1 className="text-3xl font-bold tracking-tight">All Chats</h1>
						<p className="text-muted-foreground">View, search, and manage all your chats.</p>
					</div>
					<Button
						onClick={() => setCreateChatDialogOpen(true)}
						className="gap-2"
						size="lg"
					>
						<Plus className="h-4 w-4" />
						New Chat
					</Button>
				</div>

				{/* Filter and Search Bar */}
				<div className="flex flex-col space-y-4 md:flex-row md:items-center md:justify-between md:space-y-0">
					<div className="flex flex-1 items-center gap-2">
						<div className="relative w-full md:w-80">
							<Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
							<Input
								type="text"
								placeholder="Search chats..."
								className="pl-8"
								value={searchQuery}
								onChange={(e) => setSearchQuery(e.target.value)}
							/>
						</div>

						<Select value={selectedType} onValueChange={setSelectedType}>
							<SelectTrigger className="w-full md:w-40">
								<SelectValue placeholder="Filter by type" />
							</SelectTrigger>
							<SelectContent>
								<SelectGroup>
									{chatTypes.map((type) => (
										<SelectItem key={type} value={type}>
											{type === "all" ? "All Types" : type.charAt(0).toUpperCase() + type.slice(1)}
										</SelectItem>
									))}
								</SelectGroup>
							</SelectContent>
						</Select>
					</div>

					<div className="flex items-center gap-2">
						{selectionMode ? (
							<>
								<Button
									variant="outline"
									size="sm"
									onClick={selectAllVisibleChats}
									className="gap-1"
									title="Select or deselect all chats on the current page"
								>
									<CheckCircle className="h-4 w-4" />
									{currentChats.every((chat) => selectedChats.includes(chat.id))
										? "Deselect Page"
										: "Select Page"}
								</Button>
								<Button
									variant="default"
									size="sm"
									onClick={startPodcastGeneration}
									className="gap-1"
									disabled={selectedChats.length === 0}
								>
									<Podcast className="h-4 w-4" />
									Generate Podcast ({selectedChats.length})
								</Button>
								<Button variant="ghost" size="sm" onClick={cancelSelectionMode}>
									Cancel
								</Button>
							</>
						) : (
							<>
								<Button
									variant="outline"
									size="sm"
									onClick={() => setSelectionMode(true)}
									className="gap-1"
								>
									<Podcast className="h-4 w-4" />
									Podcaster
								</Button>
								<Select value={sortOrder} onValueChange={setSortOrder}>
									<SelectTrigger className="w-40">
										<SelectValue placeholder="Sort order" />
									</SelectTrigger>
									<SelectContent>
										<SelectGroup>
											<SelectItem value="newest">Newest First</SelectItem>
											<SelectItem value="oldest">Oldest First</SelectItem>
										</SelectGroup>
									</SelectContent>
								</Select>
							</>
						)}
					</div>
				</div>

				{/* Status Messages */}
				{isLoading && (
					<div className="flex items-center justify-center h-40">
						<div className="flex flex-col items-center gap-2">
							<div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
							<p className="text-sm text-muted-foreground">Loading chats...</p>
						</div>
					</div>
				)}

				{error && !isLoading && (
					<div className="border border-destructive/50 text-destructive p-4 rounded-md">
						<h3 className="font-medium">Error loading chats</h3>
						<p className="text-sm">{error}</p>
					</div>
				)}

				{!isLoading && !error && filteredChats.length === 0 && (
					<div className="flex flex-col items-center justify-center h-40 gap-2 text-center">
						<MessageCircleMore className="h-8 w-8 text-muted-foreground" />
						<h3 className="font-medium">No chats found</h3>
						<p className="text-sm text-muted-foreground">
							{searchQuery || selectedType !== "all"
								? "Try adjusting your search filters"
								: "Start a new chat to get started"}
						</p>
					</div>
				)}

				{/* Chat Grid */}
				{!isLoading && !error && filteredChats.length > 0 && (
					<AnimatePresence mode="wait">
						<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
							{currentChats.map((chat, index) => (
								<MotionCard
									key={chat.id}
									variants={chatCardVariants}
									initial="initial"
									animate="animate"
									exit="exit"
									transition={{ duration: 0.2, delay: index * 0.05 }}
									className={cn(
										"overflow-hidden hover:shadow-md transition-shadow",
										selectionMode && selectedChats.includes(chat.id)
											? "ring-2 ring-primary ring-offset-2"
											: ""
									)}
									onClick={(e) => {
										if (!selectionMode) return;
										// Ignore clicks coming from interactive elements
										if ((e.target as HTMLElement).closest("button, a, [data-stop-selection]"))
											return;
										toggleChatSelection(chat.id);
									}}
								>
									<CardHeader className="pb-3">
										<div className="flex justify-between items-start">
											<div className="space-y-1 flex items-start gap-2">
												{selectionMode && (
													<div className="mt-1">
														{selectedChats.includes(chat.id) ? (
															<CheckCircle className="h-4 w-4 text-primary" />
														) : (
															<Circle className="h-4 w-4 text-muted-foreground" />
														)}
													</div>
												)}
												<div>
													<CardTitle className="line-clamp-1">
														{chat.title || `Chat ${chat.id}`}
													</CardTitle>
													<CardDescription>
														<span className="flex items-center gap-1">
															<Calendar className="h-3.5 w-3.5" />
															<span>{format(new Date(chat.created_at), "MMM d, yyyy")}</span>
														</span>
													</CardDescription>
												</div>
											</div>
											{!selectionMode && (
												<DropdownMenu>
													<DropdownMenuTrigger asChild>
														<Button
															variant="ghost"
															size="icon"
															className="h-8 w-8"
															data-stop-selection
														>
															<MoreHorizontal className="h-4 w-4" />
															<span className="sr-only">Open menu</span>
														</Button>
													</DropdownMenuTrigger>
													<DropdownMenuContent align="end">
														<DropdownMenuItem
															onClick={() =>
																router.push(
																	`/dashboard/${chat.search_space_id}/researcher/${chat.id}`
																)
															}
														>
															<ExternalLink className="mr-2 h-4 w-4" />
															<span>View Chat</span>
														</DropdownMenuItem>
														<DropdownMenuItem
															onClick={() => {
																setSelectedChats([chat.id]);
																setPodcastTitle(chat.title || `Chat ${chat.id}`);
																setPodcastDialogOpen(true);
															}}
														>
															<Podcast className="mr-2 h-4 w-4" />
															<span>Generate Podcast</span>
														</DropdownMenuItem>
														<DropdownMenuSeparator />
														<DropdownMenuItem
															className="text-destructive focus:text-destructive"
															onClick={(e) => {
																e.stopPropagation();
																setChatToDelete({
																	id: chat.id,
																	title: chat.title || `Chat ${chat.id}`,
																});
																setDeleteDialogOpen(true);
															}}
														>
															<Trash2 className="mr-2 h-4 w-4" />
															<span>Delete Chat</span>
														</DropdownMenuItem>
													</DropdownMenuContent>
												</DropdownMenu>
											)}
										</div>
									</CardHeader>

									<CardFooter className="flex items-center justify-between gap-2 w-full">
										<Badge variant="secondary" className="text-xs">
											<Tag className="mr-1 h-3 w-3" />
											{chat.type || "Unknown"}
										</Badge>
										<Button
											size="sm"
											onClick={() =>
												router.push(`/dashboard/${chat.search_space_id}/researcher/${chat.id}`)
											}
										>
											<MessageCircleMore className="h-4 w-4" />
											<span>View Chat</span>
										</Button>
									</CardFooter>
								</MotionCard>
							))}
						</div>
					</AnimatePresence>
				)}

				{/* Pagination */}
				{!isLoading && !error && totalPages > 1 && (
					<Pagination className="mt-8">
						<PaginationContent>
							<PaginationItem>
								<PaginationPrevious
									href={`?page=${Math.max(1, currentPage - 1)}`}
									onClick={(e) => {
										e.preventDefault();
										if (currentPage > 1) setCurrentPage(currentPage - 1);
									}}
									className={currentPage <= 1 ? "pointer-events-none opacity-50" : ""}
								/>
							</PaginationItem>

							{Array.from({ length: totalPages }).map((_, index) => {
								const pageNumber = index + 1;
								const isVisible =
									pageNumber === 1 ||
									pageNumber === totalPages ||
									(pageNumber >= currentPage - 1 && pageNumber <= currentPage + 1);

								if (!isVisible) {
									// Show ellipsis at appropriate positions
									if (pageNumber === 2 || pageNumber === totalPages - 1) {
										return (
											<PaginationItem key={pageNumber}>
												<span className="flex h-9 w-9 items-center justify-center">...</span>
											</PaginationItem>
										);
									}
									return null;
								}

								return (
									<PaginationItem key={pageNumber}>
										<PaginationLink
											href={`?page=${pageNumber}`}
											onClick={(e) => {
												e.preventDefault();
												setCurrentPage(pageNumber);
											}}
											isActive={pageNumber === currentPage}
										>
											{pageNumber}
										</PaginationLink>
									</PaginationItem>
								);
							})}

							<PaginationItem>
								<PaginationNext
									href={`?page=${Math.min(totalPages, currentPage + 1)}`}
									onClick={(e) => {
										e.preventDefault();
										if (currentPage < totalPages) setCurrentPage(currentPage + 1);
									}}
									className={currentPage >= totalPages ? "pointer-events-none opacity-50" : ""}
								/>
							</PaginationItem>
						</PaginationContent>
					</Pagination>
				)}
			</div>

			{/* Delete Confirmation Dialog */}
			<Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
				<DialogContent className="sm:max-w-md">
					<DialogHeader>
						<DialogTitle className="flex items-center gap-2">
							<Trash2 className="h-5 w-5 text-destructive" />
							<span>Delete Chat</span>
						</DialogTitle>
						<DialogDescription>
							Are you sure you want to delete{" "}
							<span className="font-medium">{chatToDelete?.title}</span>? This action cannot be
							undone.
						</DialogDescription>
					</DialogHeader>
					<DialogFooter className="flex gap-2 sm:justify-end">
						<Button
							variant="outline"
							onClick={() => setDeleteDialogOpen(false)}
							disabled={isDeleting}
						>
							Cancel
						</Button>
						<Button
							variant="destructive"
							onClick={handleDeleteChat}
							disabled={isDeleting}
							className="gap-2"
						>
							{isDeleting ? (
								<>
									<span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
									Deleting...
								</>
							) : (
								<>
									<Trash2 className="h-4 w-4" />
									Delete
								</>
							)}
						</Button>
					</DialogFooter>
				</DialogContent>
			</Dialog>

			{/* Podcast Generation Dialog */}
			<Dialog
				open={podcastDialogOpen}
				onOpenChange={(isOpen: boolean) => {
					if (!isOpen) {
						// Cancel the process if dialog is closed
						setPodcastDialogOpen(false);
						setSelectedChats([]);
						setSelectionMode(false);
						setCurrentChatIndex(0);
						setPodcastTitles({});
						setProcessingChat(null);
						setPodcastTitle("");
					} else {
						setPodcastDialogOpen(true);
					}
				}}
			>
				<DialogContent className="sm:max-w-md">
					<DialogHeader>
						<DialogTitle className="flex items-center gap-2">
							<Podcast className="h-5 w-5 text-primary" />
							<span>
								Generate Podcast {currentChatIndex + 1} of {selectedChats.length}
							</span>
						</DialogTitle>
						<DialogDescription>
							{selectedChats.length > 1 ? (
								<>
									Creating individual podcasts for each selected chat. Currently processing:{" "}
									<span className="font-medium">
										{processingChat?.title || `Chat ${selectedChats[currentChatIndex]}`}
									</span>
								</>
							) : (
								"Create a podcast from this chat. The podcast will be available in the podcasts section once generated."
							)}
						</DialogDescription>
					</DialogHeader>

					<div className="space-y-4 py-2">
						<div className="space-y-2">
							<Label htmlFor="podcast-title">Podcast Title</Label>
							<Input
								id="podcast-title"
								placeholder="Enter podcast title"
								value={podcastTitle}
								onChange={(e) => updateCurrentChatTitle(e.target.value)}
							/>
						</div>

						{selectedChats.length > 1 && (
							<div className="w-full bg-muted rounded-full h-2.5 mt-4">
								<div
									className="bg-primary h-2.5 rounded-full transition-all duration-300"
									style={{ width: `${(currentChatIndex / selectedChats.length) * 100}%` }}
								></div>
							</div>
						)}
					</div>

					<DialogFooter className="flex gap-2 sm:justify-end">
						{selectedChats.length > 1 && !isGeneratingPodcast && (
							<Button variant="outline" onClick={skipCurrentChat} className="gap-1">
								Skip
							</Button>
						)}
						<Button
							variant="outline"
							onClick={() => {
								setPodcastDialogOpen(false);
								setCurrentChatIndex(0);
								setPodcastTitles({});
								setProcessingChat(null);
							}}
							disabled={isGeneratingPodcast}
						>
							Cancel
						</Button>
						<Button
							variant="default"
							onClick={handleGeneratePodcast}
							disabled={isGeneratingPodcast}
							className="gap-2"
						>
							{isGeneratingPodcast ? (
								<>
									<span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
									Generating...
								</>
							) : (
								<>
									<Podcast className="h-4 w-4" />
									Generate Podcast
								</>
							)}
						</Button>
					</DialogFooter>
				</DialogContent>
			</Dialog>

			{/* New Chat Creation Dialog */}
			<Dialog open={createChatDialogOpen} onOpenChange={setCreateChatDialogOpen}>
				<DialogContent className="sm:max-w-lg max-h-[90vh] overflow-y-auto">
					<DialogHeader>
						<DialogTitle className="flex items-center gap-2">
							<MessageCircleMore className="h-5 w-5 text-primary" />
							<span>Create New Chat</span>
						</DialogTitle>
						<DialogDescription>
							Set up your chat with a title and optionally add documents or YouTube URLs
						</DialogDescription>
					</DialogHeader>

					<div className="space-y-4 py-4">
						{/* Chat Title */}
						<div className="space-y-2">
							<Label htmlFor="chat-title">Chat Title *</Label>
							<Input
								id="chat-title"
								placeholder="Enter chat title"
								value={newChatTitle}
								onChange={(e) => setNewChatTitle(e.target.value)}
								onKeyDown={(e) => {
									if (e.key === 'Enter' && newChatTitle.trim()) {
										e.preventDefault();
										handleCreateChat();
									}
								}}
							/>
						</div>

						{/* Documents Section */}
						<div className="space-y-2">
							<Label>Documents (Optional)</Label>
						<Button
							type="button"
							onClick={() => {
								setDocumentPickerOpen(true);
								if (displayDocuments.length === 0) {
									manualFetchDocuments();
								}
							}}
							variant="outline"
							className="w-full justify-start gap-2"
						>
							<FileText className="h-4 w-4" />
							{selectedDocuments.length > 0
								? `${selectedDocuments.length} document(s) selected`
								: "Select Documents"}
						</Button>
							{selectedDocuments.length > 0 && (
								<div className="flex flex-wrap gap-2 mt-2">
									{selectedDocuments.map((docId) => {
										const doc = displayDocuments.find((d) => d.id === docId);
										return (
											<Badge key={docId} variant="secondary" className="gap-1">
												<FileText className="h-3 w-3" />
												{doc?.title || `Doc #${docId}`}
												<button
													type="button"
													onClick={() => removeDocument(docId)}
													className="ml-1 hover:bg-destructive/20 rounded-full"
												>
													<X className="h-3 w-3" />
												</button>
											</Badge>
										);
									})}
								</div>
							)}
						</div>

						{/* YouTube URLs Section */}
						<div className="space-y-2">
							<Label>YouTube URLs (Optional)</Label>
							<Button
								type="button"
								onClick={() => setUrlPickerOpen(true)}
								variant="outline"
								className="w-full justify-start gap-2"
							>
								<Video className="h-4 w-4" />
								{newChatYoutubeUrls.length > 0
									? `${newChatYoutubeUrls.length} URL(s) added`
									: "Add YouTube URLs"}
							</Button>
							{newChatYoutubeUrls.length > 0 && (
								<div className="flex flex-wrap gap-2 mt-2">
									{newChatYoutubeUrls.map((url) => (
										<Badge key={url} variant="secondary" className="gap-1">
											<Video className="h-3 w-3" />
											{url.length > 30 ? url.substring(0, 30) + '...' : url}
											<button
												type="button"
												onClick={() => removeYoutubeUrl(url)}
												className="ml-1 hover:bg-destructive/20 rounded-full"
											>
												<X className="h-3 w-3" />
											</button>
										</Badge>
									))}
								</div>
							)}
						</div>

						{/* Connectors Section */}
						<div className="space-y-2">
							<Label>Connectors (Optional)</Label>
							<Button
								type="button"
								onClick={() => setConnectorPickerOpen(true)}
								variant="outline"
								className="w-full justify-start gap-2"
							>
								<Cable className="h-4 w-4" />
								{selectedConnectors.length > 0
									? `${selectedConnectors.length} connector(s) selected`
									: "Select Connectors"}
							</Button>
							{selectedConnectors.length > 0 && (
								<div className="flex flex-wrap gap-2 mt-2">
									{selectedConnectors.map((connectorType) => {
										const connector = connectors.find(c => c.connector_type === connectorType);
										return (
											<Badge key={connectorType} variant="secondary" className="gap-1">
												<Cable className="h-3 w-3" />
												{connector?.name || connectorType}
												<button
													type="button"
													onClick={() => removeConnector(connectorType)}
													className="ml-1 hover:bg-destructive/20 rounded-full"
												>
													<X className="h-3 w-3" />
												</button>
											</Badge>
										);
									})}
								</div>
							)}
						</div>
					</div>

					<DialogFooter className="flex gap-2 sm:justify-end">
						<Button
							variant="outline"
							onClick={() => {
								setCreateChatDialogOpen(false);
								setNewChatTitle("");
								setSelectedDocuments([]);
								setNewChatYoutubeUrls([]);
								setNewYoutubeInput("");
								setSelectedConnectors([]);
							}}
							disabled={isCreatingChat}
						>
							Cancel
						</Button>
						<Button
							variant="default"
							onClick={handleCreateChat}
							disabled={isCreatingChat || !newChatTitle.trim() || processingDocuments.length > 0}
							className="gap-2"
						>
							{isCreatingChat ? (
								<>
									<span className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
									Creating...
								</>
							) : (
								<>
									<MessageCircleMore className="h-4 w-4" />
									Create Chat
								</>
							)}
						</Button>
					</DialogFooter>
				</DialogContent>
			</Dialog>

			{/* Document Picker Dialog */}
			<Dialog open={documentPickerOpen} onOpenChange={setDocumentPickerOpen}>
				<DialogContent className="sm:max-w-2xl max-h-[85vh] overflow-hidden flex flex-col">
					<DialogHeader>
						<DialogTitle className="flex items-center gap-2">
							<FileText className="h-5 w-5 text-primary" />
							<span>Add Documents</span>
						</DialogTitle>
						<DialogDescription>
							Select from existing documents or upload new files
						</DialogDescription>
					</DialogHeader>

					<Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 overflow-hidden flex flex-col">
						<TabsList className="grid w-full grid-cols-2">
							<TabsTrigger value="existing">
								<Search className="h-4 w-4 mr-2" />
								Select Existing
							</TabsTrigger>
							<TabsTrigger value="upload">
								<Upload className="h-4 w-4 mr-2" />
								Upload New
							</TabsTrigger>
						</TabsList>

						{/* Existing Documents Tab */}
						<TabsContent value="existing" className="flex-1 overflow-hidden flex flex-col mt-4 space-y-4">
							{/* Search Documents */}
							<div className="relative">
								<Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
								<Input
									placeholder="Search documents..."
									className="pl-8"
									value={documentSearchQuery}
									onChange={(e) => {
										setDocumentSearchQuery(e.target.value);
										if (e.target.value.trim()) {
											searchAvailableDocuments?.(e.target.value, 0, 100);
										} else {
											manualFetchDocuments();
										}
									}}
								/>
							</div>

							{/* Documents List */}
							<div className="flex-1 overflow-y-auto border rounded-md">
								{documentsLoading ? (
									<div className="flex items-center justify-center h-40">
										<div className="h-6 w-6 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
									</div>
								) : displayDocuments.length === 0 && processingDocuments.length === 0 ? (
									<div className="flex flex-col items-center justify-center h-40 gap-2">
										<FileText className="h-8 w-8 text-muted-foreground" />
										<p className="text-sm text-muted-foreground">
											{documentSearchQuery ? "No documents found" : "No documents available"}
										</p>
									</div>
								) : (
									<div className="p-4 space-y-2">
										{/* Processing Documents (Loading State) */}
										{processingDocuments.map((doc) => (
											<div
												key={doc.id}
												className="flex items-start gap-3 p-3 rounded-lg border bg-accent/30 opacity-70"
											>
												<div className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent mt-0.5"></div>
												<div className="flex-1 min-w-0">
													<p className="font-medium truncate">{doc.name}</p>
													<div className="flex items-center gap-2 mt-1">
														<Badge variant="outline" className="text-xs">
															Processing...
														</Badge>
													</div>
												</div>
											</div>
										))}
										
										{/* Existing Documents */}
										{displayDocuments.map((doc) => (
											<div
												key={doc.id}
												className="flex items-start gap-3 p-3 rounded-lg border hover:bg-accent/50 transition-colors cursor-pointer"
												onClick={() => {
													setSelectedDocuments((prev) =>
														prev.includes(doc.id)
															? prev.filter((id) => id !== doc.id)
															: [...prev, doc.id]
													);
												}}
											>
												<Checkbox
													checked={selectedDocuments.includes(doc.id)}
													onCheckedChange={(checked) => {
														if (checked) {
															setSelectedDocuments([...selectedDocuments, doc.id]);
														} else {
															setSelectedDocuments(selectedDocuments.filter((id) => id !== doc.id));
														}
													}}
													onClick={(e) => e.stopPropagation()}
												/>
												<div className="flex-1 min-w-0">
													<p className="font-medium truncate">{doc.title}</p>
													<div className="flex items-center gap-2 mt-1">
														<Badge variant="outline" className="text-xs">
															{doc.document_type}
														</Badge>
														<span className="text-xs text-muted-foreground">
															{new Date(doc.created_at).toLocaleDateString()}
														</span>
													</div>
												</div>
											</div>
										))}
									</div>
								)}
							</div>

							{/* Selected Count */}
							<div className="pt-2 border-t">
								<span className="text-sm text-muted-foreground">
									{selectedDocuments.length} document(s) selected
								</span>
							</div>
						</TabsContent>

						{/* Upload New Documents Tab */}
						<TabsContent value="upload" className="flex-1 overflow-hidden flex flex-col mt-4 space-y-4">
							{/* File Input */}
							<div className="border-2 border-dashed rounded-lg p-8 text-center hover:border-primary/50 transition-colors">
								<input
									type="file"
									multiple
									id="file-upload"
									className="hidden"
									onChange={(e) => {
										const files = Array.from(e.target.files || []);
										setUploadingFiles((prev) => [...prev, ...files]);
									}}
									accept=".pdf,.doc,.docx,.txt,.md,.csv,.xlsx,.xls,.ppt,.pptx,.jpg,.jpeg,.png,.mp3,.mp4,.wav"
								/>
								<label htmlFor="file-upload" className="cursor-pointer">
									<Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
									<p className="text-lg font-medium mb-1">Click to upload files</p>
									<p className="text-sm text-muted-foreground">
										or drag and drop files here
									</p>
									<p className="text-xs text-muted-foreground mt-2">
										PDF, DOC, TXT, Images, Audio, and more
									</p>
								</label>
							</div>

							{/* Files to Upload */}
							{uploadingFiles.length > 0 && (
								<div className="flex-1 overflow-y-auto border rounded-md p-4 space-y-2">
									<div className="flex items-center justify-between mb-2">
										<span className="text-sm font-medium">
											{uploadingFiles.length} file(s) ready to upload
										</span>
										<Button
											variant="ghost"
											size="sm"
											onClick={() => setUploadingFiles([])}
											disabled={isUploading}
										>
											Clear all
										</Button>
									</div>
									{uploadingFiles.map((file, index) => (
										<div
											key={index}
											className="flex items-center justify-between p-3 rounded-lg border bg-card"
										>
											<div className="flex items-center gap-3 flex-1 min-w-0">
												<FileText className="h-5 w-5 text-muted-foreground flex-shrink-0" />
												<div className="flex-1 min-w-0">
													<p className="font-medium truncate">{file.name}</p>
													<p className="text-xs text-muted-foreground">
														{formatFileSize(file.size)}
													</p>
												</div>
											</div>
											<Button
												variant="ghost"
												size="icon"
												className="h-8 w-8 flex-shrink-0"
												onClick={() => removeUploadFile(index)}
												disabled={isUploading}
											>
												<X className="h-4 w-4" />
											</Button>
										</div>
									))}
								</div>
							)}

							{/* Upload Progress */}
							{isUploading && (
								<div className="space-y-2">
									<div className="flex items-center justify-between text-sm">
										<span>Uploading files...</span>
										<span>{Math.round(uploadProgress)}%</span>
									</div>
									<Progress value={uploadProgress} className="h-2" />
								</div>
							)}

							{/* Upload Button */}
							{uploadingFiles.length > 0 && !isUploading && (
								<Button
									onClick={handleFileUpload}
									className="w-full"
									disabled={isUploading}
								>
									<Upload className="h-4 w-4 mr-2" />
									Upload {uploadingFiles.length} file(s)
								</Button>
							)}
						</TabsContent>
					</Tabs>

					<DialogFooter className="flex gap-2 sm:justify-end">
						<Button
							variant="outline"
							onClick={() => {
								setDocumentPickerOpen(false);
								setUploadingFiles([]);
								setShowUploadSection(false);
							}}
							disabled={isUploading}
						>
							Cancel
						</Button>
						<Button
							variant="default"
							onClick={() => setDocumentPickerOpen(false)}
							disabled={isUploading}
						>
							Done
						</Button>
					</DialogFooter>
				</DialogContent>
			</Dialog>

			{/* YouTube URL Picker Dialog */}
			<Dialog open={urlPickerOpen} onOpenChange={setUrlPickerOpen}>
				<DialogContent className="sm:max-w-lg">
					<DialogHeader>
						<DialogTitle className="flex items-center gap-2">
							<Video className="h-5 w-5 text-primary" />
							<span>Add YouTube URLs</span>
						</DialogTitle>
						<DialogDescription>
							Enter YouTube video URLs to include in your chat
						</DialogDescription>
					</DialogHeader>

					<div className="space-y-4 py-4">
						{/* Add URL Input */}
						<div className="flex gap-2">
							<Input
								placeholder="https://youtube.com/watch?v=..."
								value={newYoutubeInput}
								onChange={(e) => setNewYoutubeInput(e.target.value)}
								onKeyDown={(e) => {
									if (e.key === 'Enter' && newYoutubeInput.trim()) {
										e.preventDefault();
										addYoutubeUrl();
									}
								}}
							/>
							<Button
								type="button"
								onClick={addYoutubeUrl}
								disabled={!newYoutubeInput.trim()}
							>
								<Plus className="h-4 w-4" />
							</Button>
						</div>

						{/* URL List */}
						{newChatYoutubeUrls.length > 0 && (
							<div className="border rounded-md p-4 space-y-2 max-h-[300px] overflow-y-auto">
								{newChatYoutubeUrls.map((url, index) => (
									<div
										key={index}
										className="flex items-center justify-between p-2 rounded-lg border bg-card"
									>
										<div className="flex items-center gap-2 flex-1 min-w-0">
											<Video className="h-4 w-4 text-muted-foreground flex-shrink-0" />
											<span className="text-sm truncate">{url}</span>
										</div>
										<Button
											variant="ghost"
											size="icon"
											className="h-8 w-8 flex-shrink-0"
											onClick={() => removeYoutubeUrl(url)}
										>
											<X className="h-4 w-4" />
										</Button>
									</div>
								))}
							</div>
						)}

						{newChatYoutubeUrls.length === 0 && (
							<div className="flex flex-col items-center justify-center h-32 gap-2 text-center border rounded-md border-dashed">
								<Video className="h-8 w-8 text-muted-foreground" />
								<p className="text-sm text-muted-foreground">
									No URLs added yet
								</p>
							</div>
						)}
					</div>

					<DialogFooter className="flex gap-2 sm:justify-end">
						<Button
							variant="outline"
							onClick={() => setUrlPickerOpen(false)}
						>
							Cancel
						</Button>
						<Button
							variant="default"
							onClick={() => setUrlPickerOpen(false)}
						>
							Done
						</Button>
					</DialogFooter>
				</DialogContent>
			</Dialog>

			{/* Connector Picker Dialog */}
			<Dialog open={connectorPickerOpen} onOpenChange={setConnectorPickerOpen}>
				<DialogContent className="sm:max-w-lg">
					<DialogHeader>
						<DialogTitle className="flex items-center gap-2">
							<Cable className="h-5 w-5 text-primary" />
							<span>Select Connectors</span>
						</DialogTitle>
						<DialogDescription>
							Choose which data sources to include in your chat
						</DialogDescription>
					</DialogHeader>

					<div className="space-y-4">
						{connectorsLoading ? (
							<div className="flex justify-center py-8">
								<div className="animate-spin h-6 w-6 border-2 border-primary border-t-transparent rounded-full" />
							</div>
						) : connectors.length === 0 ? (
							<div className="flex flex-col items-center justify-center py-8 text-center">
								<Cable className="h-12 w-12 text-muted-foreground mb-4" />
								<h3 className="text-lg font-medium mb-2">No Connectors Configured</h3>
								<p className="text-sm text-muted-foreground mb-4">
									You need to add connectors first in the Manage Connectors page.
								</p>
								<Button
									variant="outline"
									onClick={() => {
										setConnectorPickerOpen(false);
										// Navigate to connectors page
										window.open(`/dashboard/${searchSpaceId}/connectors`, '_blank');
									}}
								>
									Go to Manage Connectors
								</Button>
							</div>
						) : (
							<div className="grid grid-cols-2 gap-3">
								{connectors.map((connector) => {
									const isSelected = selectedConnectors.includes(connector.connector_type);
									return (
										<Button
											key={connector.id}
											className={`flex items-center gap-2 p-3 rounded-md border cursor-pointer transition-colors h-auto ${
												isSelected ? "bg-primary text-primary-foreground" : "hover:bg-accent"
											}`}
											onClick={() => {
												if (isSelected) {
													removeConnector(connector.connector_type);
												} else {
													addConnector(connector.connector_type);
												}
											}}
											variant={isSelected ? "default" : "outline"}
											type="button"
										>
											{getConnectorIcon(connector.connector_type)}
											<span className="text-sm font-medium">{connector.name}</span>
										</Button>
									);
								})}
							</div>
						)}
					</div>

					<DialogFooter className="flex justify-between items-center">
						<div className="flex gap-2">
							<Button variant="outline" onClick={() => setSelectedConnectors([])}>
								Clear All
							</Button>
							<Button onClick={() => setSelectedConnectors(connectors.map(c => c.connector_type))}>
								Select All
							</Button>
						</div>
						<div className="flex gap-2">
							<Button
								variant="outline"
								onClick={() => setConnectorPickerOpen(false)}
							>
								Cancel
							</Button>
							<Button
								variant="default"
								onClick={() => setConnectorPickerOpen(false)}
							>
								Done
							</Button>
						</div>
					</DialogFooter>
				</DialogContent>
			</Dialog>
		</motion.div>
	);
}
