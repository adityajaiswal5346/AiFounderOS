"""
Script — MCP OAuth Setup Helper

Interactive script to set up OAuth2 credentials for:
- Gmail
- Google Sheets (same OAuth app)
- Slack (Bot token)
- Notion (Integration token)

Run this once to get your tokens, then add them to your .env file.

Usage:
    python scripts/setup_mcp_auth.py
    python scripts/setup_mcp_auth.py --service gmail
    python scripts/setup_mcp_auth.py --service slack
    python scripts/setup_mcp_auth.py --service notion
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


def setup_google_oauth() -> None:
    """Walk through Gmail + Sheets OAuth2 setup."""
    print("\n── Google OAuth2 (Gmail + Sheets) ─────────────────────────\n")
    print("Steps:")
    print("1. Go to: https://console.cloud.google.com/apis/credentials")
    print("2. Create OAuth 2.0 Client ID (type: Web application)")
    print("3. Add redirect URI: http://localhost:8080")
    print("4. Download the credentials JSON")
    print("5. Run the authorization flow below\n")

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow

        credentials_path = input("Path to downloaded credentials JSON: ").strip()
        if not os.path.exists(credentials_path):
            print(f"File not found: {credentials_path}")
            return

        SCOPES = [
            "https://www.googleapis.com/auth/gmail.send",
            "https://www.googleapis.com/auth/spreadsheets",
        ]

        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
        creds = flow.run_local_server(port=8080)

        print("\n✓ Authorization complete. Add these to your .env:\n")
        print(f"GMAIL_CLIENT_ID={creds.client_id}")
        print(f"GMAIL_CLIENT_SECRET={creds.client_secret}")
        print(f"GMAIL_REFRESH_TOKEN={creds.refresh_token}")
        print(f"SHEETS_CLIENT_ID={creds.client_id}")
        print(f"SHEETS_CLIENT_SECRET={creds.client_secret}")
        print(f"SHEETS_REFRESH_TOKEN={creds.refresh_token}")

    except ImportError:
        print("google-auth-oauthlib not installed. Run: pip install google-auth-oauthlib")


def setup_slack() -> None:
    """Slack Bot Token setup instructions."""
    print("\n── Slack Setup ─────────────────────────────────────────────\n")
    print("Steps:")
    print("1. Go to: https://api.slack.com/apps")
    print("2. Create New App → From scratch")
    print("3. Add these Bot Token Scopes:")
    print("   - chat:write")
    print("   - channels:read")
    print("4. Install App to your workspace")
    print("5. Copy the Bot User OAuth Token (xoxb-...)")
    print("6. Copy the Signing Secret from 'Basic Information'\n")

    bot_token = input("Bot Token (xoxb-...): ").strip()
    signing_secret = input("Signing Secret: ").strip()
    channel_id = input("Default Channel ID (C...): ").strip()

    print("\n✓ Add these to your .env:\n")
    print(f"SLACK_BOT_TOKEN={bot_token}")
    print(f"SLACK_SIGNING_SECRET={signing_secret}")
    print(f"SLACK_CHANNEL_ID={channel_id}")


def setup_notion() -> None:
    """Notion Integration token setup instructions."""
    print("\n── Notion Setup ────────────────────────────────────────────\n")
    print("Steps:")
    print("1. Go to: https://www.notion.so/my-integrations")
    print("2. New Integration → give it a name")
    print("3. Copy the Internal Integration Secret (secret_...)")
    print("4. Open your Tasks database in Notion")
    print("5. Connections → Add connection → your integration")
    print("6. Copy the database URL, e.g.:")
    print("   https://notion.so/YOUR_WORKSPACE/DATABASE_ID?v=...")
    print("   The DATABASE_ID is the UUID before the '?'\n")

    token = input("Integration Secret (secret_...): ").strip()
    db_id = input("Database ID (UUID format): ").strip()

    print("\n✓ Add these to your .env:\n")
    print(f"NOTION_API_KEY={token}")
    print(f"NOTION_DATABASE_ID={db_id}")


def setup_serpapi() -> None:
    """SerpAPI setup for Google Trends."""
    print("\n── SerpAPI (Google Trends) ─────────────────────────────────\n")
    print("1. Create a free account at: https://serpapi.com/")
    print("2. Copy your API key from the dashboard\n")
    key = input("SerpAPI Key: ").strip()
    print("\n✓ Add to your .env:\n")
    print(f"SERPAPI_KEY={key}")


SERVICE_MAP = {
    "google": setup_google_oauth,
    "gmail": setup_google_oauth,
    "sheets": setup_google_oauth,
    "slack": setup_slack,
    "notion": setup_notion,
    "serpapi": setup_serpapi,
    "trends": setup_serpapi,
}


def main(service: str | None = None) -> None:
    if service:
        fn = SERVICE_MAP.get(service.lower())
        if fn is None:
            print(f"Unknown service '{service}'. Options: {', '.join(SERVICE_MAP.keys())}")
            sys.exit(1)
        fn()
    else:
        print("AI Founder OS — MCP Auth Setup")
        print("=" * 50)
        print("Which services do you want to configure?")
        print("  1. Google (Gmail + Sheets)")
        print("  2. Slack")
        print("  3. Notion")
        print("  4. SerpAPI (Google Trends)")
        print("  5. All")

        choice = input("\nEnter number(s) separated by comma (e.g., 1,3): ").strip()
        choices = [c.strip() for c in choice.split(",")]

        services = []
        for c in choices:
            if c == "1": services.append(setup_google_oauth)
            elif c == "2": services.append(setup_slack)
            elif c == "3": services.append(setup_notion)
            elif c == "4": services.append(setup_serpapi)
            elif c == "5": services = [setup_google_oauth, setup_slack, setup_notion, setup_serpapi]; break

        for fn in services:
            fn()

    print("\n✓ Done. Copy the values above into your .env file.")
    print("  Then run: docker-compose up -d && python scripts/seed_onboarding.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Set up MCP OAuth credentials")
    parser.add_argument(
        "--service",
        type=str,
        choices=list(SERVICE_MAP.keys()),
        default=None,
        help="Specific service to set up",
    )
    args = parser.parse_args()
    main(service=args.service)
