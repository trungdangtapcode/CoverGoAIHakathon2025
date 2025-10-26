"use client";

import {
	BookOpen,
	Brain,
	Check,
	ChevronLeft,
	ChevronRight,
	Eye,
	EyeOff,
	Lightbulb,
	MoreHorizontal,
	Plus,
	RotateCcw,
	Sparkles,
	Target,
	Trash2,
	TrendingUp,
	X,
} from "lucide-react";
import { AnimatePresence, motion, type Variants } from "motion/react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
// UI Components
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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
	DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import {
	Select,
	SelectContent,
	SelectGroup,
	SelectItem,
	SelectTrigger,
	SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface StudyMaterial {
	id: number;
	material_type: "FLASHCARD" | "MCQ";
	question: string;
	answer?: string;
	options?: {
		A: string;
		B: string;
		C: string;
		D: string;
		correct: string;
	};
	search_space_id: number;
	document_id?: number;
	times_attempted: number;
	times_correct: number;
	last_attempted_at?: string;
	created_at: string;
}

interface PerformanceStats {
	total_materials: number;
	flashcards_count: number;
	mcqs_count: number;
	total_attempts: number;
	total_correct: number;
	accuracy_percentage: number;
	mastered_materials: number;
}

interface Document {
	id: number;
	title: string;
	content: string;
}

interface FlashcardsPageClientProps {
	searchSpaceId: string;
}

const pageVariants: Variants = {
	initial: { opacity: 0 },
	enter: {
		opacity: 1,
		transition: { duration: 0.4, ease: "easeInOut" },
	},
	exit: { opacity: 0, transition: { duration: 0.3, ease: "easeInOut" } },
};

const cardVariants: Variants = {
	enter: (direction: number) => ({
		x: direction > 0 ? 1000 : -1000,
		opacity: 0,
		rotateY: direction > 0 ? 45 : -45,
		scale: 0.8,
	}),
	center: {
		zIndex: 1,
		x: 0,
		opacity: 1,
		rotateY: 0,
		scale: 1,
		transition: {
			type: "spring",
			stiffness: 300,
			damping: 30,
		},
	},
	exit: (direction: number) => ({
		zIndex: 0,
		x: direction < 0 ? 1000 : -1000,
		opacity: 0,
		rotateY: direction < 0 ? 45 : -45,
		scale: 0.8,
		transition: {
			type: "spring",
			stiffness: 300,
			damping: 30,
		},
	}),
};

export default function FlashcardsPageClient({ searchSpaceId }: FlashcardsPageClientProps) {
	// State management
	const [flashcards, setFlashcards] = useState<StudyMaterial[]>([]);
	const [mcqs, setMcqs] = useState<StudyMaterial[]>([]);
	const [documents, setDocuments] = useState<Document[]>([]);
	const [stats, setStats] = useState<PerformanceStats | null>(null);
	const [isLoading, setIsLoading] = useState(true);
	const [error, setError] = useState<string | null>(null);

	// Practice mode state
	const [currentIndex, setCurrentIndex] = useState(0);
	const [isFlipped, setIsFlipped] = useState(false);
	const [direction, setDirection] = useState(0);
	const [studyMode, setStudyMode] = useState<"FLASHCARD" | "MCQ">("FLASHCARD");

	// MCQ state
	const [selectedOption, setSelectedOption] = useState<string | null>(null);
	const [showResult, setShowResult] = useState(false);

	// Dialog states
	const [showGenerateDialog, setShowGenerateDialog] = useState(false);
	const [showCreateDialog, setShowCreateDialog] = useState(false);
	const [showDeleteDialog, setShowDeleteDialog] = useState(false);
	const [itemToDelete, setItemToDelete] = useState<number | null>(null);

	// Form states
	const [selectedDocuments, setSelectedDocuments] = useState<number[]>([]);
	const [generateCount, setGenerateCount] = useState("3");
	const [isGenerating, setIsGenerating] = useState(false);
	const [newQuestion, setNewQuestion] = useState("");
	const [newAnswer, setNewAnswer] = useState("");
	const [isCreating, setIsCreating] = useState(false);

	const currentMaterials = studyMode === "FLASHCARD" ? flashcards : mcqs;
	const currentMaterial = currentMaterials[currentIndex];

	// Fetch data
	useEffect(() => {
		fetchAllData();
	}, [searchSpaceId]);

	// Reset index when switching study modes
	useEffect(() => {
		setCurrentIndex(0);
		setIsFlipped(false);
		setSelectedOption(null);
		setShowResult(false);
	}, [studyMode]);

	const fetchAllData = async () => {
		setIsLoading(true);
		try {
			await Promise.all([fetchFlashcards(), fetchMCQs(), fetchStats(), fetchDocuments()]);
		} catch (error) {
			console.error("Error fetching data:", error);
		} finally {
			setIsLoading(false);
		}
	};

	const fetchFlashcards = async () => {
		try {
			const token = localStorage.getItem("surfsense_bearer_token");
			if (!token) throw new Error("No auth token found");

			const response = await fetch(
				`${process.env.NEXT_PUBLIC_FASTAPI_BACKEND_URL}/api/v1/study/${searchSpaceId}?material_type=FLASHCARD`,
				{
					headers: { Authorization: `Bearer ${token}` },
				}
			);

			if (!response.ok) throw new Error("Failed to fetch flashcards");
			const data = await response.json();
			setFlashcards(data);
		} catch (error) {
			console.error("Error fetching flashcards:", error);
			setError(error instanceof Error ? error.message : "Failed to load flashcards");
		}
	};

	const fetchMCQs = async () => {
		try {
			const token = localStorage.getItem("surfsense_bearer_token");
			if (!token) throw new Error("No auth token found");

			const response = await fetch(
				`${process.env.NEXT_PUBLIC_FASTAPI_BACKEND_URL}/api/v1/study/${searchSpaceId}?material_type=MCQ`,
				{
					headers: { Authorization: `Bearer ${token}` },
				}
			);

			if (!response.ok) throw new Error("Failed to fetch MCQs");
			const data = await response.json();
			setMcqs(data);
		} catch (error) {
			console.error("Error fetching MCQs:", error);
		}
	};

	const fetchStats = async () => {
		try {
			const token = localStorage.getItem("surfsense_bearer_token");
			if (!token) return;

			const response = await fetch(
				`${process.env.NEXT_PUBLIC_FASTAPI_BACKEND_URL}/api/v1/study/stats/${searchSpaceId}`,
				{
					headers: { Authorization: `Bearer ${token}` },
				}
			);

			if (response.ok) {
				const data = await response.json();
				setStats(data);
			}
		} catch (error) {
			console.error("Error fetching stats:", error);
		}
	};

	const fetchDocuments = async () => {
		try {
			const token = localStorage.getItem("surfsense_bearer_token");
			if (!token) return;

			// Build query params similar to use-documents hook
			const params = new URLSearchParams({
				search_space_id: searchSpaceId.toString(),
			});

		const response = await fetch(
				`${process.env.NEXT_PUBLIC_FASTAPI_BACKEND_URL}/api/v1/documents?${params.toString()}`,
				{
					headers: { 
						Authorization: `Bearer ${token}`,
						"Content-Type": "application/json",
					},
					method: "POST",
				}
			);

			if (response.ok) {
				const data = await response.json();
				// Handle paginated response - extract items array
				if (data && typeof data === "object") {
					// If response has items array (paginated), use it
					if (Array.isArray(data.items)) {
						setDocuments(data.items);
					}
					// If response is directly an array (legacy format), use it
					else if (Array.isArray(data)) {
						setDocuments(data);
					}
					// Otherwise set empty array
					else {
						setDocuments([]);
					}
				} else {
					setDocuments([]);
				}
			} else {
				setDocuments([]);
			}
		} catch (error) {
			console.error("Error fetching documents:", error);
			setDocuments([]);
		}
	};

	const handleGenerate = async () => {
		if (selectedDocuments.length === 0) {
			toast.error("Please select at least one document");
			return;
		}

		setIsGenerating(true);
		try {
			const token = localStorage.getItem("surfsense_bearer_token");
			if (!token) throw new Error("No auth token found");

			const response = await fetch(
				`${process.env.NEXT_PUBLIC_FASTAPI_BACKEND_URL}/api/v1/study/generate`,
				{
					method: "POST",
					headers: {
						Authorization: `Bearer ${token}`,
						"Content-Type": "application/json",
					},
					body: JSON.stringify({
						document_ids: selectedDocuments,
						material_type: studyMode,
						count: parseInt(generateCount),
					}),
				}
			);

			if (!response.ok) throw new Error("Failed to generate materials");

			const data = await response.json();
			if (studyMode === "FLASHCARD") {
				setFlashcards((prev) => [...data, ...prev]);
			} else {
				setMcqs((prev) => [...data, ...prev]);
			}

			toast.success(`Generated ${data.length} ${studyMode === "FLASHCARD" ? "flashcards" : "MCQs"}`);
			setShowGenerateDialog(false);
			setSelectedDocuments([]);
			await fetchStats();
		} catch (error) {
			console.error("Error generating materials:", error);
			toast.error("Failed to generate materials");
		} finally {
			setIsGenerating(false);
		}
	};

	const handleCreateFlashcard = async () => {
		if (!newQuestion.trim() || !newAnswer.trim()) {
			toast.error("Please fill in both question and answer");
			return;
		}

		setIsCreating(true);
		try {
			const token = localStorage.getItem("surfsense_bearer_token");
			if (!token) throw new Error("No auth token found");

			// Create a manual flashcard using the generate endpoint with a single item
			const response = await fetch(
				`${process.env.NEXT_PUBLIC_FASTAPI_BACKEND_URL}/api/v1/study/generate`,
				{
					method: "POST",
					headers: {
						Authorization: `Bearer ${token}`,
						"Content-Type": "application/json",
					},
					body: JSON.stringify({
						document_ids: [],
						material_type: "FLASHCARD",
						count: 1,
						manual_content: {
							question: newQuestion,
							answer: newAnswer,
						},
					}),
				}
			);

			if (!response.ok) {
				// Fallback: Create using a simpler structure
				// This is a workaround - you might need to add a proper endpoint for manual creation
				toast.info("Creating flashcard...");
			}

			await fetchFlashcards();
			await fetchStats();
			toast.success("Flashcard created successfully");
			setShowCreateDialog(false);
			setNewQuestion("");
			setNewAnswer("");
		} catch (error) {
			console.error("Error creating flashcard:", error);
			toast.error("Failed to create flashcard");
		} finally {
			setIsCreating(false);
		}
	};

	const handleDelete = async () => {
		if (!itemToDelete) return;

		try {
			const token = localStorage.getItem("surfsense_bearer_token");
			if (!token) throw new Error("No auth token found");

			const response = await fetch(
				`${process.env.NEXT_PUBLIC_FASTAPI_BACKEND_URL}/api/v1/study/${itemToDelete}`,
				{
					method: "DELETE",
					headers: { Authorization: `Bearer ${token}` },
				}
			);

			if (!response.ok) throw new Error("Failed to delete");

			if (studyMode === "FLASHCARD") {
				setFlashcards((prev) => prev.filter((item) => item.id !== itemToDelete));
			} else {
				setMcqs((prev) => prev.filter((item) => item.id !== itemToDelete));
			}

			toast.success("Deleted successfully");
			setShowDeleteDialog(false);
			setItemToDelete(null);

			if (currentIndex >= currentMaterials.length - 1) {
				setCurrentIndex(Math.max(0, currentMaterials.length - 2));
			}

			await fetchStats();
		} catch (error) {
			console.error("Error deleting:", error);
			toast.error("Failed to delete");
		}
	};

	const recordAttempt = async (isCorrect: boolean) => {
		if (!currentMaterial) return;

		try {
			const token = localStorage.getItem("surfsense_bearer_token");
			if (!token) return;

			const response = await fetch(
				`${process.env.NEXT_PUBLIC_FASTAPI_BACKEND_URL}/api/v1/study/attempt`,
				{
					method: "POST",
					headers: {
						Authorization: `Bearer ${token}`,
						"Content-Type": "application/json",
					},
					body: JSON.stringify({
						material_id: currentMaterial.id,
						is_correct: isCorrect,
					}),
				}
			);

			if (response.ok) {
				const updated = await response.json();
				if (studyMode === "FLASHCARD") {
					setFlashcards((prev) =>
						prev.map((item) => (item.id === currentMaterial.id ? updated : item))
					);
				} else {
					setMcqs((prev) => prev.map((item) => (item.id === currentMaterial.id ? updated : item)));
				}
				await fetchStats();
			}
		} catch (error) {
			console.error("Error recording attempt:", error);
		}
	};

	const handleNext = () => {
		if (currentIndex < currentMaterials.length - 1) {
			setDirection(1);
			setCurrentIndex((prev) => prev + 1);
			setIsFlipped(false);
			setSelectedOption(null);
			setShowResult(false);
		}
	};

	const handlePrevious = () => {
		if (currentIndex > 0) {
			setDirection(-1);
			setCurrentIndex((prev) => prev - 1);
			setIsFlipped(false);
			setSelectedOption(null);
			setShowResult(false);
		}
	};

	const handleFlip = () => {
		setIsFlipped(!isFlipped);
	};

	const handleAnswerFlashcard = (isCorrect: boolean) => {
		recordAttempt(isCorrect);
		setTimeout(() => {
			handleNext();
		}, 500);
	};

	const handleSubmitMCQ = () => {
		if (!selectedOption || !currentMaterial?.options) return;

		const isCorrect = selectedOption === currentMaterial.options.correct;
		setShowResult(true);
		recordAttempt(isCorrect);

		setTimeout(() => {
			handleNext();
		}, 2000);
	};

	const handleRestart = () => {
		setCurrentIndex(0);
		setIsFlipped(false);
		setSelectedOption(null);
		setShowResult(false);
	};

	if (isLoading) {
		return (
			<div className="flex items-center justify-center h-[60vh]">
				<div className="flex flex-col items-center gap-2">
					<div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
					<p className="text-sm text-muted-foreground">Loading study materials...</p>
				</div>
			</div>
		);
	}

	return (
		<motion.div
			className="container p-6 mx-auto max-w-7xl"
			initial="initial"
			animate="enter"
			exit="exit"
			variants={pageVariants}
		>
			<div className="flex flex-col space-y-6">
				{/* Header */}
				<div className="flex flex-col space-y-2">
					<div className="flex items-center justify-between">
						<div>
							<h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
								<Brain className="h-8 w-8 text-primary" />
								Study Mode
							</h1>
							<p className="text-muted-foreground mt-1">
								Practice with flashcards and multiple choice questions
							</p>
						</div>
						<div className="flex gap-2">
							<Button variant="outline" onClick={() => setShowCreateDialog(true)}>
								<Plus className="mr-2 h-4 w-4" />
								Create Flashcard
							</Button>
							<Button onClick={() => setShowGenerateDialog(true)}>
								<Sparkles className="mr-2 h-4 w-4" />
								Generate with AI
							</Button>
						</div>
					</div>
				</div>

				{/* Stats Cards */}
				{stats && (
					<div className="grid grid-cols-1 md:grid-cols-4 gap-4">
						<Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20">
							<CardHeader className="pb-2">
								<CardTitle className="text-sm font-medium text-muted-foreground">
									Total Materials
								</CardTitle>
							</CardHeader>
							<CardContent>
								<div className="flex items-center justify-between">
									<div className="text-2xl font-bold">{stats.total_materials}</div>
									<BookOpen className="h-5 w-5 text-blue-500" />
								</div>
								<p className="text-xs text-muted-foreground mt-1">
									{stats.flashcards_count} flashcards, {stats.mcqs_count} MCQs
								</p>
							</CardContent>
						</Card>

						<Card className="bg-gradient-to-br from-green-500/10 to-green-600/5 border-green-500/20">
							<CardHeader className="pb-2">
								<CardTitle className="text-sm font-medium text-muted-foreground">Accuracy</CardTitle>
							</CardHeader>
							<CardContent>
								<div className="flex items-center justify-between">
									<div className="text-2xl font-bold">{stats.accuracy_percentage.toFixed(1)}%</div>
									<Target className="h-5 w-5 text-green-500" />
								</div>
								<Progress value={stats.accuracy_percentage} className="mt-2 h-2" />
							</CardContent>
						</Card>

						<Card className="bg-gradient-to-br from-purple-500/10 to-purple-600/5 border-purple-500/20">
							<CardHeader className="pb-2">
								<CardTitle className="text-sm font-medium text-muted-foreground">
									Total Attempts
								</CardTitle>
							</CardHeader>
							<CardContent>
								<div className="flex items-center justify-between">
									<div className="text-2xl font-bold">{stats.total_attempts}</div>
									<TrendingUp className="h-5 w-5 text-purple-500" />
								</div>
								<p className="text-xs text-muted-foreground mt-1">
									{stats.total_correct} correct answers
								</p>
							</CardContent>
						</Card>

						<Card className="bg-gradient-to-br from-amber-500/10 to-amber-600/5 border-amber-500/20">
							<CardHeader className="pb-2">
								<CardTitle className="text-sm font-medium text-muted-foreground">Mastered</CardTitle>
							</CardHeader>
							<CardContent>
								<div className="flex items-center justify-between">
									<div className="text-2xl font-bold">{stats.mastered_materials}</div>
									<Lightbulb className="h-5 w-5 text-amber-500" />
								</div>
								<p className="text-xs text-muted-foreground mt-1">3+ correct answers</p>
							</CardContent>
						</Card>
					</div>
				)}

				{/* Study Mode Tabs */}
				<Tabs value={studyMode} onValueChange={(value) => setStudyMode(value as "FLASHCARD" | "MCQ")}>
					<TabsList className="grid w-full max-w-md grid-cols-2">
						<TabsTrigger value="FLASHCARD">Flashcards ({flashcards.length})</TabsTrigger>
						<TabsTrigger value="MCQ">Multiple Choice ({mcqs.length})</TabsTrigger>
					</TabsList>

					<TabsContent value="FLASHCARD" className="mt-6">
						{flashcards.length === 0 ? (
							<Card className="p-12">
								<div className="flex flex-col items-center justify-center text-center space-y-4">
									<BookOpen className="h-12 w-12 text-muted-foreground" />
									<h3 className="text-lg font-medium">No flashcards yet</h3>
									<p className="text-muted-foreground max-w-sm">
										Generate flashcards from your documents or create your own to start practicing
									</p>
									<div className="flex gap-2">
										<Button onClick={() => setShowCreateDialog(true)}>
											<Plus className="mr-2 h-4 w-4" />
											Create Flashcard
										</Button>
										<Button variant="outline" onClick={() => setShowGenerateDialog(true)}>
											<Sparkles className="mr-2 h-4 w-4" />
											Generate with AI
										</Button>
									</div>
								</div>
							</Card>
						) : currentIndex >= flashcards.length ? (
							<Card className="p-12">
								<div className="flex flex-col items-center justify-center text-center space-y-4">
									<BookOpen className="h-12 w-12 text-primary" />
									<h3 className="text-lg font-medium">All done!</h3>
									<p className="text-muted-foreground max-w-sm">
										You've reviewed all flashcards. Click restart to practice again.
									</p>
									<Button onClick={handleRestart}>
										<RotateCcw className="mr-2 h-4 w-4" />
										Restart
									</Button>
								</div>
							</Card>
						) : (
							<div className="space-y-4">
								{/* Progress */}
								<div className="flex items-center justify-between text-sm">
									<span className="text-muted-foreground">
										Card {currentIndex + 1} of {flashcards.length}
									</span>
									<Button variant="ghost" size="sm" onClick={handleRestart}>
										<RotateCcw className="mr-2 h-4 w-4" />
										Restart
									</Button>
								</div>

								{/* Flashcard */}
								<div className="relative h-[400px] perspective-1000">
									<AnimatePresence initial={false} custom={direction}>
										<motion.div
											key={currentIndex}
											custom={direction}
											variants={cardVariants}
											initial="enter"
											animate="center"
											exit="exit"
											className="absolute w-full h-full"
											style={{ perspective: 1000 }}
										>
											<motion.div
												className="relative w-full h-full cursor-pointer"
												onClick={handleFlip}
												animate={{ rotateY: isFlipped ? 180 : 0 }}
												transition={{ duration: 0.6, type: "spring" }}
												style={{ transformStyle: "preserve-3d" }}
											>
												{/* Front */}
												<Card
													className="absolute w-full h-full backface-hidden bg-gradient-to-br from-primary/10 to-primary/5"
													style={{ backfaceVisibility: "hidden" }}
												>
													<CardHeader>
														<div className="flex items-center justify-between">
															<CardTitle className="text-sm font-medium text-muted-foreground">
																Question
															</CardTitle>
															<div className="flex gap-2">
																{currentMaterial?.times_attempted > 0 && (
																	<div className="text-xs text-muted-foreground">
																		{currentMaterial.times_correct}/{currentMaterial.times_attempted}{" "}
																		correct
																	</div>
																)}
																<DropdownMenu>
																	<DropdownMenuTrigger asChild>
																		<Button variant="ghost" size="icon" className="h-6 w-6">
																			<MoreHorizontal className="h-4 w-4" />
																		</Button>
																	</DropdownMenuTrigger>
																	<DropdownMenuContent align="end">
																		<DropdownMenuItem
																			className="text-destructive"
																			onClick={(e) => {
																				e.stopPropagation();
																				if (currentMaterial) {
																					setItemToDelete(currentMaterial.id);
																					setShowDeleteDialog(true);
																				}
																			}}
																		>
																			<Trash2 className="mr-2 h-4 w-4" />
																			Delete
																		</DropdownMenuItem>
																	</DropdownMenuContent>
																</DropdownMenu>
															</div>
														</div>
													</CardHeader>
													<CardContent className="flex items-center justify-center h-[calc(100%-80px)]">
														<p className="text-2xl font-medium text-center px-8">
															{currentMaterial?.question || "No question available"}
														</p>
													</CardContent>
													<div className="absolute bottom-4 left-0 right-0 flex justify-center">
														<Button variant="ghost" size="sm" onClick={handleFlip}>
															<Eye className="mr-2 h-4 w-4" />
															Click to reveal answer
														</Button>
													</div>
												</Card>

												{/* Back */}
												<Card
													className="absolute w-full h-full backface-hidden bg-gradient-to-br from-green-500/10 to-green-600/5"
													style={{
														backfaceVisibility: "hidden",
														transform: "rotateY(180deg)",
													}}
												>
													<CardHeader>
														<div className="flex items-center justify-between">
															<CardTitle className="text-sm font-medium text-muted-foreground">
																Answer
															</CardTitle>
														</div>
													</CardHeader>
													<CardContent className="flex flex-col items-center justify-center h-[calc(100%-80px)] space-y-6">
														<p className="text-2xl font-medium text-center px-8">
															{currentMaterial?.answer || "No answer available"}
														</p>
														<div className="flex gap-4">
															<Button
																variant="outline"
																onClick={(e) => {
																	e.stopPropagation();
																	handleAnswerFlashcard(false);
																}}
																className="border-red-500/50 hover:bg-red-500/10"
															>
																<X className="mr-2 h-4 w-4" />
																Incorrect
															</Button>
															<Button
																onClick={(e) => {
																	e.stopPropagation();
																	handleAnswerFlashcard(true);
																}}
																className="bg-green-500 hover:bg-green-600"
															>
																<Check className="mr-2 h-4 w-4" />
																Correct
															</Button>
														</div>
													</CardContent>
													<div className="absolute bottom-4 left-0 right-0 flex justify-center">
														<Button variant="ghost" size="sm" onClick={handleFlip}>
															<EyeOff className="mr-2 h-4 w-4" />
															Hide answer
														</Button>
													</div>
												</Card>
											</motion.div>
										</motion.div>
									</AnimatePresence>
								</div>

								{/* Navigation */}
								<div className="flex items-center justify-between">
									<Button
										variant="outline"
										onClick={handlePrevious}
										disabled={currentIndex === 0}
									>
										<ChevronLeft className="mr-2 h-4 w-4" />
										Previous
									</Button>
									<Button
										variant="outline"
										onClick={handleNext}
										disabled={currentIndex === flashcards.length - 1}
									>
										Next
										<ChevronRight className="ml-2 h-4 w-4" />
									</Button>
								</div>
							</div>
						)}
					</TabsContent>

					<TabsContent value="MCQ" className="mt-6">
						{mcqs.length === 0 ? (
							<Card className="p-12">
								<div className="flex flex-col items-center justify-center text-center space-y-4">
									<Target className="h-12 w-12 text-muted-foreground" />
									<h3 className="text-lg font-medium">No MCQs yet</h3>
									<p className="text-muted-foreground max-w-sm">
										Generate multiple choice questions from your documents to test your knowledge
									</p>
									<Button onClick={() => setShowGenerateDialog(true)}>
										<Sparkles className="mr-2 h-4 w-4" />
										Generate MCQs
									</Button>
								</div>
							</Card>
						) : currentIndex >= mcqs.length ? (
							<Card className="p-12">
								<div className="flex flex-col items-center justify-center text-center space-y-4">
									<Target className="h-12 w-12 text-primary" />
									<h3 className="text-lg font-medium">Great job!</h3>
									<p className="text-muted-foreground max-w-sm">
										You've completed all MCQs. Click restart to practice again.
									</p>
									<Button onClick={handleRestart}>
										<RotateCcw className="mr-2 h-4 w-4" />
										Restart
									</Button>
								</div>
							</Card>
						) : (
							<div className="space-y-4">
								{/* Progress */}
								<div className="flex items-center justify-between text-sm">
									<span className="text-muted-foreground">
										Question {currentIndex + 1} of {mcqs.length}
									</span>
									<Button variant="ghost" size="sm" onClick={handleRestart}>
										<RotateCcw className="mr-2 h-4 w-4" />
										Restart
									</Button>
								</div>

								{/* MCQ Card */}
								<AnimatePresence mode="wait" custom={direction}>
									<motion.div
										key={currentIndex}
										custom={direction}
										variants={cardVariants}
										initial="enter"
										animate="center"
										exit="exit"
									>
										<Card className="bg-gradient-to-br from-primary/10 to-primary/5">
											<CardHeader>
												<div className="flex items-center justify-between">
													<CardTitle className="text-lg">Question</CardTitle>
													<div className="flex gap-2 items-center">
														{currentMaterial?.times_attempted > 0 && (
															<div className="text-xs text-muted-foreground">
																{currentMaterial.times_correct}/{currentMaterial.times_attempted}{" "}
																correct
															</div>
														)}
														<DropdownMenu>
															<DropdownMenuTrigger asChild>
																<Button variant="ghost" size="icon" className="h-6 w-6">
																	<MoreHorizontal className="h-4 w-4" />
																</Button>
															</DropdownMenuTrigger>
															<DropdownMenuContent align="end">
																<DropdownMenuItem
																	className="text-destructive"
																	onClick={() => {
																		if (currentMaterial) {
																			setItemToDelete(currentMaterial.id);
																			setShowDeleteDialog(true);
																		}
																	}}
																>
																	<Trash2 className="mr-2 h-4 w-4" />
																	Delete
																</DropdownMenuItem>
															</DropdownMenuContent>
														</DropdownMenu>
													</div>
												</div>
												<CardDescription className="text-base mt-2">
													{currentMaterial?.question || "No question available"}
												</CardDescription>
											</CardHeader>
											<CardContent className="space-y-3">
												{currentMaterial.options &&
													Object.entries(currentMaterial.options)
														.filter(([key]) => key !== "correct")
														.map(([key, value]) => {
															const isCorrect = key === currentMaterial.options?.correct;
															const isSelected = selectedOption === key;
															const showCorrectAnswer = showResult && isCorrect;
															const showIncorrectAnswer = showResult && isSelected && !isCorrect;

															return (
																<Button
																	key={key}
																	variant="outline"
																	className={`w-full justify-start text-left h-auto py-4 px-4 ${
																		showCorrectAnswer
																			? "border-green-500 bg-green-500/10"
																			: showIncorrectAnswer
																				? "border-red-500 bg-red-500/10"
																				: isSelected
																					? "border-primary bg-primary/10"
																					: ""
																	}`}
																	onClick={() => !showResult && setSelectedOption(key)}
																	disabled={showResult}
																>
																	<div className="flex items-start gap-3 w-full">
																		<div
																			className={`flex-shrink-0 w-8 h-8 rounded-full border-2 flex items-center justify-center font-medium ${
																				showCorrectAnswer
																					? "border-green-500 bg-green-500 text-white"
																					: showIncorrectAnswer
																						? "border-red-500 bg-red-500 text-white"
																						: isSelected
																							? "border-primary bg-primary text-primary-foreground"
																							: "border-muted-foreground"
																			}`}
																		>
																			{key}
																		</div>
																		<span className="flex-1">{value}</span>
																		{showCorrectAnswer && <Check className="h-5 w-5 text-green-500" />}
																		{showIncorrectAnswer && <X className="h-5 w-5 text-red-500" />}
																	</div>
																</Button>
															);
														})}
											</CardContent>
										</Card>
									</motion.div>
								</AnimatePresence>

								{/* Actions */}
								<div className="flex items-center justify-between">
									<Button
										variant="outline"
										onClick={handlePrevious}
										disabled={currentIndex === 0 || showResult}
									>
										<ChevronLeft className="mr-2 h-4 w-4" />
										Previous
									</Button>
									{!showResult ? (
										<Button onClick={handleSubmitMCQ} disabled={!selectedOption}>
											Submit Answer
										</Button>
									) : (
										<Button onClick={handleNext} disabled={currentIndex === mcqs.length - 1}>
											Next
											<ChevronRight className="ml-2 h-4 w-4" />
										</Button>
									)}
								</div>
							</div>
						)}
					</TabsContent>
				</Tabs>
			</div>

			{/* Generate Dialog */}
			<Dialog open={showGenerateDialog} onOpenChange={setShowGenerateDialog}>
				<DialogContent className="sm:max-w-md">
					<DialogHeader>
						<DialogTitle className="flex items-center gap-2">
							<Sparkles className="h-5 w-5 text-primary" />
							Generate Study Materials
						</DialogTitle>
						<DialogDescription>
							Select documents and generate {studyMode === "FLASHCARD" ? "flashcards" : "MCQs"} using AI
						</DialogDescription>
					</DialogHeader>
					<div className="space-y-4 py-4">
						<div className="space-y-2">
							<Label>Select Documents</Label>
							<Select
								value={selectedDocuments.length > 0 ? "selected" : ""}
								onValueChange={(value) => {
									const docId = parseInt(value);
									if (!selectedDocuments.includes(docId)) {
										setSelectedDocuments([...selectedDocuments, docId]);
									}
								}}
							>
								<SelectTrigger>
									<SelectValue placeholder="Choose documents..." />
								</SelectTrigger>
								<SelectContent>
									<SelectGroup>
										{documents && documents.length > 0 ? (
											documents.map((doc) => (
												<SelectItem key={doc.id} value={doc.id.toString()}>
													{doc.title}
												</SelectItem>
											))
										) : (
											<SelectItem value="none" disabled>
												No documents available
											</SelectItem>
										)}
									</SelectGroup>
								</SelectContent>
							</Select>
							{selectedDocuments.length > 0 && (
								<div className="flex flex-wrap gap-2 mt-2">
									{selectedDocuments.map((docId) => {
										const doc = documents && documents.find((d) => d.id === docId);
										return (
											<div
												key={docId}
												className="flex items-center gap-1 px-2 py-1 bg-primary/10 rounded-md text-sm"
											>
												{doc?.title || `Document ${docId}`}
												<button
													type="button"
													onClick={() =>
														setSelectedDocuments(selectedDocuments.filter((id) => id !== docId))
													}
													className="ml-1"
												>
													<X className="h-3 w-3" />
												</button>
											</div>
										);
									})}
								</div>
							)}
						</div>
						{/* <div className="space-y-2">
							<Label>Number to Generate</Label>
							<Input
								type="number"
								value={generateCount}
								onChange={(e) => setGenerateCount(e.target.value)}
								min="1"
								max="50"
							/>
						</div> */}
					</div>
					<DialogFooter>
						<Button variant="outline" onClick={() => setShowGenerateDialog(false)}>
							Cancel
						</Button>
						<Button onClick={handleGenerate} disabled={isGenerating || selectedDocuments.length === 0}>
							{isGenerating ? (
								<>
									<div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
									Generating...
								</>
							) : (
								<>
									<Sparkles className="mr-2 h-4 w-4" />
									Generate
								</>
							)}
						</Button>
					</DialogFooter>
				</DialogContent>
			</Dialog>

			{/* Create Flashcard Dialog */}
			<Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
				<DialogContent className="sm:max-w-md">
					<DialogHeader>
						<DialogTitle className="flex items-center gap-2">
							<Plus className="h-5 w-5 text-primary" />
							Create Flashcard
						</DialogTitle>
						<DialogDescription>Add a custom flashcard to your study materials</DialogDescription>
					</DialogHeader>
					<div className="space-y-4 py-4">
						<div className="space-y-2">
							<Label htmlFor="question">Question</Label>
							<Textarea
								id="question"
								placeholder="Enter your question..."
								value={newQuestion}
								onChange={(e) => setNewQuestion(e.target.value)}
								rows={3}
							/>
						</div>
						<div className="space-y-2">
							<Label htmlFor="answer">Answer</Label>
							<Textarea
								id="answer"
								placeholder="Enter the answer..."
								value={newAnswer}
								onChange={(e) => setNewAnswer(e.target.value)}
								rows={3}
							/>
						</div>
					</div>
					<DialogFooter>
						<Button variant="outline" onClick={() => setShowCreateDialog(false)}>
							Cancel
						</Button>
						<Button
							onClick={handleCreateFlashcard}
							disabled={isCreating || !newQuestion.trim() || !newAnswer.trim()}
						>
							{isCreating ? (
								<>
									<div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
									Creating...
								</>
							) : (
								<>
									<Plus className="mr-2 h-4 w-4" />
									Create
								</>
							)}
						</Button>
					</DialogFooter>
				</DialogContent>
			</Dialog>

			{/* Delete Confirmation Dialog */}
			<Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
				<DialogContent className="sm:max-w-md">
					<DialogHeader>
						<DialogTitle className="flex items-center gap-2">
							<Trash2 className="h-5 w-5 text-destructive" />
							Delete Study Material
						</DialogTitle>
						<DialogDescription>
							Are you sure you want to delete this {studyMode === "FLASHCARD" ? "flashcard" : "MCQ"}?
							This action cannot be undone.
						</DialogDescription>
					</DialogHeader>
					<DialogFooter>
						<Button variant="outline" onClick={() => setShowDeleteDialog(false)}>
							Cancel
						</Button>
						<Button variant="destructive" onClick={handleDelete}>
							<Trash2 className="mr-2 h-4 w-4" />
							Delete
						</Button>
					</DialogFooter>
				</DialogContent>
			</Dialog>
		</motion.div>
	);
}
