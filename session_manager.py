#!/usr/bin/env python3
"""
Session Management for Security Suite
Save and load analysis sessions with findings
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class SessionManager:
    """Manage analysis sessions"""

    def __init__(self, sessions_dir: str = "sessions"):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)
        self.current_session: Optional[Dict[str, Any]] = None

    def create_session(self, target: str, program: Optional[str] = None) -> Dict[str, Any]:
        """Create a new session"""
        session = {
            "session_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "target": target,
            "program": program,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "findings": [],
            "commands_run": [],
            "tool_outputs": {},
            "ai_analysis": [],
            "notes": []
        }
        self.current_session = session
        return session

    def add_finding(self, severity: str, title: str, description: str,
                    tool: Optional[str] = None, evidence: Optional[str] = None):
        """Add a finding to current session"""
        if not self.current_session:
            raise ValueError("No active session")

        finding = {
            "id": len(self.current_session["findings"]) + 1,
            "timestamp": datetime.now().isoformat(),
            "severity": severity,
            "title": title,
            "description": description,
            "tool": tool,
            "evidence": evidence,
            "status": "new"
        }
        self.current_session["findings"].append(finding)
        self.current_session["updated_at"] = datetime.now().isoformat()

    def add_command(self, command: str, output: str, exit_code: int = 0):
        """Record a command that was run"""
        if not self.current_session:
            raise ValueError("No active session")

        cmd_record = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "output": output[:1000],  # Truncate long outputs
            "exit_code": exit_code
        }
        self.current_session["commands_run"].append(cmd_record)
        self.current_session["updated_at"] = datetime.now().isoformat()

    def add_tool_output(self, tool: str, output: Any):
        """Store parsed tool output"""
        if not self.current_session:
            raise ValueError("No active session")

        if tool not in self.current_session["tool_outputs"]:
            self.current_session["tool_outputs"][tool] = []

        self.current_session["tool_outputs"][tool].append({
            "timestamp": datetime.now().isoformat(),
            "data": output
        })
        self.current_session["updated_at"] = datetime.now().isoformat()

    def add_ai_analysis(self, analysis_type: str, content: str):
        """Add AI analysis result"""
        if not self.current_session:
            raise ValueError("No active session")

        analysis = {
            "timestamp": datetime.now().isoformat(),
            "type": analysis_type,
            "content": content
        }
        self.current_session["ai_analysis"].append(analysis)
        self.current_session["updated_at"] = datetime.now().isoformat()

    def add_note(self, note: str):
        """Add a manual note"""
        if not self.current_session:
            raise ValueError("No active session")

        note_entry = {
            "timestamp": datetime.now().isoformat(),
            "content": note
        }
        self.current_session["notes"].append(note_entry)
        self.current_session["updated_at"] = datetime.now().isoformat()

    def update_finding_status(self, finding_id: int, status: str):
        """Update finding status (new, confirmed, false_positive, reported)"""
        if not self.current_session:
            raise ValueError("No active session")

        for finding in self.current_session["findings"]:
            if finding["id"] == finding_id:
                finding["status"] = status
                finding["status_updated_at"] = datetime.now().isoformat()
                self.current_session["updated_at"] = datetime.now().isoformat()
                return True
        return False

    def save_session(self, session_name: Optional[str] = None) -> str:
        """Save current session to file"""
        if not self.current_session:
            raise ValueError("No active session to save")

        if session_name:
            filename = f"{session_name}.json"
        else:
            filename = f"{self.current_session['session_id']}_{self.current_session['target'].replace('/', '_')}.json"

        filepath = self.sessions_dir / filename

        with open(filepath, 'w') as f:
            json.dump(self.current_session, f, indent=2)

        return str(filepath)

    def load_session(self, session_file: str) -> Dict[str, Any]:
        """Load a session from file"""
        filepath = self.sessions_dir / session_file if not '/' in session_file else Path(session_file)

        if not filepath.exists():
            raise FileNotFoundError(f"Session file not found: {filepath}")

        with open(filepath, 'r') as f:
            session = json.load(f)

        self.current_session = session
        return session

    def list_sessions(self) -> List[Dict[str, str]]:
        """List all saved sessions"""
        sessions = []

        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)
                    sessions.append({
                        "filename": session_file.name,
                        "session_id": data.get("session_id", "unknown"),
                        "target": data.get("target", "unknown"),
                        "program": data.get("program", "N/A"),
                        "created_at": data.get("created_at", "unknown"),
                        "findings_count": len(data.get("findings", [])),
                        "commands_count": len(data.get("commands_run", []))
                    })
            except Exception:
                continue

        # Sort by created_at descending
        sessions.sort(key=lambda x: x["created_at"], reverse=True)
        return sessions

    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session"""
        if not self.current_session:
            return {"error": "No active session"}

        findings_by_severity = {}
        for finding in self.current_session["findings"]:
            sev = finding["severity"]
            findings_by_severity[sev] = findings_by_severity.get(sev, 0) + 1

        return {
            "session_id": self.current_session["session_id"],
            "target": self.current_session["target"],
            "program": self.current_session.get("program"),
            "duration": (datetime.fromisoformat(self.current_session["updated_at"]) -
                        datetime.fromisoformat(self.current_session["created_at"])).total_seconds(),
            "total_findings": len(self.current_session["findings"]),
            "findings_by_severity": findings_by_severity,
            "commands_run": len(self.current_session["commands_run"]),
            "tools_used": list(self.current_session["tool_outputs"].keys()),
            "ai_analyses": len(self.current_session["ai_analysis"]),
            "notes_count": len(self.current_session["notes"])
        }

    def export_findings(self, format: str = "json") -> str:
        """Export findings in various formats"""
        if not self.current_session:
            raise ValueError("No active session")

        findings = self.current_session["findings"]

        if format == "json":
            return json.dumps(findings, indent=2)

        elif format == "csv":
            import csv
            from io import StringIO

            output = StringIO()
            if findings:
                writer = csv.DictWriter(output, fieldnames=findings[0].keys())
                writer.writeheader()
                writer.writerows(findings)
            return output.getvalue()

        elif format == "markdown":
            lines = [f"# Findings for {self.current_session['target']}\n"]
            lines.append(f"**Total Findings:** {len(findings)}\n")

            for finding in findings:
                lines.append(f"\n## [{finding['severity'].upper()}] {finding['title']}")
                lines.append(f"**Status:** {finding['status']}")
                lines.append(f"**Tool:** {finding.get('tool', 'N/A')}")
                lines.append(f"**Description:**\n{finding['description']}")
                if finding.get('evidence'):
                    lines.append(f"**Evidence:**\n```\n{finding['evidence']}\n```")
                lines.append("\n---")

            return "\n".join(lines)

        else:
            raise ValueError(f"Unknown export format: {format}")

    def delete_session(self, session_file: str) -> bool:
        """Delete a session file"""
        filepath = self.sessions_dir / session_file
        if filepath.exists():
            filepath.unlink()
            return True
        return False

    def merge_sessions(self, session_files: List[str], output_name: str) -> str:
        """Merge multiple sessions into one"""
        merged = {
            "session_id": output_name,
            "target": "merged",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "findings": [],
            "commands_run": [],
            "tool_outputs": {},
            "ai_analysis": [],
            "notes": []
        }

        for session_file in session_files:
            session = self.load_session(session_file)
            merged["findings"].extend(session.get("findings", []))
            merged["commands_run"].extend(session.get("commands_run", []))
            merged["ai_analysis"].extend(session.get("ai_analysis", []))
            merged["notes"].extend(session.get("notes", []))

            # Merge tool outputs
            for tool, outputs in session.get("tool_outputs", {}).items():
                if tool not in merged["tool_outputs"]:
                    merged["tool_outputs"][tool] = []
                merged["tool_outputs"][tool].extend(outputs)

        # Renumber findings
        for i, finding in enumerate(merged["findings"], 1):
            finding["id"] = i

        self.current_session = merged
        return self.save_session(output_name)
