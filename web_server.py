from flask import Flask, render_template, request
from security_suite import DeepSeekSecuritySuite, get_available_tools, ALL_TOOLS
import os
from dotenv import load_dotenv
from pathlib import Path

# Explicitly load .env from the current directory
dotenv_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=dotenv_path)
app = Flask(__name__)

# It's better to initialize this once and reuse it.
# Make sure DEEPSEEK_API_KEY is set in your environment.
api_key = os.getenv("DEEPSEEK_API_KEY")
if not api_key:
    raise ValueError("DEEPSEEK_API_KEY environment variable not set.")
suite = DeepSeekSecuritySuite(api_key=api_key)

@app.route('/', methods=['GET', 'POST'])
def index():
    commands = ""
    if request.method == 'POST':
        target = request.form['target']
        if target:
            # For simplicity, we're not checking for available tools here.
            # In a real application, you would.
            commands = suite.generate_commands(target)
    return render_template('index.html', commands=commands)

@app.route('/analyze', methods=['GET', 'POST'])
def analyze():
    analysis = ""
    if request.method == 'POST':
        bounty_text = request.form['bounty_text']
        if bounty_text:
            analysis = suite.analyze_bounty(bounty_text)
    return render_template('analyze.html', analysis=analysis)

@app.route('/tools')
def tools():
    available_tools = get_available_tools()
    missing_tools = set(ALL_TOOLS) - available_tools
    return render_template('tools.html', available_tools=sorted(available_tools), missing_tools=sorted(missing_tools))

if __name__ == '__main__':
    # Note: This is a development server. For a production environment,
    # use a production-ready WSGI server like Gunicorn or uWSGI.
    # The web interface is a simplified version of the CLI and does not
    # include features like session management or command execution.
    app.run(debug=True, host='0.0.0.0', port=8080)
