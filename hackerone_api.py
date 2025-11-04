import requests
from typing import List, Dict, Any, Optional

class HackerOneAPI:
    """A client for the HackerOne API."""

    BASE_URL = "https://api.hackerone.com/v1"

    def __init__(self, username: str, token: str, timeout: int = 30):
        if not username or not token:
            raise ValueError("HackerOne username and token are required.")

        self.auth = (username, token)
        self.timeout = timeout
        self.headers = {"Accept": "application/json"}

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a GET request to the HackerOne API."""
        try:
            response = requests.get(
                f"{self.BASE_URL}/{endpoint}",
                auth=self.auth,
                params=params,
                timeout=self.timeout,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise ConnectionRefusedError("HackerOne API authentication failed. Check your credentials.") from e
            elif e.response.status_code == 404:
                raise FileNotFoundError(f"Resource not found: {endpoint}") from e
            else:
                raise ConnectionError(f"HTTP Error: {e}") from e
        except requests.exceptions.Timeout as e:
            raise TimeoutError(f"Request to {endpoint} timed out after {self.timeout} seconds.") from e
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"A connection error occurred: {e}") from e

    def search_programs(self, query: str, max_pages: int = 5) -> List[Dict[str, Any]]:
        """Search for programs."""
        programs = []
        params = {"filter[name]": query, "page[size]": 100} # Max page size

        endpoint = "programs"
        for page_num in range(1, max_pages + 1):
            params["page[number]"] = page_num
            data = self._make_request(endpoint, params=params)
            programs.extend(data.get("data", []))
            if "next" not in data.get("links", {}):
                break

        return programs

    def get_program(self, handle: str) -> Dict[str, Any]:
        """Get a specific program by its handle."""
        return self._make_request(f"programs/{handle}")

    @staticmethod
    def format_program_details(program: Dict[str, Any]) -> str:
        """Format program details for display."""
        attrs = program.get("data", {}).get("attributes", {})
        scopes = attrs.get("structured_scopes", {}).get("data", [])

        formatted = [
            f"Name: {attrs.get('name', 'N/A')}",
            f"Handle: {attrs.get('handle', 'N/A')}",
            f"URL: {attrs.get('url', 'N/A')}",
            f"Offers Bounties: {'Yes' if attrs.get('offers_bounties') else 'No'}",
            "\n--- In-Scope Targets ---"
        ]

        if not scopes:
            formatted.append("  No structured scopes available.")
        else:
            for scope in scopes[:5]: # Display first 5 scopes
                scope_attrs = scope.get("attributes", {})
                asset = f"{scope_attrs.get('asset_type')}: {scope_attrs.get('asset_identifier')}"
                bounty_info = " (Bounty Eligible)" if scope_attrs.get('eligible_for_bounty') else ""
                formatted.append(f"  - {asset}{bounty_info}")

        if len(scopes) > 5:
            formatted.append(f"  ...and {len(scopes) - 5} more.")

        formatted.append("\n--- Out-of-Scope ---")
        out_of_scope = attrs.get('targets_out_of_scope', 'N/A')
        formatted.append(f"  {out_of_scope}")

        return "\n".join(formatted)


    @staticmethod
    def export_program_for_analysis(program: Dict[str, Any]) -> str:
        """Export program details for AI analysis."""
        attrs = program.get("data", {}).get("attributes", {})
        scopes = attrs.get("structured_scopes", {}).get("data", [])

        in_scope_items = []
        for scope in scopes:
            scope_attrs = scope.get("attributes", {})
            in_scope_items.append(
                f"- Asset Type: {scope_attrs.get('asset_type')}, "
                f"Identifier: {scope_attrs.get('asset_identifier')}, "
                f"Bounty Eligible: {scope_attrs.get('eligible_for_bounty')}"
            )

        in_scope_str = "\n".join(in_scope_items) if in_scope_items else "Not specified."

        return f"""
BUG BOUNTY PROGRAM DETAILS
==========================

Program Name: {attrs.get('name', 'N/A')}
Program Handle: {attrs.get('handle', 'N/A')}

IN SCOPE TARGETS:
-----------------
{in_scope_str}

OUT OF SCOPE:
-------------
{attrs.get('targets_out_of_scope', 'Not specified.')}

POLICY & RULES:
---------------
{attrs.get('policy', 'Not specified.')}
"""
