import pytest
from unittest.mock import Mock, patch
import requests
from hackerone_api import HackerOneAPI

@pytest.fixture
def mock_h1_client():
    """Fixture for a HackerOneAPI client with mocked requests."""
    with patch('requests.get') as mock_get:
        yield HackerOneAPI("testuser", "testtoken"), mock_get

class TestHackerOneAPI:
    """Test suite for the updated HackerOne API client."""

    def test_init_with_valid_credentials(self):
        """Test initialization with valid credentials."""
        client = HackerOneAPI("testuser", "testtoken")
        assert client.auth == ("testuser", "testtoken")
        assert client.timeout == 30
        assert "Accept" in client.headers
        assert client.headers["Accept"] == "application/json"

    def test_init_without_credentials(self):
        """Test initialization fails without credentials."""
        with pytest.raises(ValueError, match="HackerOne username and token are required."):
            HackerOneAPI("", "")

    def test_make_request_success(self, mock_h1_client):
        """Test a successful API request."""
        client, mock_get = mock_h1_client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "success"}
        mock_get.return_value = mock_response

        response = client._make_request("test_endpoint")
        assert response == {"data": "success"}
        mock_get.assert_called_once()

    def test_make_request_401_error(self, mock_h1_client):
        """Test handling of a 401 Unauthorized error."""
        client, mock_get = mock_h1_client
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_get.return_value = mock_response

        with pytest.raises(ConnectionRefusedError, match="HackerOne API authentication failed"):
            client._make_request("test_endpoint")

    def test_make_request_404_error(self, mock_h1_client):
        """Test handling of a 404 Not Found error."""
        client, mock_get = mock_h1_client
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_get.return_value = mock_response

        with pytest.raises(FileNotFoundError, match="Resource not found"):
            client._make_request("test_endpoint")

    def test_make_request_timeout(self, mock_h1_client):
        """Test handling of a request timeout."""
        client, mock_get = mock_h1_client
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")

        with pytest.raises(TimeoutError, match="timed out"):
            client._make_request("test_endpoint")

    def test_search_programs_pagination(self, mock_h1_client):
        """Test that program search handles pagination correctly."""
        client, mock_get = mock_h1_client

        # Mock first page response
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {
            "data": [{"id": 1}, {"id": 2}],
            "links": {"next": "https://api.hackerone.com/v1/programs?page[number]=2"}
        }

        # Mock second page response
        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {"data": [{"id": 3}]} # No 'next' link

        mock_get.side_effect = [mock_response1, mock_response2]

        programs = client.search_programs("test", max_pages=2)
        assert len(programs) == 3
        assert programs[2]['id'] == 3
        assert mock_get.call_count == 2

    def test_get_program(self, mock_h1_client):
        """Test fetching a single program."""
        client, mock_get = mock_h1_client
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": {"attributes": {"handle": "test_program"}}}
        mock_get.return_value = mock_response

        program = client.get_program("test_program")
        assert program["data"]["attributes"]["handle"] == "test_program"
        mock_get.assert_called_with(
            f"{client.BASE_URL}/programs/test_program",
            auth=client.auth,
            params=None,
            timeout=client.timeout,
            headers=client.headers
        )

    def test_format_program_details(self):
        """Test the static method for formatting program details."""
        program_data = {
            "data": {
                "attributes": {
                    "name": "Test Program",
                    "handle": "testprog",
                    "url": "https://hackerone.com/testprog",
                    "offers_bounties": True,
                    "structured_scopes": {
                        "data": [{
                            "attributes": {
                                "asset_type": "URL",
                                "asset_identifier": "example.com",
                                "eligible_for_bounty": True
                            }
                        }]
                    },
                    "targets_out_of_scope": "No admin panels."
                }
            }
        }
        formatted = HackerOneAPI.format_program_details(program_data)
        assert "Name: Test Program" in formatted
        assert "Handle: testprog" in formatted
        assert "URL: example.com (Bounty Eligible)" in formatted
        assert "Out-of-Scope" in formatted
        assert "No admin panels" in formatted

    def test_export_program_for_analysis(self):
        """Test the method for exporting program details for AI analysis."""
        program_data = {
            "data": {
                "attributes": {
                    "name": "Test Program",
                    "handle": "testprog",
                    "policy": "Be responsible.",
                    "structured_scopes": {
                        "data": [{
                            "attributes": {
                                "asset_type": "URL",
                                "asset_identifier": "test.com",
                                "eligible_for_bounty": False
                            }
                        }]
                    },
                    "targets_out_of_scope": "staging.test.com"
                }
            }
        }
        exported = HackerOneAPI.export_program_for_analysis(program_data)
        assert "BUG BOUNTY PROGRAM DETAILS" in exported
        assert "Program Name: Test Program" in exported
        assert "IN SCOPE TARGETS:" in exported
        assert "Identifier: test.com" in exported
        assert "OUT OF SCOPE:" in exported
        assert "staging.test.com" in exported
        assert "POLICY & RULES:" in exported
        assert "Be responsible." in exported
