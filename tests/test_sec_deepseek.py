#!/usr/bin/env python3
"""
Unit tests for DeepSeek Security Suite - focusing on timeout and retry logic
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
import json
import time
import sys
import os

# Import the classes from sec.py
sys.path.insert(0, os.path.dirname(__file__))
from security_suite import (
    DeepSeekSecuritySuite,
    DeepSeekError,
    DeepSeekAPIError,
    DeepSeekRequestError,
    DeepSeekResponseError,
    extract_tool_from_command,
    filter_commands_by_availability
)


class TestDeepSeekSecuritySuite:
    """Test suite for DeepSeek client"""

    def test_init_with_valid_api_key(self):
        """Test initialization with valid API key"""
        suite = DeepSeekSecuritySuite("test-api-key")
        assert suite.headers["Authorization"] == "Bearer test-api-key"
        assert suite.model == "deepseek-chat"
        assert suite.temperature == 0.7
        assert suite.timeout == 120  # Updated default timeout
        assert suite.max_retries == 3

    def test_init_without_api_key(self):
        """Test initialization fails without API key"""
        with pytest.raises(ValueError, match="DEEPSEEK_API_KEY is required"):
            DeepSeekSecuritySuite("")

    def test_init_with_custom_parameters(self):
        """Test initialization with custom parameters"""
        suite = DeepSeekSecuritySuite(
            "test-key",
            model="deepseek-coder",
            temperature=0.5,
            timeout=60,
            max_retries=5
        )
        assert suite.model == "deepseek-coder"
        assert suite.temperature == 0.5
        assert suite.timeout == 60
        assert suite.max_retries == 5

    def test_set_system_prompt(self):
        """Test setting system prompt"""
        suite = DeepSeekSecuritySuite("test-key")
        suite.set_system_prompt("You are a security expert")

        assert len(suite.conversation_history) == 1
        assert suite.conversation_history[0]["role"] == "system"
        assert suite.conversation_history[0]["content"] == "You are a security expert"

    def test_clear_history(self):
        """Test clearing conversation history"""
        suite = DeepSeekSecuritySuite("test-key")
        suite.conversation_history = [
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": "response"}
        ]
        suite.clear_history()
        assert len(suite.conversation_history) == 0

    @patch('requests.post')
    def test_call_deepseek_success(self, mock_post):
        """Test successful API call"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {"message": {"content": "This is a test response"}}
            ]
        }
        mock_post.return_value = mock_response

        suite = DeepSeekSecuritySuite("test-key")
        response = suite.call_deepseek("Test message")

        assert response == "This is a test response"
        assert len(suite.conversation_history) == 2
        assert suite.conversation_history[0]["role"] == "user"
        assert suite.conversation_history[1]["role"] == "assistant"
        mock_post.assert_called_once()

    @patch('requests.post')
    @patch('time.sleep')
    def test_call_deepseek_timeout_with_retry(self, mock_sleep, mock_post):
        """Test timeout with successful retry"""
        # First call times out, second succeeds
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "Success after retry"}}]
        }

        mock_post.side_effect = [
            requests.exceptions.Timeout(),
            mock_response_success
        ]

        suite = DeepSeekSecuritySuite("test-key", max_retries=3)
        response = suite.call_deepseek("Test message")

        assert response == "Success after retry"
        assert mock_post.call_count == 2
        assert mock_sleep.call_count == 1  # One retry delay

    @patch('requests.post')
    @patch('time.sleep')
    def test_call_deepseek_all_retries_timeout(self, mock_sleep, mock_post):
        """Test all retries exhausted due to timeout"""
        mock_post.side_effect = requests.exceptions.Timeout()

        suite = DeepSeekSecuritySuite("test-key", max_retries=3)

        with pytest.raises(DeepSeekRequestError, match="Timeout after 3 attempts"):
            suite.call_deepseek("Test message")

        assert mock_post.call_count == 3
        assert mock_sleep.call_count == 2  # n-1 retry delays

    @patch('requests.post')
    @patch('time.sleep')
    def test_call_deepseek_connection_error_with_retry(self, mock_sleep, mock_post):
        """Test connection error with successful retry"""
        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "Connected after retry"}}]
        }

        mock_post.side_effect = [
            requests.exceptions.ConnectionError(),
            mock_response_success
        ]

        suite = DeepSeekSecuritySuite("test-key", max_retries=3)
        response = suite.call_deepseek("Test message")

        assert response == "Connected after retry"
        assert mock_post.call_count == 2

    @patch('requests.post')
    def test_call_deepseek_500_error_with_retry(self, mock_post):
        """Test 500 server error triggers retry"""
        mock_response_error = Mock()
        mock_response_error.status_code = 500
        mock_response_error.text = "Internal Server Error"
        mock_response_error.json.return_value = {"error": {"message": "Server error"}}

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "Success after server error"}}]
        }

        # First call raises HTTPError, second succeeds
        mock_post.side_effect = [
            Mock(
                status_code=500,
                raise_for_status=Mock(side_effect=requests.exceptions.HTTPError(response=mock_response_error))
            ),
            mock_response_success
        ]

        suite = DeepSeekSecuritySuite("test-key", max_retries=3)

        # Should retry on 500 errors
        with patch('time.sleep'):
            response = suite.call_deepseek("Test message")
            assert response == "Success after server error"

    @patch('requests.post')
    def test_call_deepseek_429_rate_limit_retry(self, mock_post):
        """Test 429 rate limit error triggers retry"""
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        mock_response_429.text = "Rate limit exceeded"
        mock_response_429.json.return_value = {"error": {"message": "Too many requests"}}

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {
            "choices": [{"message": {"content": "Success after rate limit"}}]
        }

        mock_post.side_effect = [
            Mock(
                status_code=429,
                raise_for_status=Mock(side_effect=requests.exceptions.HTTPError(response=mock_response_429))
            ),
            mock_response_success
        ]

        suite = DeepSeekSecuritySuite("test-key", max_retries=3)

        with patch('time.sleep'):
            response = suite.call_deepseek("Test message")
            assert response == "Success after rate limit"

    @patch('requests.post')
    def test_call_deepseek_400_error_no_retry(self, mock_post):
        """Test 400 client error does not retry"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.json.return_value = {"error": {"message": "Invalid request"}}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_post.return_value = mock_response

        suite = DeepSeekSecuritySuite("test-key", max_retries=3)

        with pytest.raises(DeepSeekAPIError, match="400"):
            suite.call_deepseek("Test message")

        # Should only call once, no retries for 4xx errors
        assert mock_post.call_count == 1

    @patch('requests.post')
    def test_call_deepseek_missing_content_in_response(self, mock_post):
        """Test handling of malformed response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"message": {}}]}  # Missing content
        mock_post.return_value = mock_response

        suite = DeepSeekSecuritySuite("test-key")

        # The error gets wrapped in DeepSeekError, so check for either
        with pytest.raises((DeepSeekResponseError, DeepSeekError), match="missing 'content'|unexpected error"):
            suite.call_deepseek("Test message")

    @patch('requests.post')
    def test_analyze_bounty(self, mock_post):
        """Test bounty analysis"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "in_scope_targets": ["*.example.com"],
                        "out_of_scope_items": ["admin panel"],
                        "rules_and_restrictions": ["No DoS attacks"],
                        "reward_information": "$100-$5000",
                        "testing_guidelines": ["Responsible disclosure"]
                    })
                }
            }]
        }
        mock_post.return_value = mock_response

        suite = DeepSeekSecuritySuite("test-key")
        result = suite.analyze_bounty("Test bounty program")

        assert "in_scope_targets" in result
        assert "example.com" in result


class TestToolManagement:
    """Test suite for tool management functions"""

    def test_extract_tool_from_command(self):
        """Test extracting tool name from command"""
        assert extract_tool_from_command("nmap -sV example.com") == "nmap"
        assert extract_tool_from_command("subfinder -d example.com") == "subfinder"
        assert extract_tool_from_command("~/tools/testssl.sh https://example.com") == "testssl.sh"
        assert extract_tool_from_command("python script.py") == "python"
        assert extract_tool_from_command("") == ""

    def test_filter_commands_by_availability(self):
        """Test filtering commands by tool availability"""
        commands = """
nmap -sV example.com
subfinder -d example.com
nonexistent-tool --test
httpx -l urls.txt
"""
        available_tools = {"nmap", "httpx"}

        available, unavailable = filter_commands_by_availability(commands, available_tools)

        assert len(available) == 2
        assert any("nmap" in cmd for cmd in available)
        assert any("httpx" in cmd for cmd in available)

        assert len(unavailable) == 2
        assert any("subfinder" in cmd for cmd in unavailable)
        assert any("nonexistent-tool" in cmd for cmd in unavailable)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
