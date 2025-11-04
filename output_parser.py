import json
from typing import Dict, Any, Optional

class OutputParser:
    @staticmethod
    def parse(output: str, tool: Optional[str] = None) -> Optional[Dict[str, Any]]:
        if tool:
            parser = getattr(OutputParser, f"parse_{tool}", None)
            if parser:
                return parser(output)
        # Auto-detect
        if "nmap" in output.lower():
            if "<nmaprun>" in output:
                return OutputParser.parse_nmap_xml(output)
            return OutputParser.parse_nmap_simple(output)
        if "subfinder" in output.lower():
            return OutputParser.parse_subfinder(output)
        # Add more auto-detection rules here
        return None

    @staticmethod
    def parse_nmap_xml(xml_data: str) -> Dict[str, Any]:
        # Basic XML parsing, not a full implementation
        # In a real scenario, use a proper XML parsing library
        import xml.etree.ElementTree as ET
        root = ET.fromstring(xml_data)
        hosts = []
        for host in root.findall('host'):
            host_info = {'addresses': [], 'ports': []}
            for addr in host.findall('address'):
                host_info['addresses'].append(addr.attrib)
            for port in host.findall('.//port'):
                port_info = port.attrib
                service = port.find('service')
                if service is not None:
                    port_info['service'] = service.attrib
                host_info['ports'].append(port_info)
            hosts.append(host_info)
        return {"hosts": hosts}

    @staticmethod
    def parse_nmap_simple(text_data: str) -> Dict[str, Any]:
        open_ports = []
        for line in text_data.splitlines():
            if "/tcp" in line and "open" in line:
                parts = line.split()
                port_info = {
                    "port": parts[0],
                    "state": parts[1],
                    "service": parts[2]
                }
                open_ports.append(port_info)
        return {"open_ports": open_ports}

    @staticmethod
    def parse_subfinder(text_data: str) -> Dict[str, Any]:
        subdomains = [line.strip() for line in text_data.splitlines() if line.strip()]
        return {"subdomains": subdomains}

    @staticmethod
    def parse_httpx(json_data: str) -> Dict[str, Any]:
        results = []
        for line in json_data.splitlines():
            if line.strip():
                results.append(json.loads(line))
        return {"httpx_results": results}

def parse_file(filepath: str, tool: Optional[str] = None) -> Optional[Dict[str, Any]]:
    with open(filepath, 'r') as f:
        content = f.read()
    return OutputParser.parse(content, tool)
