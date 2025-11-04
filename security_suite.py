# main.py - Refactored for interaction and command execution
import os
import requests
import json
import subprocess  # For running shell commands
import shlex       # For safely splitting command strings
from typing import List, Dict, Optional, Generator, Any, Set
from dotenv import load_dotenv
import re  # For parsing tool requirements
import time  # For retry delays

# Optional HackerOne API integration
try:
    from hackerone_api import HackerOneAPI
    HACKERONE_AVAILABLE = True
except ImportError:
    HACKERONE_AVAILABLE = False

# --- Color Definitions ---
class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    MAGENTA = '\033[35m'
    WHITE = '\033[97m'
    BG_BLACK = '\033[40m'

def print_banner():
    """Display ASCII art banner"""
    banner = f"""{Colors.CYAN}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     ██████╗ ███████╗███████╗██████╗ ███████╗███████╗██╗  ██╗ ║
║     ██╔══██╗██╔════╝██╔════╝██╔══██╗██╔════╝██╔════╝██║ ██╔╝ ║
║     ██║  ██║█████╗  █████╗  ██████╔╝███████╗█████╗  █████╔╝  ║
║     ██║  ██║██╔══╝  ██╔══╝  ██╔═══╝ ╚════██║██╔══╝  ██╔═██╗  ║
║     ██████╔╝███████╗███████╗██║     ███████║███████╗██║  ██╗ ║
║     ╚═════╝ ╚══════╝╚══════╝╚═╝     ╚══════╝╚══════╝╚═╝  ╚═╝ ║
║                                                              ║
║           {Colors.WHITE}Security Research Suite v2.0{Colors.CYAN}                    ║
║        {Colors.YELLOW}Powered by DeepSeek AI{Colors.CYAN}  |  {Colors.GREEN}Enhanced Edition{Colors.CYAN}       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
{Colors.ENDC}"""
    print(banner)

def print_box(title: str, content: str, color: str = Colors.CYAN):
    """Print content in a colored box"""
    lines = content.split('\n')
    width = max(len(line) for line in lines) + 4

    print(f"{color}╔{'═' * width}╗")
    print(f"║{title.center(width)}║")
    print(f"╠{'═' * width}╣")
    for line in lines:
        print(f"║  {line.ljust(width-2)}║")
    print(f"╚{'═' * width}╝{Colors.ENDC}")

# --- Custom Exceptions ---
class DeepSeekError(Exception):
    """Base exception for DeepSeek client errors."""
    pass

class DeepSeekAPIError(DeepSeekError):
    """Raised for API errors (e.g., 4xx, 5xx response)."""
    pass

class DeepSeekRequestError(DeepSeekError):
    """Raised for network or request-related errors (e.g., timeout, connection error)."""
    pass

class DeepSeekResponseError(DeepSeekError):
    """Raised when the API response is malformed or unparseable."""
    pass

