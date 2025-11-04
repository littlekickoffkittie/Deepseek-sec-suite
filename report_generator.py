#!/usr/bin/env python3
"""
Report Generator for Security Testing
Generate professional security assessment reports
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class ReportGenerator:
    """Generate security testing reports in various formats"""

    def __init__(self):
        self.reports_dir = Path("reports")
        self.reports_dir.mkdir(exist_ok=True)

    def generate_markdown_report(self, session: Dict[str, Any], include_raw_output: bool = False) -> str:
        """Generate a comprehensive markdown report"""
        lines = []

        # Header
        lines.append("# Security Assessment Report")
        lines.append(f"\n**Target:** {session.get('target', 'N/A')}")
        lines.append(f"**Program:** {session.get('program', 'N/A')}")
        lines.append(f"**Session ID:** {session.get('session_id', 'N/A')}")
        lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("\n---\n")

        # Executive Summary
        lines.append("## Executive Summary\n")
        findings = session.get('findings', [])
        findings_by_severity = {}
        for finding in findings:
            sev = finding.get('severity', 'unknown')
            findings_by_severity[sev] = findings_by_severity.get(sev, 0) + 1

        lines.append(f"Total Findings: **{len(findings)}**\n")
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = findings_by_severity.get(severity, 0)
            if count > 0:
                lines.append(f"- **{severity.upper()}**: {count}")
        lines.append("\n")

        # Tools Used
        tools_used = list(session.get('tool_outputs', {}).keys())
        if tools_used:
            lines.append("### Tools Used\n")
            for tool in tools_used:
                lines.append(f"- {tool}")
            lines.append("\n")

        # Testing Timeline
        lines.append("### Testing Timeline\n")
        lines.append(f"- **Started:** {session.get('created_at', 'N/A')}")
        lines.append(f"- **Last Updated:** {session.get('updated_at', 'N/A')}")
        lines.append(f"- **Commands Executed:** {len(session.get('commands_run', []))}")
        lines.append("\n---\n")

        # Findings Detail
        if findings:
            lines.append("## Detailed Findings\n")

            # Sort by severity
            severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
            sorted_findings = sorted(findings,
                                   key=lambda x: severity_order.get(x.get('severity', 'info'), 999))

            for idx, finding in enumerate(sorted_findings, 1):
                severity = finding.get('severity', 'unknown').upper()
                title = finding.get('title', 'Untitled Finding')
                status = finding.get('status', 'new')

                lines.append(f"### Finding #{idx}: {title}")
                lines.append(f"\n**Severity:** {severity} | **Status:** {status}")

                tool = finding.get('tool')
                if tool:
                    lines.append(f" | **Detected by:** {tool}")

                lines.append(f"\n\n**Description:**\n{finding.get('description', 'No description provided')}")

                evidence = finding.get('evidence')
                if evidence:
                    lines.append(f"\n**Evidence:**\n```\n{evidence}\n```")

                lines.append(f"\n**Timestamp:** {finding.get('timestamp', 'N/A')}")
                lines.append("\n---\n")

        # AI Analysis
        ai_analyses = session.get('ai_analysis', [])
        if ai_analyses:
            lines.append("## AI Analysis\n")
            for analysis in ai_analyses:
                lines.append(f"### {analysis.get('type', 'Analysis')}")
                lines.append(f"\n{analysis.get('content', 'No content')}")
                lines.append(f"\n*Generated at: {analysis.get('timestamp', 'N/A')}*\n")
                lines.append("\n---\n")

        # Commands Run
        commands = session.get('commands_run', [])
        if commands and include_raw_output:
            lines.append("## Commands Executed\n")
            for cmd in commands[:20]:  # Limit to 20 commands
                lines.append(f"### Command")
                lines.append(f"```bash\n{cmd.get('command', 'N/A')}\n```")
                lines.append(f"**Exit Code:** {cmd.get('exit_code', 'N/A')}")
                lines.append(f"**Timestamp:** {cmd.get('timestamp', 'N/A')}")
                output = cmd.get('output', '')
                if output:
                    lines.append(f"\n**Output:**\n```\n{output[:500]}...\n```")
                lines.append("\n")

        # Notes
        notes = session.get('notes', [])
        if notes:
            lines.append("## Notes\n")
            for note in notes:
                lines.append(f"- **{note.get('timestamp', 'N/A')}:** {note.get('content', '')}")
            lines.append("\n")

        # Footer
        lines.append("\n---\n")
        lines.append("*Report generated by DeepSeek Security Suite*\n")
        lines.append(f"*Generated at: {datetime.now().isoformat()}*\n")

        return "\n".join(lines)

    def generate_html_report(self, session: Dict[str, Any]) -> str:
        """Generate an HTML report"""
        findings = session.get('findings', [])
        findings_by_severity = {}
        for finding in findings:
            sev = finding.get('severity', 'unknown')
            findings_by_severity[sev] = findings_by_severity.get(sev, 0) + 1

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Assessment Report - {session.get('target', 'N/A')}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .finding {{
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            border-left: 5px solid #ccc;
        }}
        .finding.critical {{ border-left-color: #dc3545; }}
        .finding.high {{ border-left-color: #fd7e14; }}
        .finding.medium {{ border-left-color: #ffc107; }}
        .finding.low {{ border-left-color: #28a745; }}
        .finding.info {{ border-left-color: #17a2b8; }}
        .severity-badge {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 5px;
            color: white;
            font-weight: bold;
            font-size: 0.9em;
        }}
        .severity-critical {{ background-color: #dc3545; }}
        .severity-high {{ background-color: #fd7e14; }}
        .severity-medium {{ background-color: #ffc107; color: #333; }}
        .severity-low {{ background-color: #28a745; }}
        .severity-info {{ background-color: #17a2b8; }}
        code {{
            background: #f4f4f4;
            padding: 2px 5px;
            border-radius: 3px;
            font-family: monospace;
        }}
        pre {{
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Security Assessment Report</h1>
        <p><strong>Target:</strong> {session.get('target', 'N/A')}</p>
        <p><strong>Program:</strong> {session.get('program', 'N/A')}</p>
        <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-number">{len(findings)}</div>
            <div>Total Findings</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{findings_by_severity.get('critical', 0) + findings_by_severity.get('high', 0)}</div>
            <div>Critical/High</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len(session.get('commands_run', []))}</div>
            <div>Commands Run</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len(session.get('tool_outputs', {}))}</div>
            <div>Tools Used</div>
        </div>
    </div>

    <div class="summary">
        <h2>Executive Summary</h2>
        <p>This report contains findings from a security assessment of <strong>{session.get('target', 'N/A')}</strong>.</p>
        <h3>Findings Breakdown:</h3>
        <ul>"""

        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            count = findings_by_severity.get(severity, 0)
            if count > 0:
                html += f'<li><strong>{severity.upper()}:</strong> {count}</li>'

        html += """
        </ul>
    </div>

    <h2>Detailed Findings</h2>"""

        # Sort and display findings
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
        sorted_findings = sorted(findings,
                               key=lambda x: severity_order.get(x.get('severity', 'info'), 999))

        for idx, finding in enumerate(sorted_findings, 1):
            severity = finding.get('severity', 'unknown')
            title = finding.get('title', 'Untitled Finding')
            description = finding.get('description', 'No description')
            tool = finding.get('tool', 'N/A')
            evidence = finding.get('evidence', '')

            html += f"""
    <div class="finding {severity}">
        <h3>Finding #{idx}: {title}</h3>
        <p>
            <span class="severity-badge severity-{severity}">{severity.upper()}</span>
            <strong>Tool:</strong> {tool}
        </p>
        <p><strong>Description:</strong></p>
        <p>{description}</p>"""

            if evidence:
                html += f"""
        <p><strong>Evidence:</strong></p>
        <pre><code>{evidence[:500]}</code></pre>"""

            html += """
    </div>"""

        html += """
    <div class="summary">
        <p><em>Report generated by DeepSeek Security Suite</em></p>
        <p><em>Generated at: """ + datetime.now().isoformat() + """</em></p>
    </div>
</body>
</html>"""

        return html

    def save_report(self, session: Dict[str, Any], format: str = "markdown",
                   filename: Optional[str] = None) -> str:
        """Save report to file"""
        if format == "markdown":
            content = self.generate_markdown_report(session)
            ext = ".md"
        elif format == "html":
            content = self.generate_html_report(session)
            ext = ".html"
        else:
            raise ValueError(f"Unsupported format: {format}")

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target = session.get('target', 'unknown').replace('/', '_')
            filename = f"report_{target}_{timestamp}{ext}"

        filepath = self.reports_dir / filename

        with open(filepath, 'w') as f:
            f.write(content)

        return str(filepath)
