#!/usr/bin/env python3
"""
HackerOne API Integration
Fetches bug bounty program details from HackerOne
"""
import os
import requests
import json
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

class Colors:
    """ANSI color codes for terminal output"""
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class HackerOneError(Exception):
    """Base exception for HackerOne API client errors."""
    pass

class HackerOneAPIError(HackerOneError):
    """Raised for API errors (e.g., 4xx, 5xx response)."""
    pass

class HackerOneAuthenticationError(HackerOneAPIError):
    """Raised for authentication failures (401)."""
    pass

class HackerOneRequestError(HackerOneError):
    """Raised for network or request-related errors."""
    pass

class HackerOneAPI:
    """
    Client for interacting with the HackerOne API

    Authentication:
    - You need a HackerOne API token (username and token)
    - Get it from: https://hackerone.com/settings/api_token/edit
    """

    BASE_URL = "https://api.hackerone.com/v1"

    def __init__(self, username: str, api_token: str, timeout: int = 30):
        if not username or not api_token:
            raise ValueError("HackerOne username and API token are required")

        self.auth = (username, api_token)
        self.timeout = timeout
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Dict:
        """Make authenticated request to HackerOne API"""
        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                auth=self.auth,
                headers=self.headers,
                params=params,
                json=data,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise HackerOneAuthenticationError("Authentication failed. Check your HackerOne credentials.")
            elif e.response.status_code == 404:
                raise HackerOneAPIError(f"Resource not found: {endpoint}")
            else:
                raise HackerOneAPIError(f"API Error ({e.response.status_code}): {e.response.text}")
        except requests.exceptions.Timeout:
            raise HackerOneRequestError(f"Request timed out after {self.timeout}s")
        except requests.exceptions.RequestException as e:
            raise HackerOneRequestError(f"Request failed: {str(e)}")

    def list_programs(self, page_size: int = 100) -> List[Dict]:
        """
        List available bug bounty programs

        Args:
            page_size: Number of programs per page (default: 100)

        Returns:
            List of program dictionaries
        """
        programs = []
        page = 1

        while True:
            params = {
                "page[size]": page_size,
                "page[number]": page
            }

            print(f"{Colors.YELLOW}[*] Fetching page {page}...{Colors.ENDC}")
            result = self._make_request("GET", "hackers/programs", params=params)

            data = result.get("data", [])
            if not data:
                break

            programs.extend(data)

            # Check if there are more pages
            links = result.get("links", {})
            if not links.get("next"):
                break

            page += 1

        print(f"{Colors.GREEN}[✓] Found {len(programs)} programs{Colors.ENDC}")
        return programs

    def get_program(self, program_handle: str) -> Dict:
        """
        Get detailed information about a specific program

        Args:
            program_handle: The program's handle (e.g., "security")

        Returns:
            Program details dictionary
        """
        response = self._make_request("GET", f"hackers/programs/{program_handle}")
        # The program data could be under the 'data' key or be the response itself
        if 'data' in response and response['data']:
            return response['data']
        # If 'data' is not there or is empty, return the whole response
        # It might be the program object itself, or an empty dict to signal failure
        return response

    def search_programs(self, query: str, programs: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Search for programs by name or handle

        Args:
            query: Search query string
            programs: Optional pre-fetched list of programs

        Returns:
            List of matching programs
        """
        if programs is None:
            programs = self.list_programs()

        query_lower = query.lower()
        matches = []

        for program in programs:
            attrs = program.get("attributes", {})
            handle = attrs.get("handle", "").lower()
            name = attrs.get("name", "").lower()

            if query_lower in handle or query_lower in name:
                matches.append(program)

        return matches

    def format_program_details(self, program: Dict) -> str:
        """
        Format program details in a readable way

        Args:
            program: Program dictionary from API

        Returns:
            Formatted string with program details
        """
        # The program data could be under an 'attributes' key, or the dict itself could be the attributes
        if 'attributes' in program:
            attrs = program.get("attributes", {})
        else:
            attrs = program

        # Basic info
        name = attrs.get("name", "N/A")
        handle = attrs.get("handle", "N/A")
        url = attrs.get("url", f"https://hackerone.com/{handle}")
        state = attrs.get("state", "N/A")

        # Scope information
        submission_state = attrs.get("submission_state", "N/A")
        offers_bounties = attrs.get("offers_bounties", False)
        offers_swag = attrs.get("offers_swag", False)

        # Stats
        resolved_report_count = attrs.get("resolved_report_count", 0)
        currency = attrs.get("currency", "USD")

        # Build formatted output
        output = f"""
{Colors.CYAN}╔{'═' * 78}╗
║{Colors.BOLD} PROGRAM DETAILS {Colors.ENDC}{Colors.CYAN}{'═' * 61}║
╚{'═' * 78}╝{Colors.ENDC}

{Colors.GREEN}Program Name:{Colors.ENDC} {name}
{Colors.GREEN}Handle:{Colors.ENDC} {handle}
{Colors.GREEN}URL:{Colors.ENDC} {url}
{Colors.GREEN}State:{Colors.ENDC} {state}
{Colors.GREEN}Submission State:{Colors.ENDC} {submission_state}
{Colors.GREEN}Offers Bounties:{Colors.ENDC} {'Yes' if offers_bounties else 'No'}
{Colors.GREEN}Offers Swag:{Colors.ENDC} {'Yes' if offers_swag else 'No'}
{Colors.GREEN}Resolved Reports:{Colors.ENDC} {resolved_report_count}
{Colors.GREEN}Currency:{Colors.ENDC} {currency}
"""

        # Scope details
        structured_scopes = attrs.get("structured_scopes", {}).get("data", [])
        if structured_scopes:
            output += f"\n{Colors.CYAN}{'─' * 80}{Colors.ENDC}\n"
            output += f"{Colors.BOLD}IN SCOPE ASSETS:{Colors.ENDC}\n\n"

            for idx, scope in enumerate(structured_scopes, 1):
                scope_attrs = scope.get("attributes", {})
                asset_type = scope_attrs.get("asset_type", "N/A")
                asset_identifier = scope_attrs.get("asset_identifier", "N/A")
                eligible_for_bounty = scope_attrs.get("eligible_for_bounty", False)
                eligible_for_submission = scope_attrs.get("eligible_for_submission", True)

                bounty_icon = "💰" if eligible_for_bounty else "🏆"
                status_icon = "✓" if eligible_for_submission else "✗"

                output += f"{status_icon} {Colors.GREEN}{idx}. [{asset_type}]{Colors.ENDC} {asset_identifier} {bounty_icon}\n"

        # Out of scope
        targets_out_of_scope = attrs.get("targets_out_of_scope", "")
        if targets_out_of_scope:
            output += f"\n{Colors.CYAN}{'─' * 80}{Colors.ENDC}\n"
            output += f"{Colors.BOLD}OUT OF SCOPE:{Colors.ENDC}\n\n"
            output += f"{targets_out_of_scope}\n"

        # Rules
        policy = attrs.get("policy", "")
        if policy:
            output += f"\n{Colors.CYAN}{'─' * 80}{Colors.ENDC}\n"
            output += f"{Colors.BOLD}POLICY & RULES:{Colors.ENDC}\n\n"
            # Truncate if too long
            if len(policy) > 1000:
                output += f"{policy[:1000]}...\n{Colors.YELLOW}[Policy truncated. See full policy at {url}]{Colors.ENDC}\n"
            else:
                output += f"{policy}\n"

        output += f"\n{Colors.CYAN}{'═' * 80}{Colors.ENDC}\n"
        return output

    def export_program_for_analysis(self, program: Dict) -> str:
        """
        Export program details in a format suitable for AI analysis

        Args:
            program: Program dictionary from API

        Returns:
            Formatted text for AI analysis
        """
        # The program data could be under an 'attributes' key, or the dict itself could be the attributes
        if 'attributes' in program:
            attrs = program.get("attributes", {})
        else:
            attrs = program

        # Build analysis-friendly format
        output = f"""BUG BOUNTY PROGRAM DETAILS

Program: {attrs.get('name', 'N/A')}
Handle: {attrs.get('handle', 'N/A')}
URL: {attrs.get('url', 'N/A')}
State: {attrs.get('state', 'N/A')}
Accepts Submissions: {attrs.get('submission_state', 'N/A')}
Offers Bounties: {'Yes' if attrs.get('offers_bounties', False) else 'No'}

=== IN SCOPE TARGETS ===
"""

        # Add scopes
        structured_scopes = attrs.get("structured_scopes", {}).get("data", [])
        if structured_scopes:
            for scope in structured_scopes:
                scope_attrs = scope.get("attributes", {})
                asset_type = scope_attrs.get("asset_type", "unknown")
                asset_identifier = scope_attrs.get("asset_identifier", "N/A")
                bounty_eligible = "Yes" if scope_attrs.get("eligible_for_bounty", False) else "No"

                output += f"- [{asset_type}] {asset_identifier} (Bounty Eligible: {bounty_eligible})\n"
        else:
            output += "No structured scope information available.\n"

        # Out of scope
        targets_out_of_scope = attrs.get("targets_out_of_scope", "")
        if targets_out_of_scope:
            output += f"\n=== OUT OF SCOPE ===\n{targets_out_of_scope}\n"

        # Policy
        policy = attrs.get("policy", "")
        if policy:
            output += f"\n=== POLICY & RULES ===\n{policy}\n"

        return output


def main():
    """Example usage of HackerOne API"""
    load_dotenv()

    username = os.getenv("HACKERONE_USERNAME")
    api_token = os.getenv("HACKERONE_API_TOKEN")

    if not username or not api_token:
        print(f"{Colors.RED}[!] Error: HackerOne credentials not found in environment{Colors.ENDC}")
        print(f"\n{Colors.YELLOW}To use this script:{Colors.ENDC}")
        print(f"1. Get API credentials from: {Colors.CYAN}https://hackerone.com/settings/api_token/edit{Colors.ENDC}")
        print(f"2. Add to your .env file:")
        print(f"   {Colors.GREEN}HACKERONE_USERNAME=your_username{Colors.ENDC}")
        print(f"   {Colors.GREEN}HACKERONE_API_TOKEN=your_token{Colors.ENDC}")
        return

    try:
        client = HackerOneAPI(username, api_token)

        # Interactive menu
        while True:
            print(f"\n{Colors.CYAN}╔{'═' * 58}╗")
            print(f"║{Colors.BOLD}{'HACKERONE API CLIENT'.center(58)}{Colors.ENDC}{Colors.CYAN}║")
            print(f"╠{'═' * 58}╣")
            print(f"║  {Colors.GREEN}[1]{Colors.ENDC} List All Programs".ljust(67) + "║")
            print(f"║  {Colors.GREEN}[2]{Colors.ENDC} Search Programs".ljust(67) + "║")
            print(f"║  {Colors.GREEN}[3]{Colors.ENDC} Get Program Details".ljust(67) + "║")
            print(f"║  {Colors.GREEN}[4]{Colors.ENDC} Export Program for Analysis".ljust(67) + "║")
            print(f"║  {Colors.RED}[q]{Colors.ENDC} Quit".ljust(67) + "║")
            print(f"╚{'═' * 58}╝{Colors.ENDC}\n")

            choice = input(f"{Colors.CYAN}[HackerOne] ▶{Colors.ENDC} ").strip().lower()

            if choice in ['q', 'quit', 'exit']:
                print(f"\n{Colors.YELLOW}👋 Goodbye!{Colors.ENDC}\n")
                break

            elif choice == '1':
                programs = client.list_programs()
                print(f"\n{Colors.CYAN}{'═' * 80}{Colors.ENDC}")
                print(f"{Colors.BOLD}AVAILABLE PROGRAMS:{Colors.ENDC}\n")
                for idx, program in enumerate(programs[:20], 1):  # Show first 20
                    attrs = program.get("attributes", {})
                    name = attrs.get("name", "N/A")
                    handle = attrs.get("handle", "N/A")
                    bounties = "💰" if attrs.get("offers_bounties", False) else "🏆"
                    print(f"{idx:3d}. {bounties} {Colors.GREEN}{handle:30s}{Colors.ENDC} | {name}")

                if len(programs) > 20:
                    print(f"\n{Colors.YELLOW}... and {len(programs) - 20} more programs{Colors.ENDC}")

            elif choice == '2':
                query = input(f"{Colors.CYAN}Search query: {Colors.ENDC}").strip()
                if not query:
                    continue

                matches = client.search_programs(query)
                print(f"\n{Colors.GREEN}[✓] Found {len(matches)} matching programs{Colors.ENDC}\n")

                for idx, program in enumerate(matches, 1):
                    attrs = program.get("attributes", {})
                    name = attrs.get("name", "N/A")
                    handle = attrs.get("handle", "N/A")
                    bounties = "💰" if attrs.get("offers_bounties", False) else "🏆"
                    print(f"{idx}. {bounties} {Colors.GREEN}{handle}{Colors.ENDC} | {name}")

            elif choice == '3':
                handle = input(f"{Colors.CYAN}Program handle: {Colors.ENDC}").strip()
                if not handle:
                    continue

                try:
                    program = client.get_program(handle)
                    print(client.format_program_details(program))
                except HackerOneError as e:
                    print(f"{Colors.RED}[!] Error: {e}{Colors.ENDC}")

            elif choice == '4':
                handle = input(f"{Colors.CYAN}Program handle: {Colors.ENDC}").strip()
                if not handle:
                    continue

                try:
                    program = client.get_program(handle)
                    analysis_text = client.export_program_for_analysis(program)

                    # Save to file
                    filename = f"{handle}_bounty_details.txt"
                    with open(filename, 'w') as f:
                        f.write(analysis_text)

                    print(f"\n{Colors.GREEN}[✓] Program details exported to: {filename}{Colors.ENDC}")
                    print(f"{Colors.YELLOW}[i] You can now use this file with your AI analysis tools{Colors.ENDC}\n")
                    print(analysis_text)

                except HackerOneError as e:
                    print(f"{Colors.RED}[!] Error: {e}{Colors.ENDC}")

            else:
                print(f"{Colors.YELLOW}Unknown option: {choice}{Colors.ENDC}")

    except HackerOneError as e:
        print(f"{Colors.RED}[!] Error: {e}{Colors.ENDC}")


if __name__ == "__main__":
    main()
