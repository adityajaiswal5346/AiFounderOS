"""
MCP Client — Google Sheets

Read and write operations on Google Sheets via the Sheets API.
Used by the Sales Agent for CRM pipeline management.
"""

from __future__ import annotations

import logging
import os
from typing import Any

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_credentials() -> Credentials:
    creds = Credentials(
        token=None,
        refresh_token=os.environ["SHEETS_REFRESH_TOKEN"],
        client_id=os.environ["SHEETS_CLIENT_ID"],
        client_secret=os.environ["SHEETS_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    if creds.expired or not creds.valid:
        creds.refresh(Request())
    return creds


def _get_service():
    return build("sheets", "v4", credentials=_get_credentials())


async def read_sheet(
    sheet_name: str,
    spreadsheet_id: str | None = None,
    range_suffix: str = "!A:Z",
) -> list[list[Any]]:
    """
    Read all rows from a named sheet.

    Args:
        sheet_name: Tab name within the spreadsheet
        spreadsheet_id: Override the default SHEETS_SPREADSHEET_ID env var
        range_suffix: A1 notation suffix (default reads all columns)

    Returns:
        2D list of values (first row is headers)
    """
    spreadsheet_id = spreadsheet_id or os.environ["SHEETS_SPREADSHEET_ID"]
    range_name = f"{sheet_name}{range_suffix}"

    service = _get_service()
    result = (
        service.spreadsheets()
        .values()
        .get(spreadsheetId=spreadsheet_id, range=range_name)
        .execute()
    )
    return result.get("values", [])


async def update_sheet_row(
    sheet_name: str,
    row_id: str,
    updates: dict[str, Any],
    spreadsheet_id: str | None = None,
) -> dict:
    """
    Update specific columns in a row identified by its ID column.

    Args:
        sheet_name: Tab name
        row_id: Value in the 'ID' column to identify the row
        updates: Dict of column_name → new_value
        spreadsheet_id: Override spreadsheet ID

    Returns:
        Sheets API update response
    """
    spreadsheet_id = spreadsheet_id or os.environ["SHEETS_SPREADSHEET_ID"]
    rows = await read_sheet(sheet_name=sheet_name, spreadsheet_id=spreadsheet_id)

    if not rows:
        raise ValueError(f"Sheet '{sheet_name}' is empty")

    headers = rows[0]
    id_col = headers.index("ID") if "ID" in headers else 0

    # Find the row index
    target_row_idx = None
    for i, row in enumerate(rows[1:], start=2):  # 1-indexed, skip header
        if row[id_col] == row_id:
            target_row_idx = i
            break

    if target_row_idx is None:
        raise ValueError(f"Row with ID '{row_id}' not found in '{sheet_name}'")

    # Build update requests
    service = _get_service()
    data = []
    for col_name, value in updates.items():
        if col_name not in headers:
            logger.warning(f"Column '{col_name}' not found in sheet '{sheet_name}'")
            continue
        col_idx = headers.index(col_name)
        col_letter = chr(ord("A") + col_idx)
        data.append({
            "range": f"{sheet_name}!{col_letter}{target_row_idx}",
            "values": [[value]],
        })

    body = {"valueInputOption": "USER_ENTERED", "data": data}
    result = (
        service.spreadsheets()
        .values()
        .batchUpdate(spreadsheetId=spreadsheet_id, body=body)
        .execute()
    )
    return result
