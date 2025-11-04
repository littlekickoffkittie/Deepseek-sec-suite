#!/usr/bin/env python3
"""
Unit tests for HackerOne API client
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from hackerone_api import HackerOneAPI


class TestHackerOneAPI:
    """Test suite for HackerOne API client"""

    def test_init_with_valid_credentials(self):
        """Test initialization with valid credentials"""
        client = HackerOneAPI("testuser", "testtoken")
        assert client.auth == ("testuser", "testtoken")
        assert client.timeout == 30
        assert "Accept" in client.headers
        assert "application/json" in client.headers["Accept"]

    def test_init_without_credentials(self):
        """Test initialization fails without credentials"""
        with pytest.raises(ValueError, match="username and API token are required"):
            HackerOneAPI("", "")

    def test_init_with_custom_timeout(self):
        """Test initialization with custom timeout"""
        client = HackerOneAPI("testuser", "testtoken", timeout=60)
        assert client.timeout == 60

    @patch('requests.request')
    def test_make_request_success(self, mock_request):
        """Test successful API request"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "1"}]}
        mock_request.return_value = mock_response

        client = HackerOneAPI("testuser", "testtoken")
        result = client._make_request("GET", "hackers/programs")

        assert result == {"data": [{"id": "1"}]}
        mock_request.assert_called_once()

    @patch('requests.request')
    def test_make_request_401_error(self, mock_request):
        """Test authentication failure"""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_request.return_value = mock_response

        client = HackerOneAPI("baduser", "badtoken")

        with pytest.raises(Exception, match="Authentication failed"):
            client._make_request("GET", "hackers/programs")

    @patch('requests.request')
    def test_make_request_404_error(self, mock_request):
        """Test resource not found"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_request.return_value = mock_response

        client = HackerOneAPI("testuser", "testtoken")

        with pytest.raises(Exception, match="Resource not found"):
            client._make_request("GET", "hackers/programs/nonexistent")

    @patch('requests.request')
    def test_make_request_timeout(self, mock_request):
        """Test request timeout"""
        mock_request.side_effect = requests.exceptions.Timeout()

        client = HackerOneAPI("testuser", "testtoken", timeout=5)

        with pytest.raises(Exception, match="timed out"):
            client._make_request("GET", "hackers/programs")

    @patch('requests.request')
    def test_list_programs(self, mock_request):
        """Test listing programs"""
        # Mock first page
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            "data": [
                {"id": "1", "attributes": {"handle": "program1", "name": "Program 1"}},
                {"id": "2", "attributes": {"handle": "program2", "name": "Program 2"}}
            ],
            "links": {"next": "page2"}
        }

        # Mock second page (last page)
        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {
            "data": [
                {"id": "3", "attributes": {"handle": "program3", "name": "Program 3"}}
            ],
            "links": {}  # No next link
        }

        mock_request.side_effect = [mock_response1, mock_response2]

        client = HackerOneAPI("testuser", "testtoken")
        programs = client.list_programs(page_size=2)

        assert len(programs) == 3
        assert programs[0]["id"] == "1"
        assert programs[2]["id"] == "3"
        assert mock_request.call_count == 2

    @patch('requests.request')
    def test_get_program(self, mock_request):
        """Test getting specific program details"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "id": "1",
                "attributes": {
                    "handle": "security",
                    "name": "HackerOne",
                    "url": "https://hackerone.com/security"
                }
            }
        }
        mock_request.return_value = mock_response

        client = HackerOneAPI("testuser", "testtoken")
        program = client.get_program("security")

        assert program["id"] == "1"
        assert program["attributes"]["handle"] == "security"
        mock_request.assert_called_once()

    def test_search_programs(self):
        """Test searching programs"""
        programs = [
            {"attributes": {"handle": "stripe", "name": "Stripe"}},
            {"attributes": {"handle": "security", "name": "HackerOne"}},
            {"attributes": {"handle": "rails", "name": "Ruby on Rails"}}
        ]

        client = HackerOneAPI("testuser", "testtoken")

        # Search by handle
        matches = client.search_programs("stripe", programs)
        assert len(matches) == 1
        assert matches[0]["attributes"]["handle"] == "stripe"

        # Search by name (case insensitive)
        matches = client.search_programs("hackerone", programs)
        assert len(matches) == 1
        assert matches[0]["attributes"]["handle"] == "security"

        # Search with no matches
        matches = client.search_programs("nonexistent", programs)
        assert len(matches) == 0

        # Search partial match
        matches = client.search_programs("rail", programs)
        assert len(matches) == 1
        assert matches[0]["attributes"]["handle"] == "rails"

    def test_format_program_details(self):
        """Test formatting program details"""
        program = {
            "attributes": {
                "name": "Test Program",
                "handle": "testprog",
                "url": "https://hackerone.com/testprog",
                "state": "open",
                "submission_state": "open",
                "offers_bounties": True,
                "offers_swag": False,
                "resolved_report_count": 100,
                "currency": "USD",
                "structured_scopes": {
                    "data": [
                        {
                            "attributes": {
                                "asset_type": "URL",
                                "asset_identifier": "https://example.com",
                                "eligible_for_bounty": True,
                                "eligible_for_submission": True
                            }
                        }
                    ]
                },
                "targets_out_of_scope": "*.example.com/admin",
                "policy": "Please follow responsible disclosure"
            }
        }

        client = HackerOneAPI("testuser", "testtoken")
        formatted = client.format_program_details(program)

        assert "Test Program" in formatted
        assert "testprog" in formatted
        assert "https://example.com" in formatted
        assert "URL" in formatted
        assert "*.example.com/admin" in formatted
        assert "responsible disclosure" in formatted

    def test_export_program_for_analysis(self):
        """Test exporting program for AI analysis"""
        program = {
            "attributes": {
                "name": "Test Program",
                "handle": "testprog",
                "url": "https://hackerone.com/testprog",
                "state": "open",
                "submission_state": "open",
                "offers_bounties": True,
                "structured_scopes": {
                    "data": [
                        {
                            "attributes": {
                                "asset_type": "URL",
                                "asset_identifier": "https://example.com",
                                "eligible_for_bounty": True
                            }
                        }
                    ]
                },
                "targets_out_of_scope": "Admin panels",
                "policy": "Test responsibly"
            }
        }

        client = HackerOneAPI("testuser", "testtoken")
        exported = client.export_program_for_analysis(program)

        assert "BUG BOUNTY PROGRAM DETAILS" in exported
        assert "Test Program" in exported
        assert "IN SCOPE TARGETS" in exported
        assert "https://example.com" in exported
        assert "OUT OF SCOPE" in exported
        assert "Admin panels" in exported
        assert "POLICY & RULES" in exported
        assert "Test responsibly" in exported


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
