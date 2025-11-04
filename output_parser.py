#!/usr/bin/env python3
"""
Output Parser for Security Tools
Parses outputs from common security tools into structured data
"""
import json
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
import re


class OutputParser:
    """Parse outputs from various security tools"""

    @staticmethod
    def parse_nmap_xml(xml_content: str) -> Dict[str, Any]:
        """Parse nmap XML output"""
        try:
            root = ET.fromstring(xml_content)
            results = {
                "scan_info": {},
                "hosts": []
            }

            # Parse scan info
            scaninfo = root.find('scaninfo')
            if scaninfo is not None:
                results["scan_info"] = dict(scaninfo.attrib)

            # Parse hosts
            for host in root.findall('host'):
                host_data = {
                    "status": "",
                    "addresses": [],
                    "hostnames": [],
                    "ports": [],
                    "os": []
                }

                # Status
                status = host.find('status')
                if status is not None:
                    host_data["status"] = status.get('state', '')

                # Addresses
                for addr in host.findall('address'):
                    host_data["addresses"].append({
                        "addr": addr.get('addr'),
                        "addrtype": addr.get('addrtype')
                    })

                # Hostnames
                hostnames = host.find('hostnames')
                if hostnames is not None:
                    for hostname in hostnames.findall('hostname'):
                        host_data["hostnames"].append(hostname.get('name'))

                # Ports
                ports = host.find('ports')
                if ports is not None:
                    for port in ports.findall('port'):
                        port_data = {
                            "portid": port.get('portid'),
                            "protocol": port.get('protocol'),
                            "state": "",
                            "service": {}
                        }

                        state = port.find('state')
                        if state is not None:
                            port_data["state"] = state.get('state', '')

                        service = port.find('service')
                        if service is not None:
                            port_data["service"] = dict(service.attrib)

                        host_data["ports"].append(port_data)

                # OS Detection
                os_elem = host.find('os')
                if os_elem is not None:
                    for osmatch in os_elem.findall('osmatch'):
                        host_data["os"].append({
                            "name": osmatch.get('name'),
                            "accuracy": osmatch.get('accuracy')
                        })

                results["hosts"].append(host_data)

            return results

        except ET.ParseError as e:
            return {"error": f"XML parse error: {str(e)}"}

    @staticmethod
    def parse_subfinder(output: str) -> List[str]:
        """Parse subfinder output (simple line-by-line subdomains)"""
        subdomains = []
        for line in output.strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('[') and not line.startswith('#'):
                subdomains.append(line)
        return subdomains

    @staticmethod
    def parse_httpx_json(json_content: str) -> List[Dict[str, Any]]:
        """Parse httpx JSON output"""
        results = []
        for line in json_content.strip().split('\n'):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                parsed = {
                    "url": data.get('url', ''),
                    "status_code": data.get('status_code', 0),
                    "content_length": data.get('content_length', 0),
                    "title": data.get('title', ''),
                    "webserver": data.get('webserver', ''),
                    "tech": data.get('tech', []),
                    "method": data.get('method', ''),
                    "host": data.get('host', ''),
                    "path": data.get('path', ''),
                    "time": data.get('time', '')
                }
                results.append(parsed)
            except json.JSONDecodeError:
                continue
        return results

    @staticmethod
    def parse_nuclei_json(json_content: str) -> List[Dict[str, Any]]:
        """Parse nuclei JSON output"""
        findings = []
        for line in json_content.strip().split('\n'):
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                finding = {
                    "template_id": data.get('template-id', ''),
                    "template": data.get('template', ''),
                    "type": data.get('type', ''),
                    "host": data.get('host', ''),
                    "matched_at": data.get('matched-at', ''),
                    "severity": data.get('info', {}).get('severity', 'unknown'),
                    "name": data.get('info', {}).get('name', ''),
                    "description": data.get('info', {}).get('description', ''),
                    "tags": data.get('info', {}).get('tags', []),
                    "reference": data.get('info', {}).get('reference', []),
                    "extracted_results": data.get('extracted-results', []),
                    "matcher_name": data.get('matcher-name', ''),
                    "timestamp": data.get('timestamp', '')
                }
                findings.append(finding)
            except json.JSONDecodeError:
                continue
        return findings

    @staticmethod
    def parse_ffuf_json(json_content: str) -> Dict[str, Any]:
        """Parse ffuf JSON output"""
        try:
            data = json.loads(json_content)
            return {
                "command_line": data.get('commandline', ''),
                "time": data.get('time', ''),
                "results": [
                    {
                        "url": r.get('url', ''),
                        "status": r.get('status', 0),
                        "length": r.get('length', 0),
                        "words": r.get('words', 0),
                        "lines": r.get('lines', 0),
                        "redirectlocation": r.get('redirectlocation', ''),
                        "duration": r.get('duration', 0)
                    }
                    for r in data.get('results', [])
                ]
            }
        except json.JSONDecodeError as e:
            return {"error": f"JSON parse error: {str(e)}"}

    @staticmethod
    def parse_nmap_simple(output: str) -> Dict[str, Any]:
        """Parse simple nmap text output"""
        results = {
            "hosts": [],
            "open_ports": []
        }

        # Extract IP addresses
        ip_pattern = r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
        ips = re.findall(ip_pattern, output)
        results["hosts"] = list(set(ips))

        # Extract open ports
        port_pattern = r'(\d+)/(\w+)\s+open\s+(\S+)'
        ports = re.findall(port_pattern, output)
        for port, protocol, service in ports:
            results["open_ports"].append({
                "port": int(port),
                "protocol": protocol,
                "service": service
            })

        return results

    @staticmethod
    def parse_whatweb(output: str) -> List[Dict[str, Any]]:
        """Parse whatweb output"""
        results = []
        for line in output.strip().split('\n'):
            if not line.strip() or line.startswith('['):
                continue

            # Basic parsing: URL [status] [tech1, tech2, ...]
            parts = line.split('[')
            if len(parts) >= 2:
                url = parts[0].strip()
                tech_parts = '['.join(parts[1:])

                result = {
                    "url": url,
                    "technologies": []
                }

                # Extract technologies
                tech_matches = re.findall(r'([^,\[\]]+)', tech_parts)
                result["technologies"] = [t.strip() for t in tech_matches if t.strip()]

                results.append(result)

        return results

    @staticmethod
    def identify_tool_output(output: str, filename: Optional[str] = None) -> str:
        """Identify which tool generated the output"""
        output_lower = output.lower()

        # Check XML for nmap
        if output.strip().startswith('<?xml') and 'nmap' in output_lower:
            return 'nmap_xml'

        # Check for JSON tools
        try:
            json.loads(output.split('\n')[0])
            if 'template-id' in output:
                return 'nuclei_json'
            elif 'status_code' in output and 'content_length' in output:
                return 'httpx_json'
            elif 'commandline' in output and 'ffuf' in output_lower:
                return 'ffuf_json'
        except:
            pass

        # Check filename
        if filename:
            filename_lower = filename.lower()
            if 'nmap' in filename_lower:
                return 'nmap_xml' if filename.endswith('.xml') else 'nmap_simple'
            elif 'subfinder' in filename_lower or 'subdomain' in filename_lower:
                return 'subfinder'
            elif 'httpx' in filename_lower:
                return 'httpx_json'
            elif 'nuclei' in filename_lower:
                return 'nuclei_json'
            elif 'ffuf' in filename_lower:
                return 'ffuf_json'
            elif 'whatweb' in filename_lower:
                return 'whatweb'

        # Check content patterns
        if 'starting nmap' in output_lower:
            return 'nmap_simple'
        elif re.search(r'^\S+\.\S+\.\S+$', output.strip(), re.MULTILINE):
            return 'subfinder'

        return 'unknown'

    @staticmethod
    def parse(output: str, tool: Optional[str] = None, filename: Optional[str] = None) -> Any:
        """
        Auto-parse output based on tool type

        Args:
            output: Tool output string
            tool: Tool name (optional, will auto-detect if not provided)
            filename: Filename (optional, helps with detection)

        Returns:
            Parsed output in structured format
        """
        if tool is None:
            tool = OutputParser.identify_tool_output(output, filename)

        parsers = {
            'nmap_xml': OutputParser.parse_nmap_xml,
            'nmap_simple': OutputParser.parse_nmap_simple,
            'subfinder': OutputParser.parse_subfinder,
            'httpx_json': OutputParser.parse_httpx_json,
            'nuclei_json': OutputParser.parse_nuclei_json,
            'ffuf_json': OutputParser.parse_ffuf_json,
            'whatweb': OutputParser.parse_whatweb
        }

        parser = parsers.get(tool)
        if parser:
            return parser(output)
        else:
            return {"error": f"Unknown tool type: {tool}", "raw_output": output}


# Convenience functions
def parse_tool_output(output: str, tool: Optional[str] = None) -> Any:
    """Convenience function to parse tool output"""
    return OutputParser.parse(output, tool)


def parse_file(filepath: str, tool: Optional[str] = None) -> Any:
    """Parse tool output from file"""
    with open(filepath, 'r') as f:
        content = f.read()
    return OutputParser.parse(content, tool, filepath)
