"""
Quiz Logic & User Session Management Module.
Maintains in-memory quiz states independently for each Telegram user,
stores question banks, validates answers, and calculates scores.
"""

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

# ==============================================================================
# Question Bank
# You can easily add more questions or modify existing ones below!
# ==============================================================================
QUESTIONS_DATABASE: List[Dict[str, Any]] = [
    {
        "question": "What is the result of 2 ** 3 in Python?",
        "options": ["5", "6", "8", "9"],
        "answer": "8",
        "explanation": "In Python, '**' is the exponentiation operator. 2 ** 3 = 2 × 2 × 2 = 8."
    },
    {
        "question": "Which keyword is used to define a function in Python?",
        "options": ["func", "define", "def", "function"],
        "answer": "def",
        "explanation": "The 'def' keyword is used to declare a function header (e.g., 'def greet():')."
    },
    {
        "question": "What data type is the result of: type(3.14)?",
        "options": ["int", "float", "double", "decimal"],
        "answer": "float",
        "explanation": "Numbers with decimal points are represented by the 'float' type in Python."
    },
    {
        "question": "Which built-in collection is ordered and mutable?",
        "options": ["tuple", "list", "set", "frozenset"],
        "answer": "list",
        "explanation": "Lists (e.g. [1, 2, 3]) maintain element order and can be changed in-place."
    },
    {
        "question": "What does the len() function return?",
        "options": [
            "Memory size in bytes",
            "Number of items in an object",
            "Largest value",
            "Smallest value"
        ],
        "answer": "Number of items in an object",
        "explanation": "len() returns the length (count of items) of a sequence or collection."
    },
    {
        "question": "How do you write a single-line comment in Python?",
        "options": ["// comment", "/* comment */", "# comment", "-- comment"],
        "answer": "# comment",
        "explanation": "The '#' symbol begins a single-line comment in Python."
    },
    {
        "question": "What is the output of bool('False') in Python?",
        "options": ["True", "False", "None", "Error"],
        "answer": "True",
        "explanation": "Any non-empty string in Python evaluates to True in boolean context."
    },
    {
        "question": "Which method is used to add an item to the end of a list?",
        "options": ["push()", "add()", "append()", "insert()"],
        "answer": "append()",
        "explanation": "The .append(item) method adds an element to the end of an existing list."
    }
]


# ==============================================================================
# User Quiz Session Model
# ==============================================================================
@dataclass
class QuizSession:
    """Represents an active quiz session for an individual user."""
    user_id: int
    questions: List[Dict[str, Any]]
    current_index: int = 0
    score: int = 0
    is_active: bool = True
    user_answers: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def total_questions(self) -> int:
        return len(self.questions)

    @property
    def is_finished(self) -> bool:
        return self.current_index >= self.total_questions

    def get_current_question(self) -> Optional[Dict[str, Any]]:
        """Returns the current active question or None if finished."""
        if self.is_finished:
            return None
        return self.questions[self.current_index]

    def submit_answer(self, chosen_option: str) -> tuple[bool, str, str]:
        """
        Validates user choice, updates score, advances question counter.
        Returns: (is_correct, correct_answer_text, explanation_text)
        """
        current_q = self.get_current_question()
        if not current_q:
            return False, "", "No active question."

        correct = str(current_q["answer"]).strip()
        explanation = current_q.get("explanation", "Great question!")
        is_correct = chosen_option.strip() == correct

        if is_correct:
            self.score += 1

        self.user_answers.append({
            "question": current_q["question"],
            "chosen": chosen_option,
            "correct": correct,
            "is_correct": is_correct,
            "explanation": explanation
        })

        self.current_index += 1
        if self.is_finished:
            self.is_active = False

        return is_correct, correct, explanation


# ==============================================================================
# Multi-User Session Store
# ==============================================================================
# Mapping from Telegram user_id -> QuizSession
_USER_SESSIONS: Dict[int, QuizSession] = {}


def get_user_session(user_id: int) -> Optional[QuizSession]:
    """Retrieve existing session for user."""
    return _USER_SESSIONS.get(user_id)


def start_new_quiz_session(user_id: int, num_questions: int = 5) -> QuizSession:
    """
    Creates a new 5-question randomized quiz session for this user.
    Independent for every Telegram user ID.
    """
    # Sample questions randomly without repeating
    available_questions = list(QUESTIONS_DATABASE)
    random.shuffle(available_questions)
    selected_questions = available_questions[: min(num_questions, len(available_questions))]

    session = QuizSession(
        user_id=user_id,
        questions=selected_questions,
        current_index=0,
        score=0,
        is_active=True
    )
    _USER_SESSIONS[user_id] = session
    return session


def clear_user_session(user_id: int) -> None:
    """Clears user session from memory."""
    _USER_SESSIONS.pop(user_id, None)


def calculate_percentage(score: int, total: int) -> float:
    """Calculate percentage rounded to 1 decimal place."""
    if total <= 0:
        return 0.0
    return round((score / total) * 100, 1)


def get_feedback_message(percentage: float) -> str:
    """
    Returns motivational feedback based on performance percentage:
      90-100% → "Excellent work! 🌟"
      70-89%  → "Great job! 👍"
      50-69%  → "Good effort! Keep practicing. 💪"
      Below 50% → "Keep learning and try again! 📚"
    """
    if percentage >= 90.0:
        return "Excellent work! 🌟 Outstanding mastery of the concepts!"
    elif percentage >= 70.0:
        return "Great job! 👍 You have a strong grasp of Python basics!"
    elif percentage >= 50.0:
        return "Good effort! Keep practicing. 💪 You're making good progress!"
    else:
        return "Keep learning and try again! 📚 Review the fundamentals and take another shot!"
