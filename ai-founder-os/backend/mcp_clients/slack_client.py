"""
MCP Client — Slack

Send messages to Slack channels via the Slack Web API.
Used by the Operations Agent (with approval gate for announcements).
"""

from __future__ import annotations

import logging
import os
from typing import Any

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


def _get_client() -> AsyncWebClient:
    return AsyncWebClient(token=os.environ["SLACK_BOT_TOKEN"])


async def send_slack_message(
    channel: str,
    message: str,
    blocks: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Send a message to a Slack channel.

    Args:
        channel: Channel name (with or without #) or channel ID
        message: Plain text fallback message
        blocks: Optional Block Kit blocks for rich formatting

    Returns:
        Slack API response dict

    Raises:
        SlackApiError: If the API call fails
    """
    client = _get_client()

    # Normalize channel name
    if channel and not channel.startswith("#") and not channel.startswith("C"):
        channel = f"#{channel}"

    try:
        kwargs: dict[str, Any] = {
            "channel": channel,
            "text": message,
        }
        if blocks:
            kwargs["blocks"] = blocks

        response = await client.chat_postMessage(**kwargs)
        logger.info(f"Sent Slack message to {channel} (ts: {response['ts']})")
        return dict(response.data)
    except SlackApiError as e:
        logger.error(f"Slack API error for channel {channel}: {e.response['error']}")
        raise


async def get_channel_id(channel_name: str) -> str | None:
    """
    Resolve a channel name to its ID.

    Args:
        channel_name: Channel name without # prefix

    Returns:
        Channel ID string or None if not found
    """
    client = _get_client()

    try:
        response = await client.conversations_list(types="public_channel,private_channel")
        for ch in response.get("channels", []):
            if ch["name"] == channel_name.lstrip("#"):
                return ch["id"]
        return None
    except SlackApiError as e:
        logger.error(f"Failed to list Slack channels: {e.response['error']}")
        raise
