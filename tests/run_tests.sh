#!/bin/bash
# Quick test runner script for Security Suite

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${CYAN}╔════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     Security Suite Test Runner            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════╝${NC}"
echo ""

if [ "$1" == "all" ] || [ -z "$1" ]; then
    echo -e "${YELLOW}Running all tests...${NC}"
    pytest test_*.py -v --tb=short

elif [ "$1" == "hackerone" ] || [ "$1" == "h1" ]; then
    echo -e "${YELLOW}Running HackerOne API tests...${NC}"
    pytest test_hackerone_api.py -v

elif [ "$1" == "deepseek" ] || [ "$1" == "ds" ]; then
    echo -e "${YELLOW}Running DeepSeek client tests...${NC}"
    pytest test_sec_deepseek.py -v

elif [ "$1" == "integration" ] || [ "$1" == "int" ]; then
    echo -e "${YELLOW}Running integration tests...${NC}"
    pytest test_integration.py -v

elif [ "$1" == "timeout" ]; then
    echo -e "${YELLOW}Running timeout-specific tests...${NC}"
    pytest test_sec_deepseek.py::TestDeepSeekSecuritySuite::test_call_deepseek_timeout_with_retry -v
    pytest test_sec_deepseek.py::TestDeepSeekSecuritySuite::test_call_deepseek_all_retries_timeout -v
    pytest test_sec_deepseek.py::TestDeepSeekSecuritySuite::test_call_deepseek_connection_error_with_retry -v

elif [ "$1" == "quick" ] || [ "$1" == "q" ]; then
    echo -e "${YELLOW}Running quick smoke tests...${NC}"
    pytest test_hackerone_api.py::TestHackerOneAPI::test_init_with_valid_credentials \
           test_sec_deepseek.py::TestDeepSeekSecuritySuite::test_init_with_valid_api_key \
           test_integration.py::TestIntegration::test_fetch_and_analyze_workflow -v

elif [ "$1" == "coverage" ] || [ "$1" == "cov" ]; then
    echo -e "${YELLOW}Running tests with coverage report...${NC}"
    pytest test_*.py --cov=. --cov-report=term --cov-report=html
    echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"

elif [ "$1" == "help" ] || [ "$1" == "-h" ]; then
    echo -e "${CYAN}Usage: ./run_tests.sh [option]${NC}"
    echo ""
    echo "Options:"
    echo "  all, (default)  - Run all tests"
    echo "  hackerone, h1   - Run HackerOne API tests only"
    echo "  deepseek, ds    - Run DeepSeek client tests only"
    echo "  integration, int- Run integration tests only"
    echo "  timeout         - Run timeout/retry tests only"
    echo "  quick, q        - Run quick smoke tests"
    echo "  coverage, cov   - Run tests with coverage report"
    echo "  help, -h        - Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./run_tests.sh              # Run all tests"
    echo "  ./run_tests.sh deepseek     # Run DeepSeek tests"
    echo "  ./run_tests.sh timeout      # Run timeout tests"

else
    echo -e "${YELLOW}Unknown option: $1${NC}"
    echo "Run './run_tests.sh help' for available options"
    exit 1
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}Test run complete!${NC}"
