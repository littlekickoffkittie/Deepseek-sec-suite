#  HackerOne API Setup Guide

This guide provides step-by-step instructions on how to obtain and configure your HackerOne API credentials for use with the DeepSeek Security Suite.

## 1. Prerequisites

- A HackerOne account. If you don't have one, you can [sign up here](https://hackerone.com/users/sign_up).

## 2. Generating an API Token

1.  **Log in** to your HackerOne account.
2.  Navigate to your **API token settings**: [https://hackerone.com/settings/api_token/edit](https://hackerone.com/settings/api_token/edit).
3.  Click the **"Create API Token"** button.
4.  Give your token a descriptive name (e.g., "DeepSeek Security Suite").
5.  You will be prompted to re-authenticate your account.
6.  Your new API token will be displayed. **Copy this token immediately** and store it in a secure location. You will not be able to see it again.

## 3. Configuring Your `.env` File

The DeepSeek Security Suite uses a `.env` file to securely store your API credentials.

1.  **Copy the example file**: In the root directory of the project, copy the `.env.example` file to a new file named `.env`.

    ```bash
    cp .env.example .env
    ```

2.  **Edit the `.env` file**: Open the newly created `.env` file in a text editor.

3.  **Add your credentials**:
    -   `DEEPSEEK_API_KEY`: Your API key from [platform.deepseek.com/api_keys](https://platform.deepseek.com/api_keys).
    -   `HACKERONE_USERNAME`: Your HackerOne username.
    -   `HACKERONE_API_TOKEN`: The API token you generated in the previous step.

    Your `.env` file should look like this:

    ```
    # DeepSeek API
    DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

    # HackerOne API (optional but recommended)
    HACKERONE_USERNAME=your_hackerone_username
    HACKERONE_API_TOKEN=your_generated_api_token
    ```

4.  **Save the file**. The application will automatically load these credentials when you run it.

## 4. Verifying Your Setup

To ensure your credentials are correct, run the security suite and select option `[0]` to fetch a program from HackerOne. If the connection is successful, your setup is complete.

## Security Reminder

-   **Never commit your `.env` file** to version control. The `.gitignore` file is already configured to prevent this.
-   **Treat your API tokens like passwords**. Do not share them publicly or store them in insecure locations.
-   **Rotate your API tokens** periodically to enhance security.
