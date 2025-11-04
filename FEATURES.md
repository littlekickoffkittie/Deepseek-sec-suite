# New Features Guide

## 🎉 Major Improvements Added!

### 1. Output Parser Module (`output_parser.py`)

Parse security tool outputs into structured data!

**Supported Tools:**
- nmap (XML and text)
- subfinder
- httpx (JSON)
- nuclei (JSON)
- ffuf (JSON)
- whatweb

**Usage:**
```python
from output_parser import OutputParser

# Auto-detect and parse
result = OutputParser.parse(tool_output)

# Or specify tool
result = OutputParser.parse(nmap_output, tool='nmap_xml')

# Parse from file
from output_parser import parse_file
data = parse_file('nmap_scan.xml')
```

**Example:**
```python
# Parse nmap XML
with open('scan.xml') as f:
    xml_data = f.read()

parsed = OutputParser.parse_nmap_xml(xml_data)
for host in parsed['hosts']:
    print(f"Host: {host['addresses'][0]['addr']}")
    for port in host['ports']:
        if port['state'] == 'open':
            print(f"  Port {port['portid']}: {port['service'].get('name', 'unknown')}")
```

---

### 2. Session Management (`session_manager.py`)

Save and resume your testing sessions!

**Features:**
- Track findings by severity
- Record commands executed
- Store AI analyses
- Add manual notes
- Export in multiple formats

**Usage:**
```python
from session_manager import SessionManager

# Create new session
sm = SessionManager()
session = sm.create_session(target="example.com", program="Example Bug Bounty")

# Add findings
sm.add_finding(
    severity="high",
    title="SQL Injection in login form",
    description="SQLi vulnerability found at /login endpoint",
    tool="sqlmap",
    evidence="sqlmap -u 'http://example.com/login?id=1' --dbs"
)

# Track commands
sm.add_command("nmap -sV example.com", output="... nmap output ...")

# Add notes
sm.add_note("Remember to test the API endpoint next")

# Save session
filepath = sm.save_session()
print(f"Session saved to: {filepath}")

# Load later
sm.load_session("session_file.json")

# List all sessions
sessions = sm.list_sessions()
for s in sessions:
    print(f"{s['target']} - {s['findings_count']} findings")
```

---

### 3. Report Generation (`report_generator.py`)

Generate professional security reports!

**Formats:**
- Markdown (`.md`)
- HTML (`.html`)

**Features:**
- Executive summary with stats
- Findings organized by severity
- Color-coded HTML reports
- Timeline of testing activities
- AI analysis included

**Usage:**
```python
from report_generator import ReportGenerator
from session_manager import SessionManager

# Load session
sm = SessionManager()
session = sm.load_session("my_session.json")

# Generate report
rg = ReportGenerator()

# Save as markdown
md_path = rg.save_report(session, format="markdown")
print(f"Markdown report: {md_path}")

# Save as HTML
html_path = rg.save_report(session, format="html")
print(f"HTML report: {html_path}")
```

---

## Complete Workflow Example

```python
from session_manager import SessionManager
from output_parser import OutputParser
from report_generator import ReportGenerator
import subprocess

# 1. Create session
sm = SessionManager()
session = sm.create_session(target="api.example.com", program="Example Bounty")

# 2. Run security scan
result = subprocess.run(['nmap', '-sV', 'api.example.com'],
                       capture_output=True, text=True)

# 3. Parse output
parsed = OutputParser.parse(result.stdout, tool='nmap_simple')

# 4. Record command
sm.add_command('nmap -sV api.example.com', result.stdout)

# 5. Store parsed data
sm.add_tool_output('nmap', parsed)

# 6. Add findings
for port in parsed.get('open_ports', []):
    if port['service'] == 'http':
        sm.add_finding(
            severity="info",
            title=f"HTTP service on port {port['port']}",
            description=f"HTTP service detected on port {port['port']}",
            tool="nmap"
        )

# 7. Add AI analysis
sm.add_ai_analysis("scope_analysis", "Target is in scope for web testing")

# 8. Save session
session_file = sm.save_session()

# 9. Generate report
rg = ReportGenerator()
report_path = rg.save_report(sm.current_session, format="html")

print(f"✓ Session saved: {session_file}")
print(f"✓ Report generated: {report_path}")
```

---

## Integration with Main App

These features are designed to integrate with `security_suite.py`:

1. **Automatic session creation** when starting a new assessment
2. **Parse tool outputs** automatically after command execution
3. **Track all findings** from AI and tool results
4. **Generate reports** on demand or at session end

---

## File Locations

- **Sessions:** Saved in `sessions/` directory
- **Reports:** Saved in `reports/` directory
- **Output parser:** `output_parser.py`
- **Session manager:** `session_manager.py`
- **Report generator:** `report_generator.py`

---

## Quick Tips

### Viewing Session Summary
```python
sm = SessionManager()
sm.load_session("my_session.json")
summary = sm.get_session_summary()
print(summary)
```

### Exporting Findings
```python
# Export as JSON
json_data = sm.export_findings(format="json")

# Export as CSV
csv_data = sm.export_findings(format="csv")

# Export as Markdown
md_data = sm.export_findings(format="markdown")
```

### Merging Sessions
```python
sm = SessionManager()
merged_path = sm.merge_sessions(
    ["session1.json", "session2.json"],
    output_name="combined_assessment"
)
```

---

## Benefits

✅ **Never lose your work** - All findings and commands are saved
✅ **Professional reports** - Generate client-ready documentation
✅ **Structured data** - Parse tool outputs for better analysis
✅ **Track progress** - See what you've tested and what's left
✅ **Collaboration** - Share sessions and reports with team

---

**Upgrade your bug hunting workflow today!** 🚀
