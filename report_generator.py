from typing import Dict, Any
import os
from datetime import datetime

class ReportGenerator:
    def save_report(self, session_data: Dict[str, Any], format: str = "html") -> str:
        if format == "markdown":
            content = self._generate_markdown(session_data)
            ext = "md"
        elif format == "html":
            content = self._generate_html(session_data)
            ext = "html"
        else:
            raise ValueError(f"Unsupported format: {format}")

        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)
        filename = f"report_{session_data['session_id']}.{ext}"
        filepath = os.path.join(reports_dir, filename)

        with open(filepath, 'w') as f:
            f.write(content)

        return filepath

    def _generate_markdown(self, data: Dict[str, Any]) -> str:
        lines = [f"# Security Report for {data['target']}"]
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        lines.append("## Executive Summary")
        lines.append(f"- **Target:** {data['target']}")
        lines.append(f"- **Program:** {data.get('program', 'N/A')}")
        lines.append(f"- **Total Findings:** {len(data['findings'])}")

        lines.append("\n## Findings")
        for finding in data['findings']:
            lines.append(f"\n### [{finding['severity'].upper()}] {finding['title']}")
            lines.append(f"- **Tool:** {finding.get('tool', 'N/A')}")
            lines.append(f"- **Description:** {finding['description']}")
            if finding.get('evidence'):
                lines.append(f"**Evidence:**\n```\n{finding['evidence']}\n```")

        return "\n".join(lines)

    def _generate_html(self, data: Dict[str, Any]) -> str:
        # Basic HTML generation, for a real tool, use a template engine like Jinja2
        findings_html = ""
        for finding in data['findings']:
            findings_html += f"""
            <div class="finding">
                <h3>[{finding['severity'].upper()}] {finding['title']}</h3>
                <p><strong>Tool:</strong> {finding.get('tool', 'N/A')}</p>
                <p><strong>Description:</strong> {finding['description']}</p>
            </div>
            """

        html = f"""
        <html>
        <head>
            <title>Security Report for {data['target']}</title>
            <style>
                body {{ font-family: sans-serif; }}
                .finding {{ border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; }}
            </style>
        </head>
        <body>
            <h1>Security Report for {data['target']}</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <h2>Findings</h2>
            {findings_html}
        </body>
        </html>
        """
        return html
