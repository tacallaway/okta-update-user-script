#!/usr/bin/env python3
"""
Bulk import users from an Excel spreadsheet into Okta in a staged state
(no activation email sent).

Usage:
    python okta_bulk_import.py --file users.xlsx

Environment variables:
    OKTA_DOMAIN  - Your Okta domain (e.g. https://yourorg.okta.com)
    OKTA_API_TOKEN - Your Okta API token

The Excel file should have the following columns (first row is the header):
    First Name | Last Name | Email
"""

import argparse
import os
import sys

import openpyxl
import requests


def load_users_from_excel(file_path: str) -> list[dict]:
    """Read users from an Excel file. Expects columns: First Name, Last Name, Email."""
    wb = openpyxl.load_workbook(file_path, read_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        print("Error: The spreadsheet is empty.")
        sys.exit(1)

    header = [str(cell).strip().lower() if cell else "" for cell in rows[0]]

    required = {"first name", "last name", "email"}
    if not required.issubset(set(header)):
        print(f"Error: Missing required columns. Found: {header}")
        print(f"Required: {required}")
        sys.exit(1)

    first_idx = header.index("first name")
    last_idx = header.index("last name")
    email_idx = header.index("email")

    users = []
    for row_num, row in enumerate(rows[1:], start=2):
        first = str(row[first_idx]).strip() if row[first_idx] else ""
        last = str(row[last_idx]).strip() if row[last_idx] else ""
        email = str(row[email_idx]).strip() if row[email_idx] else ""

        if not email:
            print(f"Warning: Skipping row {row_num} — missing email.")
            continue

        users.append({"firstName": first, "lastName": last, "email": email})

    return users


def create_okta_user(domain: str, api_token: str, user: dict) -> bool:
    """Create a single user in Okta in the STAGED state (no activation email)."""
    url = f"{domain}/api/v1/users?activate=false"
    headers = {
        "Authorization": f"SSWS {api_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "profile": {
            "firstName": user["firstName"],
            "lastName": user["lastName"],
            "email": user["email"],
            "login": user["email"],
        },
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=30)

    if resp.status_code == 200:
        print(f"  Created (staged): {user['email']}")
        return True

    print(f"  FAILED ({resp.status_code}): {user['email']} — {resp.text}")
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Bulk import users from an Excel file into Okta (staged, no activation email)."
    )
    parser.add_argument(
        "--file", required=True, help="Path to the Excel (.xlsx) file."
    )
    args = parser.parse_args()

    domain = os.environ.get("OKTA_DOMAIN", "").rstrip("/")
    api_token = os.environ.get("OKTA_API_TOKEN", "")

    if not domain or not api_token:
        print("Error: Set OKTA_DOMAIN and OKTA_API_TOKEN environment variables.")
        sys.exit(1)

    users = load_users_from_excel(args.file)
    if not users:
        print("No valid users found in the spreadsheet.")
        sys.exit(1)

    print(f"Importing {len(users)} user(s) into Okta ({domain}) …\n")

    success = 0
    failed = 0
    for user in users:
        if create_okta_user(domain, api_token, user):
            success += 1
        else:
            failed += 1

    print(f"\nDone. {success} created, {failed} failed.")


if __name__ == "__main__":
    main()
