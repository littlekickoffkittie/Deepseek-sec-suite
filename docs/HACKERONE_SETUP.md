# HackerOne API Setup Guide

This guide will help you set up HackerOne API integration for automated bounty program fetching.

## Prerequisites

- A HackerOne account
- Python 3.6+ with `requests` and `python-dotenv` packages

## Step 1: Get Your API Credentials

1. Log in to HackerOne: https://hackerone.com
2. Go to Settings → API Tokens: https://hackerone.com/settings/api_token/edit
3. Click "Create API Token"
4. Give it a name (e.g., "Security Testing Suite")
5. Copy both:
   - Your HackerOne username
   - The generated API token

## Step 2: Add Credentials to .env File

Create or edit the `.env` file in your home directory:

```bash
# HackerOne API Credentials
HACKERONE_USERNAME=your_username_here
HACKERONE_API_TOKEN=your_api_token_here

# DeepSeek API (if not already set)
DEEPSEEK_API_KEY=your_deepseek_key_here
```

**Security Note:** Never commit your `.env` file to version control!

## Step 3: Test the Integration

### Option 1: Use the standalone HackerOne client

```bash
python hackerone_api.py
```

This will show an interactive menu with options to:
- List all available programs
- Search for specific programs
- Get detailed program information
- Export program details for analysis

### Option 2: Use the integrated security suite

```bash
python sec.py
```

Then select option `[0] Fetch Program from HackerOne`

## Features

### Search Programs
Search for bug bounty programs by name or handle:
- Search: "stripe" → Find Stripe's bounty program
- Search: "security" → Find programs with "security" in the name

### Get Program Details
Fetch comprehensive information including:
- Program name, handle, and URL
- In-scope assets (domains, applications, etc.)
- Out-of-scope items
- Bounty eligibility
- Program policy and rules
- Statistics (resolved reports, etc.)

### AI Analysis Integration
When using `sec.py`, you can:
1. Fetch a program from HackerOne
2. Automatically analyze it with DeepSeek AI
3. Get structured insights about:
   - In-scope targets
   - Out-of-scope items
   - Testing guidelines
   - Rules and restrictions
   - Reward information

## Troubleshooting

### Authentication Error
If you get a 401 error:
- Double-check your username and API token
- Make sure there are no extra spaces in your `.env` file
- Verify your token hasn't expired

### Connection Timeout
If requests timeout:
- Check your internet connection
- The default timeout is 30s, you can increase it when initializing the client

### Rate Limiting
HackerOne may rate limit API requests:
- Add delays between requests
- Reduce the number of concurrent requests
- Check HackerOne's API documentation for rate limits

## API Limits & Best Practices

1. **Be respectful**: Don't spam the API with requests
2. **Cache results**: Save program details locally to avoid repeated fetches
3. **Stay updated**: Check HackerOne's API docs for changes: https://api.hackerone.com/docs/v1

## Example Workflow

```bash
# 1. Start the security suite
python sec.py

# 2. Select [0] Fetch Program from HackerOne

# 3. Search for a program
#    - Option 1: Search
#    - Query: "stripe"
#    - Select from results

# 4. Review program details

# 5. Analyze with AI
#    - Get structured analysis
#    - Context is saved for next commands

# 6. Select [2] Generate Commands
#    - Enter a target from in-scope assets
#    - Get AI-generated security testing commands

# 7. Select [3] or manual execution
#    - Run the suggested commands
#    - Review results
```

## Additional Resources

- HackerOne API Documentation: https://api.hackerone.com/docs/v1
- HackerOne Directory: https://hackerone.com/directory/programs
- API Token Management: https://hackerone.com/settings/api_token/edit

## Security Notes

1. **Protect your credentials**: Keep your API token secret
2. **Use .gitignore**: Add `.env` to your `.gitignore` file
3. **Rotate tokens**: Periodically regenerate your API tokens
4. **Scope testing**: Always respect program scope and rules
5. **Authorization**: Only test on programs you're authorized to test

## Need Help?

- HackerOne Support: https://support.hackerone.com/
- Check the script's inline documentation
- Review error messages for specific issues
