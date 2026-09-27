"""
AI Agent Module for Telegram Quiz Bot.
Uses OpenAI API to dynamically generate structured, verified educational quizzes
and generate interactive explanations based on user prompts.
"""

import json
import logging
from typing import List, Dict, Any, Tuple, Optional
from openai import AsyncOpenAI, APIError, AuthenticationError, RateLimitError
from pydantic import BaseModel, Field, ValidationError

import config

logger = logging.getLogger(__name__)


# ==============================================================================
# Pydantic Schemas for Strict Output Validation
# ==============================================================================
class QuestionModel(BaseModel):
    question: str = Field(..., description="The multiple choice question text")
    options: List[str] = Field(..., min_length=4, max_length=4, description="List of exactly 4 options")
    answer: str = Field(..., description="The correct option string, exactly matching one item in options")
    explanation: str = Field(..., description="Brief 1-2 sentence educational explanation of why this answer is correct")


class QuizPayloadModel(BaseModel):
    topic: str = Field(..., description="Topic of the quiz")
    difficulty: str = Field(default="beginner", description="Difficulty level")
    questions: List[QuestionModel] = Field(..., min_length=1, max_length=10, description="List of validated questions")


# ==============================================================================
# AI Agent Implementation
# ==============================================================================
class QuizAIAgent:
    """
    Intelligent Agent capable of understanding user requests,
    determining difficulty, and generating structured, verified quiz sets.
    """

    def __init__(self):
        self.api_key = config.OPENAI_API_KEY
        self.model = config.OPENAI_MODEL
        self._client: Optional[AsyncOpenAI] = None

    @property
    def client(self) -> Optional[AsyncOpenAI]:
        """Lazy initialization of AsyncOpenAI client."""
        if not config.is_openai_enabled():
            return None
        if self._client is None:
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def generate_custom_quiz(
        self, user_request: str, num_questions: int = config.DEFAULT_NUM_QUESTIONS
    ) -> Tuple[bool, Any, str]:
        """
        Parses a natural language prompt from the user, generates a tailored quiz,
        validates the schema and answer integrity, and returns structured data.

        Returns:
            Tuple[bool, Union[List[Dict[str, Any]], str], str]:
            (success_bool, questions_list_or_error_message, topic_name)
        """
        if not config.is_openai_enabled():
            return (
                False,
                "⚠️ OpenAI API key is not configured.\n"
                "Please add `OPENAI_API_KEY` to your `.env` file to use AI-generated quizzes.\n"
                "In the meantime, you can use /quiz for the built-in Python quiz!",
                "General"
            )

        system_prompt = (
            "You are an expert educational AI Quiz Generator. "
            "Your task is to generate high quality, clear, multiple-choice educational quiz questions based on the user's request.\n\n"
            "Requirements:\n"
            f"1. Generate exactly {num_questions} multiple-choice questions.\n"
            "2. Each question MUST have exactly 4 unique options.\n"
            "3. 'answer' MUST exactly match one of the items in the 'options' list (exact string match).\n"
            "4. Provide a clear, concise (1-2 sentences) 'explanation' for each question explaining why the answer is correct.\n"
            "5. Automatically infer the subject, topic, and difficulty (beginner, intermediate, advanced) from the prompt.\n"
            "6. Output MUST be strictly valid JSON matching this schema:\n"
            "{\n"
            '  "topic": "Extracted Topic Title",\n'
            '  "difficulty": "beginner/intermediate/advanced",\n'
            '  "questions": [\n'
            "    {\n"
            '      "question": "Question text?",\n'
            '      "options": ["Option A", "Option B", "Option C", "Option D"],\n'
            '      "answer": "Option B",\n'
            '      "explanation": "Explanation why Option B is correct."\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        user_prompt = f"User Request: {user_request}\nGenerate {num_questions} multiple-choice questions in valid JSON."

        try:
            client = self.client
            if not client:
                return False, "OpenAI client initialization failed.", "General"

            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000
            )

            raw_content = response.choices[0].message.content
            if not raw_content:
                return False, "Received empty response from AI model.", "General"

            # Parse JSON
            data = json.loads(raw_content)

            # Validate using Pydantic schema
            validated_payload = QuizPayloadModel.model_validate(data)

            # Verify that every question's answer is strictly one of its 4 options
            cleaned_questions: List[Dict[str, Any]] = []
            for q in validated_payload.questions:
                # Find matching option
                matching_opts = [opt for opt in q.options if opt.strip().lower() == q.answer.strip().lower()]
                if not matching_opts:
                    # If answer text slightly differs, attempt safe match or fix
                    logger.warning(f"Answer '{q.answer}' not in options {q.options}. Skipping question.")
                    continue

                cleaned_questions.append({
                    "question": q.question.strip(),
                    "options": [opt.strip() for opt in q.options],
                    "answer": matching_opts[0].strip(),
                    "explanation": q.explanation.strip()
                })

            if len(cleaned_questions) < 1:
                return (
                    False,
                    "Generated questions did not meet structural validation checks. Please try a different query.",
                    validated_payload.topic
                )

            return True, cleaned_questions, f"{validated_payload.topic} ({validated_payload.difficulty.capitalize()})"

        except AuthenticationError:
            logger.error("OpenAI Authentication failed. Check your API key.")
            return (
                False,
                "🔑 Invalid OpenAI API Key. Please check your `OPENAI_API_KEY` in `.env`.",
                "Error"
            )
        except RateLimitError:
            logger.error("OpenAI Rate limit exceeded.")
            return (
                False,
                "⏳ OpenAI API rate limit exceeded. Please wait a moment and try again.",
                "Error"
            )
        except (ValidationError, json.JSONDecodeError) as val_err:
            logger.error(f"Validation error in AI response: {val_err}")
            return (
                False,
                "⚠️ Failed to parse AI quiz structure. Please try asking again in slightly different words.",
                "Error"
            )
        except APIError as api_err:
            logger.error(f"OpenAI API Error: {api_err}")
            return (
                False,
                f"⚠️ OpenAI service error: {api_err.message if hasattr(api_err, 'message') else 'Temporary API issue'}.",
                "Error"
            )
        except Exception as e:
            logger.error(f"Unexpected error in AI Agent: {e}", exc_info=True)
            return (
                False,
                "⚠️ An unexpected error occurred while generating the quiz. Please try again later.",
                "Error"
            )


# Global singleton agent instance
ai_agent = QuizAIAgent()