# --- Main Class ---
class DeepSeekSecuritySuite:
    """
    Manages direct API communication with DeepSeek for security tasks.
    This class is stateful and maintains a single conversation history.
    """
    
    API_URL = "https://api.deepseek.com/v1/chat/completions"

    def __init__(self, api_key: str, model: str = "deepseek-chat", temperature: float = 0.7, timeout: int = 120, max_retries: int = 3):
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY is required.")

        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
        self.max_retries = max_retries
        self.conversation_history: List[Dict[str, str]] = []

    def _handle_api_error(self, response: requests.Response) -> str:
        try:
            err_data = response.json()
            msg = err_data.get("error", {}).get("message", response.text)
            return f"API Error ({response.status_code}): {msg}"
        except json.JSONDecodeError:
            return f"API Error ({response.status_code}): {response.text}"

    def set_system_prompt(self, system_prompt: str):
        if self.conversation_history and self.conversation_history[0]['role'] == 'system':
            self.conversation_history[0]['content'] = system_prompt
        else:
            self.conversation_history.insert(0, {"role": "system", "content": system_prompt})

    def clear_history(self):
        self.conversation_history = []

    def call_deepseek(self, message: str, system_prompt: Optional[str] = None) -> str:
        if system_prompt:
            self.set_system_prompt(system_prompt)

        current_user_message = {"role": "user", "content": message}
        messages_payload = self.conversation_history + [current_user_message]

        payload = {
            "model": self.model,
            "messages": messages_payload,
            "temperature": self.temperature,
            "stream": False
        }

        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = requests.post(self.API_URL, headers=self.headers, json=payload, timeout=self.timeout)
                response.raise_for_status()

                result = response.json()
                assistant_message = result.get('choices', [{}])[0].get('message', {}).get('content')

                if assistant_message is None:
                    raise DeepSeekResponseError(f"API response missing 'content': {result}")

                self.conversation_history.append(current_user_message)
                self.conversation_history.append({"role": "assistant", "content": assistant_message})

                return assistant_message

            except requests.exceptions.HTTPError as http_err:
                # Don't retry on 4xx client errors (except 429 rate limit)
                if http_err.response.status_code < 500 and http_err.response.status_code != 429:
                    raise DeepSeekAPIError(self._handle_api_error(http_err.response)) from http_err
                last_exception = http_err

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as conn_err:
                # Retry on timeout and connection errors
                last_exception = conn_err

            except requests.exceptions.RequestException as req_err:
                # Other request errors - don't retry
                raise DeepSeekRequestError(f"API Request Error: {req_err}") from req_err

            except (KeyError, IndexError, json.JSONDecodeError) as parse_err:
                raise DeepSeekResponseError(f"API Response Parse Error: {parse_err}") from parse_err

            except Exception as e:
                raise DeepSeekError(f"An unexpected error occurred: {str(e)}") from e

            # If we get here, we need to retry
            if attempt < self.max_retries - 1:
                wait_time = (2 ** attempt) + 1  # Exponential backoff: 2, 5, 9 seconds
                print(f"{Colors.YELLOW}[!] Request failed (attempt {attempt + 1}/{self.max_retries}). Retrying in {wait_time}s...{Colors.ENDC}")
                time.sleep(wait_time)

        # All retries exhausted
        if isinstance(last_exception, requests.exceptions.Timeout):
            raise DeepSeekRequestError(
                f"API Request Timeout after {self.max_retries} attempts. "
                f"The API took longer than {self.timeout}s to respond. "
                f"Try increasing the timeout or check your network connection."
            ) from last_exception
        elif isinstance(last_exception, requests.exceptions.ConnectionError):
            raise DeepSeekRequestError(
                f"API Connection Error after {self.max_retries} attempts: {last_exception}. "
                f"Check your internet connection and try again."
            ) from last_exception
        elif isinstance(last_exception, requests.exceptions.HTTPError):
            raise DeepSeekAPIError(self._handle_api_error(last_exception.response)) from last_exception
        else:
            raise DeepSeekRequestError(f"API Request failed after {self.max_retries} attempts: {last_exception}") from last_exception

    def stream_call_deepseek(self, message: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        if system_prompt:
            self.set_system_prompt(system_prompt)

        current_user_message = {"role": "user", "content": message}
        messages_payload = self.conversation_history + [current_user_message]

        payload = {
            "model": self.model,
            "messages": messages_payload,
            "temperature": self.temperature,
            "stream": True
        }

        full_response_content = []
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                # Use longer timeout for streaming (3x base timeout)
                stream_timeout = self.timeout * 3
                with requests.post(self.API_URL, headers=self.headers, json=payload, timeout=stream_timeout, stream=True) as response:
                    response.raise_for_status()
                    for line in response.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8')
                            if decoded_line.startswith('data: '):
                                json_data = decoded_line[6:]
                                if json_data.strip() == '[DONE]':
                                    break
                                try:
                                    chunk = json.loads(json_data)
                                    content = chunk.get('choices', [{}])[0].get('delta', {}).get('content')
                                    if content:
                                        full_response_content.append(content)
                                        yield content
                                except json.JSONDecodeError as json_err:
                                    raise DeepSeekResponseError(f"Stream Error: Invalid JSON chunk: {json_data}") from json_err

                assistant_message = "".join(full_response_content)
                if assistant_message:
                    self.conversation_history.append(current_user_message)
                    self.conversation_history.append({"role": "assistant", "content": assistant_message})

                return  # Success, exit retry loop

            except requests.exceptions.HTTPError as http_err:
                # Don't retry on 4xx client errors (except 429 rate limit)
                if http_err.response.status_code < 500 and http_err.response.status_code != 429:
                    raise DeepSeekAPIError(self._handle_api_error(http_err.response)) from http_err
                last_exception = http_err

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as conn_err:
                # Retry on timeout and connection errors
                last_exception = conn_err

            except requests.exceptions.RequestException as req_err:
                # Other request errors - don't retry
                raise DeepSeekRequestError(f"API Request Error: {req_err}") from req_err

            except Exception as e:
                raise DeepSeekError(f"An unexpected streaming error occurred: {str(e)}") from e

            # If we get here, we need to retry
            if attempt < self.max_retries - 1:
                wait_time = (2 ** attempt) + 1  # Exponential backoff: 2, 5, 9 seconds
                yield f"\n{Colors.YELLOW}[!] Stream failed (attempt {attempt + 1}/{self.max_retries}). Retrying in {wait_time}s...{Colors.ENDC}\n"
                time.sleep(wait_time)
                full_response_content = []  # Reset for retry

        # All retries exhausted
        if isinstance(last_exception, requests.exceptions.Timeout):
            raise DeepSeekRequestError(
                f"API Stream Timeout after {self.max_retries} attempts. "
                f"The API took longer than {stream_timeout}s to respond. "
                f"Try increasing the timeout or check your network connection."
            ) from last_exception
        elif isinstance(last_exception, requests.exceptions.ConnectionError):
            raise DeepSeekRequestError(
                f"API Connection Error after {self.max_retries} attempts: {last_exception}. "
                f"Check your internet connection and try again."
            ) from last_exception
        elif isinstance(last_exception, requests.exceptions.HTTPError):
            raise DeepSeekAPIError(self._handle_api_error(last_exception.response)) from last_exception
        else:
            raise DeepSeekRequestError(f"API Stream failed after {self.max_retries} attempts: {last_exception}") from last_exception

    def analyze_bounty(self, bounty_text: str) -> str:
        system_prompt = """You are a security research assistant. Analyze the provided bounty program text and extract the following in a structured JSON format:
- in_scope_targets (list of strings)
- out_of_scope_items (list of strings)
- rules_and_restrictions (list of strings)
- reward_information (string)
- testing_guidelines (list of strings)
Respond ONLY with the JSON object."""
        
        return self.call_deepseek(f"Analyze this bounty program:\n{bounty_text}", system_prompt)
    
    def generate_commands(self, target: str, available_tools: Optional[Set[str]] = None) -> str:
        # Build a list of available tools for the AI
        tools_info = ""
        if available_tools:
            tools_info = f"\n\nIMPORTANT: Only suggest commands using these available tools: {', '.join(sorted(available_tools))}"

        # Provide correct wordlist paths
        wordlist_paths = """
Common wordlist paths in this environment (use absolute paths with $HOME):
- $HOME/data/wordlists/web/common.txt
- $HOME/data/wordlists/dns/subdomains-top1million-5000.txt
- $HOME/data/wordlists/web/directory-list-2.3-medium.txt
- $HOME/data/wordlists/web/raft-medium-directories.txt
- $HOME/data/wordlists/dns/dns-jhaddix.txt
- $HOME/data/wordlists/api/api-endpoints.txt

For gobuster: Use --domain (not -d) for DNS enumeration
Example: gobuster dns --domain example.com -w $HOME/data/wordlists/dns/subdomains-top1million-5000.txt

For nuclei: Templates are in $HOME/nuclei-templates/
Example: nuclei -u example.com -t $HOME/nuclei-templates/

For nmap: Do NOT use -O (OS detection) as it requires root. Use -sV -sC for service/script scanning.
Avoid 'nmap -p- --min-rate 10000' as it times out. Use targeted port scans instead."""

        system_prompt = f"""You are a penetration testing expert. Suggest relevant security testing commands for the target.
Use the conversation history for context (e.g., previous bounty analysis).
Provide only the shell commands, each on a new line, without explanation or markdown.{tools_info}

{wordlist_paths}

Do not suggest overly aggressive scans or commands that may timeout (like nmap -p- with --min-rate 10000).
Prefer targeted, efficient commands."""

        return self.call_deepseek(f"Suggest security testing commands for: {target}", system_prompt)

# --- Tool Management Functions ---

def check_tool_available(tool_name: str) -> bool:
    """Check if a tool is available in the system PATH."""
    try:
        result = subprocess.run(['which', tool_name], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except:
        return False

def get_available_tools() -> Set[str]:
    """Get a set of all available security tools."""
    common_tools = [
        'nmap', 'subfinder', 'httpx', 'nuclei', 'ffuf', 'gobuster',
        'amass', 'waybackurls', 'sqlmap', 'whatweb', 'nikto', 'dirb',
        'wpscan', 'arjun', 'xsstrike', 'commix', 'wfuzz', 'curl',
        'testssl.sh', 'sslscan'
    ]
    return {tool for tool in common_tools if check_tool_available(tool)}

def extract_tool_from_command(command: str) -> str:
    """Extract the tool name from a command string."""
    parts = command.strip().split()
    if not parts:
        return ""

    tool = parts[0]
    # Handle paths like ~/tools/testssl.sh/testssl.sh
    if '/' in tool:
        tool = tool.split('/')[-1]
    # Remove file extensions
    tool = tool.replace('.sh', '').replace('.py', '')
    return tool

def filter_commands_by_availability(commands: str, available_tools: Set[str]) -> tuple[List[str], List[str]]:
    """
    Filter commands based on tool availability.
    Returns: (available_commands, unavailable_commands)
    """
    available = []
    unavailable = []

    for cmd in commands.split('\n'):
        cmd = cmd.strip()
        if not cmd or cmd.startswith('#'):
            continue

        tool = extract_tool_from_command(cmd)
        if tool in available_tools:
            available.append(cmd)
        else:
            unavailable.append(cmd)

    return available, unavailable

# --- New Interactive Functions ---

def get_multiline_input(prompt: str) -> str:
    """Helper function to get multiline input from the user."""
    print(prompt + " (Type 'END' on a new line when finished):")
    lines = []
    while True:
        try:
            line = input()
            if line.strip().upper() == 'END':
                break
            lines.append(line)
        except EOFError:
            break
    return "\n".join(lines)

def run_generated_commands(command_string: str, check_availability: bool = True, default_timeout: int = 120):
    """
    Parses a string of commands (one per line) and asks the user to
    confirm execution for each.

    Args:
        command_string: Commands to execute (one per line)
        check_availability: Whether to check if tools are available
        default_timeout: Default timeout in seconds for command execution
    """
    if not command_string.strip():
        print("[Info] No commands were generated.")
        return

    print("\n--- Generated Commands ---")
    commands = [cmd.strip() for cmd in command_string.split('\n') if cmd.strip() and not cmd.startswith('#')]

    if not commands:
        print("[Info] No executable commands found in response.")
        return

    # Check tool availability
    if check_availability:
        print(f"{Colors.YELLOW}[*] Checking tool availability...{Colors.ENDC}")
        available_tools = get_available_tools()
        available_cmds, unavailable_cmds = filter_commands_by_availability(command_string, available_tools)

        if unavailable_cmds:
            print(f"\n{Colors.YELLOW}⚠️  Warning: {len(unavailable_cmds)} command(s) use unavailable tools:{Colors.ENDC}")
            for cmd in unavailable_cmds[:5]:  # Show first 5
                tool = extract_tool_from_command(cmd)
                print(f"  {Colors.RED}✗{Colors.ENDC} {tool}: {cmd[:60]}...")
            if len(unavailable_cmds) > 5:
                print(f"  {Colors.YELLOW}... and {len(unavailable_cmds) - 5} more{Colors.ENDC}")
            print(f"\n{Colors.CYAN}💡 Tip: Run './setup-security-tools.sh' to install missing tools{Colors.ENDC}")

        commands = available_cmds if available_cmds else commands

    print(f"\n{Colors.GREEN}╔{'═' * 60}╗")
    print(f"║{Colors.BOLD}{'GENERATED COMMANDS'.center(60)}{Colors.ENDC}{Colors.GREEN}║")
    print(f"╚{'═' * 60}╝{Colors.ENDC}\n")

    for i, cmd in enumerate(commands, 1):
        print(f"  {Colors.CYAN}{i:2d}.{Colors.ENDC} {cmd}")

    print(f"\n{Colors.GREEN}{'─' * 60}{Colors.ENDC}")
    
    try:
        choice = input("Do you want to run these commands? (all/one/N) [N]: ").strip().lower()
        if choice not in ['all', 'one']:
            print("Commands skipped.")
            return

        for cmd in commands:
            if choice == 'one':
                confirm = input(f"Run: {cmd}? [y/N]: ").strip().lower()
                if confirm != 'y':
                    print("Command skipped.")
                    continue
            
            print(f"\n{Colors.YELLOW}{'─' * 60}")
            print(f"▶️  Executing: {Colors.CYAN}{cmd}{Colors.ENDC}")
            print(f"{'─' * 60}{Colors.ENDC}")

            # Determine timeout based on command
            timeout = default_timeout
            if 'nmap -p-' in cmd or '--script vuln' in cmd:
                timeout = 300  # 5 minutes for full scans
                print(f"{Colors.YELLOW}⏱️  Extended timeout: {timeout}s (full scan){Colors.ENDC}")
            elif 'waybackurls' in cmd or 'gau ' in cmd:
                timeout = 240  # 4 minutes for wayback/archive fetching
                print(f"{Colors.YELLOW}⏱️  Extended timeout: {timeout}s (archive fetching){Colors.ENDC}")
            elif 'nuclei' in cmd:
                timeout = 180  # 3 minutes for nuclei
                print(f"{Colors.YELLOW}⏱️  Extended timeout: {timeout}s (nuclei scan){Colors.ENDC}")
            elif 'amass' in cmd:
                timeout = 240  # 4 minutes for amass subdomain enumeration
                print(f"{Colors.YELLOW}⏱️  Extended timeout: {timeout}s (amass enum){Colors.ENDC}")
            elif 'nmap' in cmd:
                timeout = 120  # 2 minutes for regular nmap
                print(f"{Colors.YELLOW}⏱️  Timeout: {timeout}s{Colors.ENDC}")
            elif 'ffuf' in cmd or 'gobuster dir' in cmd:
                timeout = 180  # 3 minutes for directory fuzzing
                print(f"{Colors.YELLOW}⏱️  Extended timeout: {timeout}s (fuzzing){Colors.ENDC}")

            try:
                # Use shlex.split to handle quotes and arguments safely
                # Handle pipes and redirects by using shell=True for complex commands
                if '|' in cmd or '>' in cmd or '<' in cmd:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
                else:
                    args = shlex.split(cmd)
                    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)

                if result.stdout:
                    print(f"\n{Colors.GREEN}[stdout]{Colors.ENDC}")
                    print(result.stdout)
                if result.stderr:
                    print(f"\n{Colors.YELLOW}[stderr]{Colors.ENDC}")
                    print(result.stderr)

                status_color = Colors.GREEN if result.returncode == 0 else Colors.RED
                print(f"\n{status_color}[Exit Code: {result.returncode}]{Colors.ENDC}")

            except FileNotFoundError as e:
                tool = extract_tool_from_command(cmd)
                print(f"\n{Colors.RED}[✗] Command not found: {tool}{Colors.ENDC}")
                print(f"{Colors.CYAN}💡 Tip: Install it with: pip install {tool} or go install {tool}@latest{Colors.ENDC}")
            except subprocess.TimeoutExpired:
                print(f"\n{Colors.RED}[✗] Command timed out after {timeout}s.{Colors.ENDC}")
                print(f"{Colors.CYAN}💡 Tip: Use a more targeted scan or increase timeout{Colors.ENDC}")
            except Exception as e:
                print(f"\n{Colors.RED}[✗] Failed to execute command: {e}{Colors.ENDC}")
                
            if choice == 'one':
                more = input("Run next command? (y/N) [y]: ").strip().lower()
                if more == 'n':
                    break
        
    except KeyboardInterrupt:
        print("\nCommand execution cancelled.")


def show_tool_status():
    """Display available and missing tools."""
    print(f"\n{Colors.CYAN}{'═' * 60}")
    print(f"║{Colors.BOLD}{'TOOL STATUS'.center(58)}{Colors.ENDC}{Colors.CYAN}║")
    print(f"{'═' * 60}{Colors.ENDC}\n")

    available_tools = get_available_tools()

    all_tools = [
        'nmap', 'subfinder', 'httpx', 'nuclei', 'ffuf', 'gobuster',
        'amass', 'waybackurls', 'sqlmap', 'whatweb', 'nikto', 'dirb',
        'wpscan', 'arjun', 'xsstrike', 'commix', 'wfuzz', 'curl',
        'testssl.sh', 'sslscan'
    ]

    print(f"{Colors.GREEN}✓ Available Tools ({len(available_tools)}):{Colors.ENDC}")
    cols = 3
    available_list = sorted(available_tools)
    for i in range(0, len(available_list), cols):
        row = available_list[i:i+cols]
        print("  " + "  ".join(f"{Colors.GREEN}✓{Colors.ENDC} {tool:15s}" for tool in row))

    missing = set(all_tools) - available_tools
    if missing:
        print(f"\n{Colors.RED}✗ Missing Tools ({len(missing)}):{Colors.ENDC}")
        missing_list = sorted(missing)
        for i in range(0, len(missing_list), cols):
            row = missing_list[i:i+cols]
            print("  " + "  ".join(f"{Colors.RED}✗{Colors.ENDC} {tool:15s}" for tool in row))
        print(f"\n{Colors.YELLOW}💡 Tip:{Colors.ENDC} Run {Colors.CYAN}'./setup-security-tools.sh'{Colors.ENDC} to install missing tools")

    print(f"\n{Colors.CYAN}{'═' * 60}{Colors.ENDC}\n")

def main_interactive_loop(suite: DeepSeekSecuritySuite):
    """Runs the main interactive REPL for the security suite."""
    print_banner()
    print(f"{Colors.YELLOW}Type {Colors.CYAN}'menu'{Colors.YELLOW} for options or {Colors.RED}'quit'{Colors.YELLOW} to exit.{Colors.ENDC}\n")

    while True:
        try:
            choice = input(f"{Colors.CYAN}[{Colors.GREEN}Main{Colors.CYAN}] ▶{Colors.ENDC} ").strip().lower()

            if choice in ['q', 'quit', 'exit']:
                print(f"\n{Colors.YELLOW}👋 Thanks for using DeepSeek Security Suite!{Colors.ENDC}\n")
                break

            elif choice in ['m', 'menu', 'h', 'help']:
                print(f"\n{Colors.CYAN}╔{'═' * 58}╗")
                print(f"║{Colors.BOLD}{'MAIN MENU'.center(58)}{Colors.ENDC}{Colors.CYAN}║")
                print(f"╠{'═' * 58}╣")
                if HACKERONE_AVAILABLE:
                    print(f"║  {Colors.GREEN}[0]{Colors.ENDC} Fetch Program from HackerOne {Colors.YELLOW}(auto-analyze){Colors.CYAN}".ljust(75) + "║")
                print(f"║  {Colors.GREEN}[1]{Colors.ENDC} Analyze Bounty {Colors.YELLOW}(provides context){Colors.CYAN}".ljust(75) + "║")
                print(f"║  {Colors.GREEN}[2]{Colors.ENDC} Generate Commands {Colors.YELLOW}(uses context){Colors.CYAN}".ljust(75) + "║")
                print(f"║  {Colors.GREEN}[3]{Colors.ENDC} Run Commands for Target {Colors.YELLOW}(clears context){Colors.CYAN}".ljust(75) + "║")
                print(f"║  {Colors.GREEN}[4]{Colors.ENDC} Stream Free-form Chat".ljust(67) + "║")
                print(f"║  {Colors.GREEN}[5]{Colors.ENDC} Clear Conversation History".ljust(67) + "║")
                print(f"║  {Colors.GREEN}[6]{Colors.ENDC} Show Tool Status".ljust(67) + "║")
                print(f"║  {Colors.RED}[q]{Colors.ENDC} Quit".ljust(67) + "║")
                print(f"╚{'═' * 58}╝{Colors.ENDC}\n")
                continue

            elif choice == '0':
                # Fetch from HackerOne
                if not HACKERONE_AVAILABLE:
                    print(f"{Colors.RED}[!] HackerOne API not available. Make sure hackerone_api.py is in the same directory.{Colors.ENDC}")
                    continue

                h1_username = os.getenv("HACKERONE_USERNAME")
                h1_token = os.getenv("HACKERONE_API_TOKEN")

                if not h1_username or not h1_token:
                    print(f"{Colors.RED}[!] HackerOne credentials not found{Colors.ENDC}")
                    print(f"\n{Colors.YELLOW}Setup instructions:{Colors.ENDC}")
                    print(f"1. Get API credentials: {Colors.CYAN}https://hackerone.com/settings/api_token/edit{Colors.ENDC}")
                    print(f"2. Add to .env file:")
                    print(f"   {Colors.GREEN}HACKERONE_USERNAME=your_username{Colors.ENDC}")
                    print(f"   {Colors.GREEN}HACKERONE_API_TOKEN=your_token{Colors.ENDC}")
                    continue

                try:
                    h1_client = HackerOneAPI(h1_username, h1_token)

                    # Ask user to search or provide handle
                    print(f"\n{Colors.CYAN}╔{'═' * 58}╗")
                    print(f"║{Colors.BOLD}{'HACKERONE PROGRAM FETCH'.center(58)}{Colors.ENDC}{Colors.CYAN}║")
                    print(f"╚{'═' * 58}╝{Colors.ENDC}\n")

                    search_choice = input(f"{Colors.CYAN}[1] Search programs [2] Enter handle directly: {Colors.ENDC}").strip()

                    program_handle = None
                    if search_choice == '1':
                        query = input(f"{Colors.CYAN}Search query: {Colors.ENDC}").strip()
                        if query:
                            print(f"{Colors.YELLOW}[*] Searching programs...{Colors.ENDC}")
                            matches = h1_client.search_programs(query)

                            if not matches:
                                print(f"{Colors.RED}[!] No programs found{Colors.ENDC}")
                                continue

                            print(f"\n{Colors.GREEN}[✓] Found {len(matches)} programs:{Colors.ENDC}\n")
                            for idx, prog in enumerate(matches[:10], 1):
                                attrs = prog.get("attributes", {})
                                handle = attrs.get("handle", "N/A")
                                name = attrs.get("name", "N/A")
                                bounty = "💰" if attrs.get("offers_bounties", False) else "🏆"
                                print(f"  {idx}. {bounty} {Colors.GREEN}{handle}{Colors.ENDC} - {name}")

                            idx_choice = input(f"\n{Colors.CYAN}Select program (1-{min(len(matches), 10)}): {Colors.ENDC}").strip()
                            try:
                                idx = int(idx_choice) - 1
                                if 0 <= idx < len(matches):
                                    program_handle = matches[idx].get("attributes", {}).get("handle")
                            except ValueError:
                                print(f"{Colors.RED}[!] Invalid selection{Colors.ENDC}")
                                continue
                    else:
                        program_handle = input(f"{Colors.CYAN}Program handle (e.g., 'security'): {Colors.ENDC}").strip()

                    if not program_handle:
                        print(f"{Colors.RED}[!] No program selected{Colors.ENDC}")
                        continue

                    # Fetch program details
                    print(f"\n{Colors.YELLOW}[*] Fetching program details for '{program_handle}'...{Colors.ENDC}")
                    program = h1_client.get_program(program_handle)

                    # Display formatted details
                    print(h1_client.format_program_details(program))

                    # Ask if user wants to analyze with AI
                    analyze = input(f"\n{Colors.CYAN}Analyze this program with AI? [Y/n]: {Colors.ENDC}").strip().lower()
                    if analyze != 'n':
                        print(f"\n{Colors.YELLOW}[*] Preparing program data for AI analysis...{Colors.ENDC}")
                        bounty_text = h1_client.export_program_for_analysis(program)

                        print(f"{Colors.YELLOW}[*] Analyzing with DeepSeek AI...{Colors.ENDC}")
                        analysis = suite.analyze_bounty(bounty_text)

                        print(f"\n{Colors.GREEN}╔{'═' * 58}╗")
                        print(f"║{Colors.BOLD}{'AI ANALYSIS RESULTS'.center(58)}{Colors.ENDC}{Colors.GREEN}║")
                        print(f"╚{'═' * 58}╝{Colors.ENDC}")
                        print(analysis)
                        print(f"{Colors.GREEN}{'─' * 60}{Colors.ENDC}\n")

                except Exception as e:
                    print(f"{Colors.RED}[✗] Error: {e}{Colors.ENDC}")

            elif choice == '6':
                # Show Tool Status
                show_tool_status()
                continue

            elif choice == '1':
                # Analyze Bounty
                print(f"\n{Colors.CYAN}{'─' * 60}{Colors.ENDC}")
                bounty_text = get_multiline_input(f"{Colors.YELLOW}Paste the bounty text{Colors.ENDC}")
                if not bounty_text:
                    print(f"{Colors.RED}[!] No text provided.{Colors.ENDC}")
                    continue
                try:
                    print(f"\n{Colors.YELLOW}[*] Analyzing bounty program...{Colors.ENDC}")
                    analysis = suite.analyze_bounty(bounty_text)
                    print(f"\n{Colors.GREEN}╔{'═' * 58}╗")
                    print(f"║{Colors.BOLD}{'BOUNTY ANALYSIS'.center(58)}{Colors.ENDC}{Colors.GREEN}║")
                    print(f"╚{'═' * 58}╝{Colors.ENDC}")
                    print(analysis)
                    print(f"{Colors.GREEN}{'─' * 60}{Colors.ENDC}\n")
                except DeepSeekError as e:
                    print(f"{Colors.RED}[✗] Error: {e}{Colors.ENDC}")

            elif choice == '2':
                # Generate Commands (Context-Aware)
                target = input(f"{Colors.CYAN}🎯 Target (e.g., example.com): {Colors.ENDC}").strip()
                if not target:
                    print(f"{Colors.RED}[!] No target provided.{Colors.ENDC}")
                    continue
                try:
                    print(f"\n{Colors.YELLOW}[*] Checking available tools...{Colors.ENDC}")
                    available_tools = get_available_tools()
                    print(f"{Colors.GREEN}[✓] Found {len(available_tools)} available tools{Colors.ENDC}")
                    print(f"{Colors.YELLOW}[*] Generating commands with AI...{Colors.ENDC}")
                    commands = suite.generate_commands(target, available_tools)
                    run_generated_commands(commands)
                except DeepSeekError as e:
                    print(f"{Colors.RED}[✗] Error: {e}{Colors.ENDC}")

            elif choice == '3':
                # Run Commands (Fresh Context)
                print(f"\n{Colors.YELLOW}[i] Clearing history for a fresh session...{Colors.ENDC}")
                suite.clear_history()
                target = input(f"{Colors.CYAN}🎯 Target (e.g., example.com): {Colors.ENDC}").strip()
                if not target:
                    print(f"{Colors.RED}[!] No target provided.{Colors.ENDC}")
                    continue
                try:
                    print(f"\n{Colors.YELLOW}[*] Checking available tools...{Colors.ENDC}")
                    available_tools = get_available_tools()
                    print(f"{Colors.GREEN}[✓] Found {len(available_tools)} available tools{Colors.ENDC}")
                    print(f"{Colors.YELLOW}[*] Generating commands with AI...{Colors.ENDC}")
                    commands = suite.generate_commands(target, available_tools)
                    run_generated_commands(commands)
                except DeepSeekError as e:
                    print(f"{Colors.RED}[✗] Error: {e}{Colors.ENDC}")
            
            elif choice == '4':
                # Stream Chat
                system_prompt = input("System Prompt (optional, press Enter to skip): ").strip()
                message = get_multiline_input("Your Message")
                if not message:
                    print("No message provided.")
                    continue
                
                print("\n--- Stream Response ---")
                try:
                    stream_gen = suite.stream_call_deepseek(message, system_prompt or None)
                    for chunk in stream_gen:
                        print(chunk, end="", flush=True)
                    print("\n-----------------------")
                except DeepSeekError as e:
                    print(f"\n[Error] {e}")

            elif choice == '5':
                # Clear History
                suite.clear_history()
                print("Conversation history cleared.")
            
            else:
                print(f"Unknown command: '{choice}'. Type 'menu' for options.")
        
        except KeyboardInterrupt:
            print("\nAction cancelled. Returning to main menu.")
            continue

# Usage example
if __name__ == "__main__":
    load_dotenv()
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    
    if not api_key:
        print("Error: DEEPSEEK_API_KEY environment variable not set.")
    else:
        try:
            suite = DeepSeekSecuritySuite(api_key)
            main_interactive_loop(suite)
        except ValueError as ve:
            print(f"[Config Error] {ve}")
