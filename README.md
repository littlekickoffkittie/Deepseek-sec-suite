# 🔐 DeepSeek Security Suite

**An AI-powered security research toolkit with HackerOne integration**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-34%20passed-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A comprehensive security testing suite that combines DeepSeek AI with HackerOne's bug bounty platform to streamline vulnerability research and testing workflows.

## ✨ Features

- **🤖 AI-Powered Analysis** - Automatic bounty program analysis using DeepSeek AI
- **🎯 HackerOne Integration** - Direct access to 500+ bug bounty programs
- **⚡ Smart Command Generation** - AI-generated security testing commands
- **🔄 Robust Error Handling** - Auto-retry with exponential backoff
- **🛠️ Tool Management** - Automatic security tool detection and filtering
- **📊 Comprehensive Testing** - 34 tests with 100% pass rate

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/deepseek-security-suite.git
cd deepseek-security-suite

# Install dependencies and test packages
pip install -e ".[test]"

# Set up credentials
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Create a `.env` file with your API credentials:

```bash
# DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_api_key

# HackerOne API (optional but recommended)
HACKERONE_USERNAME=your_username
HACKERONE_API_TOKEN=your_api_token
```

Get your credentials:
- **DeepSeek**: https://platform.deepseek.com/api_keys
- **HackerOne**: https://hackerone.com/settings/api_token/edit

## 📖 Usage

### Starting the Suite

```bash
python security_suite.py
```

### Main Menu Options

```
[0] Fetch Program from HackerOne    - Auto-analyze and create a session
[1] Analyze Bounty                  - Paste and analyze bounty details
[2] Generate Commands               - AI-powered security testing commands
[3] Run Commands for Target         - Execute generated commands in a session
[4] Stream Free-form Chat           - Interactive AI assistance
[5] Clear Conversation History      - Reset AI context
[6] Show Tool Status                - Check for installed security tools
[7] Session Management              - Create, load, or delete testing sessions
[8] Generate Report                 - Create a full report from a session
```

### Example Workflow

```bash
# 1. Start the suite
python security_suite.py

# 2. Create a new session for your target
[Main] ▶ 7
[Session] ▶ 1
Enter target (e.g., example.com): api.example.com

# 3. Fetch a program and let the AI analyze it
[Main] ▶ 0
Search query: ExampleCorp

# 4. Generate and run context-aware commands
[Main] ▶ 2
Target: api.example.com
# Commands are generated...
Do you want to run these commands? (all/one/N) [N]: all

# 5. View session summary
[Main] ▶ 7
[Session] ▶ 5

# 6. Generate a professional HTML report
[Main] ▶ 8
Enter report format (md/html) [html]: html
```

## 🧪 Testing

### Run All Tests

```bash
# Using the test runner
./tests/run_tests.sh

# Or using pytest directly
pytest tests/ -v
```

### Test Coverage

- **HackerOne API Tests** (12 tests)
  - Authentication and initialization
  - API request handling
  - Error handling (401, 404, timeout)
  - Program listing & pagination

- **DeepSeek Client Tests** (16 tests)
  - Timeout handling with retry logic
  - Exponential backoff
  - Connection error recovery
  - Rate limit handling

- **Integration Tests** (6 tests)
  - End-to-end workflows
  - Cross-component interactions
  - Real-world scenarios

### Test Results

```
============================= test session starts ==============================
collected 34 items

test_hackerone_api.py::TestHackerOneAPI   12 passed   ✓
test_sec_deepseek.py::TestDeepSeek        16 passed   ✓
test_integration.py::TestIntegration       6 passed   ✓

============================== 34 passed in 0.31s ==============================
```

## 🏗️ Project Structure

```
deepseek-security-suite/
├── security_suite.py           # Main application
├── hackerone_api.py            # HackerOne API client
├── session_manager.py          # Session management module
├── output_parser.py            # Tool output parsing module
├── report_generator.py         # Report generation module
├── tests/
│   ├── test_hackerone_api.py   # HackerOne tests
│   └── ...                     # Other test files
├── docs/
│   └── ...
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore rules
├── pyproject.toml              # Project metadata and dependencies
└── README.md                   # This file
```

## 🔧 Configuration

### Timeout Settings

Default timeout is 120 seconds with 3 automatic retries:

```python
suite = DeepSeekSecuritySuite(
    api_key="your_key",
    timeout=120,        # Request timeout in seconds
    max_retries=3       # Number of retry attempts
)
```

### Retry Logic

The suite implements smart retry logic:
- ✓ Retries on: Timeouts, 5xx errors, 429 rate limits
- ✗ No retry on: 4xx client errors (except 429)
- ⏱️ Exponential backoff: 2s, 5s, 9s between retries

## 📚 Documentation

- **[HackerOne Setup Guide](docs/HACKEONE_SETUP.md)** - Detailed setup instructions
- **[Test Summary](docs/TEST_SUMMARY.md)** - Comprehensive test report
- **API Documentation** - See inline docstrings in source code

## 🛠️ Development

### Setting Up Development Environment

```bash
# Install in editable mode with test and dev dependencies
pip install -e ".[test,dev]"

# Run tests with coverage
pytest tests/ --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Running Specific Tests

```bash
# Test timeout/retry logic
./tests/run_tests.sh timeout

# Test HackerOne integration
./tests/run_tests.sh hackerone

# Quick smoke tests
./tests/run_tests.sh quick
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Quality

- Write tests for new features
- Follow PEP 8 style guidelines
- Add docstrings to public functions
- Update documentation as needed

## 🔒 Security

### Best Practices

- ✓ Never commit `.env` files
- ✓ Rotate API tokens regularly
- ✓ Only test authorized targets
- ✓ Follow responsible disclosure
- ✓ Respect program scope and rules

### Reporting Security Issues

Please report security vulnerabilities to: security@example.com

## 🐛 Troubleshooting

### Common Issues

**Issue: API Timeout Errors**
```
Solution: The suite has automatic retry logic (3 attempts).
If issues persist, increase timeout in initialization.
```

**Issue: HackerOne Authentication Failed**
```
Solution: Verify credentials in .env file
Check: https://hackeone.com/settings/api_token/edit
```

**Issue: Missing Security Tools**
```
Solution: Run option [6] to see missing tools
Install: ./setup-security-tools.sh (if available)
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **DeepSeek AI** - For the powerful language model API
- **HackerOne** - For the comprehensive bug bounty platform API
- **Security Community** - For tools and knowledge sharing

## 📞 Contact

- **Author**: Lucie Bloodroot
- **GitHub**: [@luciebloodroot](https://github.com/luciebloodroot)
- **Issues**: [GitHub Issues](https://github.com/yourusername/deepseek-security-suite/issues)

## 🗺️ Roadmap

- [ ] Add support for more bug bounty platforms
- [ ] Implement automatic report generation
- [ ] Add vulnerability scanning modules
- [ ] Create web interface
- [ ] Docker containerization
- [ ] CI/CD pipeline integration

---

**⭐ Star this repo if you find it useful!**

Made with ❤️ for the security research community
