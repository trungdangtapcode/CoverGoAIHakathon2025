# Study Mode API - Frontend Developer Guide

Quick reference for integrating flashcards and MCQs into the frontend.

## Base URL
```
http://localhost:8000/api/v1/study
```

## Authentication
All endpoints require Bearer token in header:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

---

## Endpoints

### 1. Generate Study Materials
**POST** `/generate`

Create flashcards or MCQs from documents using AI.

```typescript
// Request
interface GenerateRequest {
  document_ids: number[];
  material_type: "FLASHCARD" | "MCQ";
  count: number;  // default: 10
}

// Response
interface StudyMaterial {
  id: number;
  material_type: "FLASHCARD" | "MCQ";
  question: string;
  answer?: string;  // For flashcards
  options?: {       // For MCQs
    A: string;
    B: string;
    C: string;
    D: string;
    correct: string;  // e.g., "B"
  };
  search_space_id: number;
  document_id?: number;
  times_attempted: number;
  times_correct: number;
  last_attempted_at?: string;
  created_at: string;
}
```

**Example:**
```javascript
const response = await fetch('/api/v1/study/generate', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    document_ids: [1, 2, 3],
    material_type: "FLASHCARD",
    count: 10
  })
});

const flashcards = await response.json();
// Returns: StudyMaterial[]
```

---

### 2. Get Study Materials
**GET** `/{search_space_id}?material_type={type}`

Retrieve all study materials for a search space.

**Query Parameters:**
- `material_type` (optional): `"FLASHCARD"` or `"MCQ"`

**Example:**
```javascript
// Get all materials
const all = await fetch(`/api/v1/study/${searchSpaceId}`, {
  headers: { 'Authorization': `Bearer ${token}` }
});

// Get only flashcards
const flashcards = await fetch(
  `/api/v1/study/${searchSpaceId}?material_type=FLASHCARD`,
  { headers: { 'Authorization': `Bearer ${token}` }}
);

// Get only MCQs
const mcqs = await fetch(
  `/api/v1/study/${searchSpaceId}?material_type=MCQ`,
  { headers: { 'Authorization': `Bearer ${token}` }}
);
```

---

### 3. Record Study Attempt
**POST** `/attempt`

Track user's answer (correct/incorrect).

```typescript
// Request
interface AttemptRequest {
  material_id: number;
  is_correct: boolean;
}

// Response: Updated StudyMaterial
```

**Example:**
```javascript
const response = await fetch('/api/v1/study/attempt', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    material_id: 1,
    is_correct: true
  })
});

const updated = await response.json();
// Returns: Updated StudyMaterial with incremented stats
```

---

### 4. Get Performance Statistics
**GET** `/stats/{search_space_id}`

Get learning progress and performance metrics.

```typescript
// Response
interface PerformanceStats {
  total_materials: number;
  flashcards_count: number;
  mcqs_count: number;
  total_attempts: number;
  total_correct: number;
  accuracy_percentage: number;
  mastered_materials: number;  // Correct ≥3 times
}
```

**Example:**
```javascript
const response = await fetch(`/api/v1/study/stats/${searchSpaceId}`, {
  headers: { 'Authorization': `Bearer ${token}` }
});

const stats = await response.json();
// Example: { total_materials: 25, accuracy_percentage: 76.0, ... }
```

---

## React/Next.js Example

```typescript
// hooks/useStudyMode.ts
import { useState, useEffect } from 'react';

interface StudyMaterial {
  id: number;
  material_type: "FLASHCARD" | "MCQ";
  question: string;
  answer?: string;
  options?: any;
  times_attempted: number;
  times_correct: number;
}

export function useStudyMode(searchSpaceId: number) {
  const [flashcards, setFlashcards] = useState<StudyMaterial[]>([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);

  // Generate flashcards
  const generateFlashcards = async (documentIds: number[], count = 10) => {
    setLoading(true);
    const response = await fetch('/api/v1/study/generate', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        document_ids: documentIds,
        material_type: "FLASHCARD",
        count
      })
    });
    const data = await response.json();
    setFlashcards(data);
    setLoading(false);
    return data;
  };

  // Get flashcards
  const loadFlashcards = async () => {
    const response = await fetch(
      `/api/v1/study/${searchSpaceId}?material_type=FLASHCARD`,
      { headers: { 'Authorization': `Bearer ${getToken()}` }}
    );
    const data = await response.json();
    setFlashcards(data);
  };

  // Record attempt
  const recordAttempt = async (materialId: number, isCorrect: boolean) => {
    const response = await fetch('/api/v1/study/attempt', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ material_id: materialId, is_correct: isCorrect })
    });
    const updated = await response.json();
    
    // Update local state
    setFlashcards(prev => 
      prev.map(card => card.id === materialId ? updated : card)
    );
    
    return updated;
  };

  // Get stats
  const loadStats = async () => {
    const response = await fetch(`/api/v1/study/stats/${searchSpaceId}`, {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    const data = await response.json();
    setStats(data);
  };

  useEffect(() => {
    loadFlashcards();
    loadStats();
  }, [searchSpaceId]);

  return {
    flashcards,
    stats,
    loading,
    generateFlashcards,
    loadFlashcards,
    recordAttempt,
    loadStats
  };
}
```

**Usage in Component:**
```tsx
function FlashcardStudy({ searchSpaceId }) {
  const { 
    flashcards, 
    stats, 
    generateFlashcards, 
    recordAttempt 
  } = useStudyMode(searchSpaceId);

  const handleAnswer = async (cardId: number, isCorrect: boolean) => {
    await recordAttempt(cardId, isCorrect);
  };

  return (
    <div>
      <h2>Study Mode</h2>
      <p>Accuracy: {stats?.accuracy_percentage}%</p>
      
      {flashcards.map(card => (
        <FlashCard 
          key={card.id}
          question={card.question}
          answer={card.answer}
          onAnswer={(correct) => handleAnswer(card.id, correct)}
        />
      ))}
    </div>
  );
}
```

---

## Error Handling

All endpoints return standard HTTP status codes:
- `200` - Success
- `401` - Unauthorized (invalid/missing token)
- `404` - Resource not found
- `500` - Server error

**Example:**
```javascript
try {
  const response = await fetch('/api/v1/study/generate', { /* ... */ });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to generate flashcards');
  }
  
  const data = await response.json();
  return data;
} catch (error) {
  console.error('Study mode error:', error);
  // Show error to user
}
```

---

## Quick Start Checklist

1. ✅ Get auth token from login
2. ✅ Call `/generate` with document IDs
3. ✅ Display flashcards to user
4. ✅ Call `/attempt` when user answers
5. ✅ Show `/stats` for progress tracking

---

## Interactive API Docs

For live testing and more examples:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Look for the **"Study Mode"** section.
