"""
Deepseek LLM Client for Remediation

Provides interface to Deepseek API with fallback to multiple models.
Tries models in order: deepseek-reasoner → deepseek-chat
"""

import os
import json
from typing import List, Optional, Dict, Any
from pathlib import Path

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    # Load .env from project root (2 levels up from this file)
    env_path = Path(__file__).parent.parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv not installed, skip loading .env
    pass

from openai import OpenAI
from .schemas import RemediationTask, RemediationPatch, PatchProposal, TransformationType, RiskLevel


# Model fallback order
# deepseek-reasoner: thinking mode, better for complex cases
# deepseek-chat: non-thinking mode, faster
DEEPSEEK_MODELS = [
    "deepseek-reasoner",  # Primary model (thinking mode)
    "deepseek-chat",      # Fallback (non-thinking mode, faster)
]

DEEPSEEK_BASE_URL = "https://api.deepseek.com"

def get_api_key() -> str:
    """Get Deepseek API key from environment variable"""
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError(
            "DEEPSEEK_API_KEY environment variable not set. "
            "Please set it in your .env file or environment."
        )
    return api_key


def build_prompt(task: RemediationTask) -> List[Dict[str, str]]:
    """Build prompt messages for LLM based on task"""
    context_str = "\n".join([f"{k}: {v}" for k, v in task.context.context.items()])

    # Get task_type as string (Pydantic uses enum values with use_enum_values=True)
    task_type_str = task.task_type if isinstance(task.task_type, str) else task.task_type.value

    system_message = """You are a data cleaning assistant for ESMA CASP register CSV files.

Your task is to propose corrected values for data quality issues.

Requirements:
1. Only fix the specific issue mentioned
2. Do not change other parts of the value
3. Maintain data integrity
4. Use standard formats (dates: DD/MM/YYYY, country codes: uppercase ISO codes)
5. For encoding fixes, use proper Unicode characters (e.g., ß, ä, ö, ü)

Respond with a JSON object:
{
    "proposed_value": "corrected value here",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of the fix",
    "transformation_type": "ENCODING_FIX or DATE_FORMAT or COUNTRY_CODE or STANDARDIZATION",
    "risk_level": "LOW" or "MEDIUM" or "HIGH"
}

Only return the JSON object, no other text."""

    user_message = f"""Task Type: {task_type_str}
Column: {task.column}
Current Value: {task.current_value}
Issue: {task.issue_description}

Context (other columns from the same row):
{context_str}

Please provide a corrected value for the {task.column} column."""

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message}
    ]


class LLMClient:
    """Client for Deepseek API with model fallback"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_api_key()
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=DEEPSEEK_BASE_URL
        )
        self.models = DEEPSEEK_MODELS.copy()
        self.last_used_model: Optional[str] = None

    def generate_patch(self, tasks: List[RemediationTask]) -> RemediationPatch:
        """
        Generate remediation patch from tasks using Deepseek API.

        Tries models in fallback order until one succeeds.

        Args:
            tasks: List of remediation tasks

        Returns:
            RemediationPatch with proposals
        """
        proposals: List[PatchProposal] = []
        used_model = None

        for model_name in self.models:
            try:
                used_model = model_name
                self.last_used_model = model_name

                # Process each task
                for task in tasks:
                    try:
                        messages = build_prompt(task)
                        response = self.client.chat.completions.create(
                            model=model_name,
                            messages=messages,
                            stream=False,
                            temperature=0.0,
                            max_tokens=500
                        )

                        # Parse response - OpenAI format
                        if response.choices and len(response.choices) > 0:
                            response_text = response.choices[0].message.content.strip()
                        else:
                            response_text = ""

                        # Skip if response is empty
                        if not response_text:
                            print(f"Empty response from {model_name} for task {task.task_id}")
                            continue

                        # Remove markdown code blocks if present
                        if response_text.startswith("```json"):
                            response_text = response_text[7:]
                        if response_text.startswith("```"):
                            response_text = response_text[3:]
                        if response_text.endswith("```"):
                            response_text = response_text[:-3]
                        response_text = response_text.strip()

                        if not response_text:
                            print(f"Empty response after cleaning from {model_name} for task {task.task_id}")
                            continue

                        proposal_data = json.loads(response_text)

                        # Create proposal
                        # Get task_type as string for fallback
                        task_type_str = task.task_type if isinstance(task.task_type, str) else task.task_type.value
                        proposal = PatchProposal(
                            task_id=task.task_id,
                            proposed_value=proposal_data.get("proposed_value", task.current_value),
                            confidence=float(proposal_data.get("confidence", 0.5)),
                            reasoning=proposal_data.get("reasoning", ""),
                            transformation_type=TransformationType(proposal_data.get("transformation_type", task_type_str)),
                            risk_level=RiskLevel(proposal_data.get("risk_level", "MEDIUM"))
                        )

                        proposals.append(proposal)

                    except Exception as e:
                        # Skip this task if it fails
                        print(f"Error processing task {task.task_id} with {model_name}: {e}")
                        continue

                # If we got at least one proposal, model worked
                if proposals:
                    break
                else:
                    # No proposals - try next model
                    print(f"No proposals generated with {model_name}, trying next model...")
                    continue

            except Exception as e:
                # Try next model
                print(f"Error with model {model_name}: {e}")
                continue

        if not used_model:
            raise RuntimeError("All Deepseek models failed. Check API key and network connection.")

        # If no proposals were generated, still create patch but with empty tasks
        # This allows graceful degradation
        if not proposals:
            print(f"Warning: No proposals generated with any model. Created empty patch.")

        # Create patch
        patch = RemediationPatch(
            model_name=used_model,
            tasks=proposals,
            metadata={
                "models_tried": self.models,
                "model_used": used_model,
                "tasks_processed": len(proposals),
                "tasks_total": len(tasks),
            }
        )

        return patch


# Backward compatibility alias
GeminiLLMClient = LLMClient

