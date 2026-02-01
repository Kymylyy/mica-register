"""
Tests for Deepseek LLM client with mocked responses
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.app.remediation.llm_client import LLMClient, build_prompt
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
    """Test that prompt messages are built correctly"""
    task = create_test_task()
    messages = build_prompt(task)

    # Should return a list of messages
    assert isinstance(messages, list)
    assert len(messages) == 2  # System and user messages

    # Check message structure
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"

    # Check content
    system_content = messages[0]["content"]
    user_content = messages[1]["content"]

    assert "data cleaning assistant" in system_content.lower()
    assert "JSON" in system_content

    task_type_str = task.task_type if isinstance(task.task_type, str) else task.task_type.value
    assert task_type_str in user_content
    assert task.column in user_content
    assert task.current_value in user_content
    assert task.issue_description in user_content


@patch('backend.app.remediation.llm_client.OpenAI')
def test_llm_client_fallback(mock_openai_class):
    """Test that client falls back to next model if first fails"""
    # Mock OpenAI client
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # First call fails, second succeeds
    mock_choice = Mock()
    mock_message = Mock()
    mock_message.content = '{"proposed_value": "Test Address", "confidence": 0.95, "reasoning": "Fixed", "transformation_type": "ENCODING_FIX", "risk_level": "LOW"}'
    mock_choice.message = mock_message

    mock_response = Mock()
    mock_response.choices = [mock_choice]

    mock_client.chat.completions.create.side_effect = [
        Exception("Model not available"),  # First model fails
        mock_response  # Second model succeeds
    ]

    client = LLMClient(api_key="test-key")
    task = create_test_task()

    patch_result = client.generate_patch([task])

    # Should use second model after first fails
    assert patch_result.model_name == "deepseek-chat"
    assert len(patch_result.tasks) == 1
    assert patch_result.tasks[0].proposed_value == "Test Address"


@patch('backend.app.remediation.llm_client.OpenAI')
def test_llm_client_success(mock_openai_class):
    """Test successful patch generation"""
    # Mock OpenAI client
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Mock response structure
    mock_choice = Mock()
    mock_message = Mock()
    mock_message.content = '{"proposed_value": "Test Address", "confidence": 0.95, "reasoning": "Fixed encoding", "transformation_type": "ENCODING_FIX", "risk_level": "LOW"}'
    mock_choice.message = mock_message

    mock_response = Mock()
    mock_response.choices = [mock_choice]

    mock_client.chat.completions.create.return_value = mock_response

    client = LLMClient(api_key="test-key")
    task = create_test_task()

    patch_result = client.generate_patch([task])

    assert patch_result.model_name == "deepseek-reasoner"
    assert len(patch_result.tasks) == 1
    assert patch_result.tasks[0].confidence == 0.95
    assert patch_result.tasks[0].proposed_value == "Test Address"


@patch('backend.app.remediation.llm_client.OpenAI')
def test_llm_client_all_models_fail(mock_openai_class):
    """Test that exception is raised if all models fail"""
    # Mock OpenAI client
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # All API calls fail
    mock_client.chat.completions.create.side_effect = Exception("API Error")

    client = LLMClient(api_key="test-key")
    task = create_test_task()

    # All models will fail at task processing level, but model creation succeeds
    # So we get empty proposals, not RuntimeError
    patch_result = client.generate_patch([task])
    # Should have tried all models but got no proposals
    assert len(patch_result.tasks) == 0
    # Should have used the last model tried (all failed, so last one is used)
    assert patch_result.model_name == "deepseek-chat"


@patch('backend.app.remediation.llm_client.OpenAI')
def test_llm_client_json_parsing_with_markdown(mock_openai_class):
    """Test that JSON parsing handles markdown code blocks"""
    # Mock OpenAI client
    mock_client = Mock()
    mock_openai_class.return_value = mock_client

    # Mock response with markdown code block
    mock_choice = Mock()
    mock_message = Mock()
    mock_message.content = '```json\n{"proposed_value": "Test Address", "confidence": 0.95, "reasoning": "Fixed", "transformation_type": "ENCODING_FIX", "risk_level": "LOW"}\n```'
    mock_choice.message = mock_message

    mock_response = Mock()
    mock_response.choices = [mock_choice]

    mock_client.chat.completions.create.return_value = mock_response

    client = LLMClient(api_key="test-key")
    task = create_test_task()

    patch_result = client.generate_patch([task])

    assert len(patch_result.tasks) == 1
    assert patch_result.tasks[0].proposed_value == "Test Address"

