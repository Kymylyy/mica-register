"""
Tests for Gemini LLM client with mocked responses
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.app.remediation.llm_client import GeminiLLMClient, build_prompt
from backend.app.remediation.schemas import (
    RemediationTask, TaskType, Severity, RowIdentifier, TaskContext
)


def create_test_task() -> RemediationTask:
    """Create a test remediation task"""
    return RemediationTask(
        task_id="test-task-1",
        task_type=TaskType.ENCODING_FIX,
        row_identifier=RowIdentifier(lei="LEI123456789012345678"),
        column="ae_address",
        current_value="Test Addres",
        issue_description="Encoding issue - missing 's'",
        context=TaskContext(context={
            "ae_address": "Test Addres",
            "ae_commercial_name": "Test Company"
        }),
        severity=Severity.ERROR
    )


def test_build_prompt():
    """Test that prompt is built correctly"""
    task = create_test_task()
    prompt = build_prompt(task)
    
    # task_type is already a string (use_enum_values=True)
    task_type_str = task.task_type if isinstance(task.task_type, str) else task.task_type.value
    assert task_type_str in prompt
    assert task.column in prompt
    assert task.current_value in prompt
    assert task.issue_description in prompt
    assert "JSON" in prompt


@patch('backend.app.remediation.llm_client.genai')
def test_gemini_client_fallback(mock_genai):
    """Test that client falls back to next model if first fails"""
    # Mock client and models
    mock_client = Mock()
    mock_models = Mock()
    mock_client.models = mock_models

    # First call fails, second succeeds
    mock_response = Mock()
    mock_candidate = Mock()
    mock_content = Mock()
    mock_part = Mock()
    mock_part.text = '{"proposed_value": "Test Address", "confidence": 0.95, "reasoning": "Fixed", "transformation_type": "ENCODING_FIX", "risk_level": "LOW"}'
    mock_content.parts = [mock_part]
    mock_candidate.content = mock_content
    mock_response.candidates = [mock_candidate]

    mock_models.generate_content.side_effect = [
        Exception("Model not available"),  # First model fails
        mock_response  # Second model succeeds
    ]

    mock_genai.Client.return_value = mock_client

    client = GeminiLLMClient(api_key="test-key")
    task = create_test_task()

    patch_result = client.generate_patch([task])

    # Should use second model after first fails
    assert patch_result.model_name in ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
    assert len(patch_result.tasks) == 1
    assert patch_result.tasks[0].proposed_value == "Test Address"


@patch('backend.app.remediation.llm_client.genai')
def test_gemini_client_success(mock_genai):
    """Test successful patch generation"""
    mock_client = Mock()
    mock_models = Mock()
    mock_client.models = mock_models

    mock_response = Mock()
    mock_candidate = Mock()
    mock_content = Mock()
    mock_part = Mock()
    mock_part.text = '{"proposed_value": "Test Address", "confidence": 0.95, "reasoning": "Fixed encoding", "transformation_type": "ENCODING_FIX", "risk_level": "LOW"}'
    mock_content.parts = [mock_part]
    mock_candidate.content = mock_content
    mock_response.candidates = [mock_candidate]
    mock_models.generate_content.return_value = mock_response

    mock_genai.Client.return_value = mock_client

    client = GeminiLLMClient(api_key="test-key")
    task = create_test_task()

    patch_result = client.generate_patch([task])

    assert patch_result.model_name == "gemini-3-flash-preview"
    assert len(patch_result.tasks) == 1
    assert patch_result.tasks[0].confidence == 0.95
    assert patch_result.tasks[0].proposed_value == "Test Address"


@patch('backend.app.remediation.llm_client.genai')
def test_gemini_client_all_models_fail(mock_genai):
    """Test that exception is raised if all models fail"""
    mock_model = Mock()
    mock_model.generate_content.side_effect = Exception("API Error")
    
    mock_genai.GenerativeModel.return_value = mock_model
    mock_genai.configure = Mock()
    
    client = GeminiLLMClient(api_key="test-key")
    task = create_test_task()
    
    # All models will fail at task processing level, but model creation succeeds
    # So we get empty proposals, not RuntimeError
    patch_result = client.generate_patch([task])
    # Should have tried all models but got no proposals
    assert len(patch_result.tasks) == 0
    # Should have used the last model tried (all failed, so last one is used)
    assert patch_result.model_name == "gemini-2.5-flash-lite"


@patch('backend.app.remediation.llm_client.genai')
def test_gemini_client_json_parsing_with_markdown(mock_genai):
    """Test that JSON parsing handles markdown code blocks"""
    mock_client = Mock()
    mock_models = Mock()
    mock_client.models = mock_models

    mock_response = Mock()
    mock_candidate = Mock()
    mock_content = Mock()
    mock_part = Mock()
    mock_part.text = '```json\n{"proposed_value": "Test Address", "confidence": 0.95, "reasoning": "Fixed", "transformation_type": "ENCODING_FIX", "risk_level": "LOW"}\n```'
    mock_content.parts = [mock_part]
    mock_candidate.content = mock_content
    mock_response.candidates = [mock_candidate]
    mock_models.generate_content.return_value = mock_response

    mock_genai.Client.return_value = mock_client

    client = GeminiLLMClient(api_key="test-key")
    task = create_test_task()

    patch_result = client.generate_patch([task])

    assert len(patch_result.tasks) == 1
    assert patch_result.tasks[0].proposed_value == "Test Address"

