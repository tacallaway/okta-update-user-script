#!/usr/bin/env python3
"""
Remove users from an Okta group based on a CSV file of email addresses.

Usage:
    python okta_remove_from_group.py --file emails.csv --group-id 00g1234567890abcdef

Environment variables:
    OKTA_DOMAIN    - Your Okta domain (e.g. https://yourorg.okta.com)
    OKTA_API_TOKEN - Your Okta API token

The CSV file should contain one email address per line with no header row.
"""

import argparse
import csv
import os
import sys

import requests


def load_emails_from_csv(file_path: str) -> list[str]:
    """Read email addresses from a headerless CSV file (one email per line)."""
    emails = []
    with open(file_path, newline="") as f:
        reader = csv.reader(f)
        for row_num, row in enumerate(reader, start=1):
            if not row:
                continue
            email = row[0].strip()
            if not email:
                print(f"Warning: Skipping empty row {row_num}.")
                continue
            emails.append(email)
    return emails


def get_user_id_by_email(domain: str, headers: dict, email: str) -> str | None:
    """Look up an Okta user ID by email address."""
    url = f"{domain}/api/v1/users/{email}"
    resp = requests.get(url, headers=headers, timeout=30)

    if resp.status_code == 200:
        return resp.json()["id"]

    if resp.status_code == 404:
        print(f"  NOT FOUND: {email}")
    else:
        print(f"  LOOKUP FAILED ({resp.status_code}): {email} — {resp.text}")
    return None


def remove_user_from_group(domain: str, headers: dict, group_id: str,
                           user_id: str, email: str) -> bool:
    """Remove a single user from an Okta group."""
    url = f"{domain}/api/v1/groups/{group_id}/users/{user_id}"
    resp = requests.delete(url, headers=headers, timeout=30)

    if resp.status_code == 204:
        print(f"  Removed from group: {email}")
        return True

    print(f"  FAILED ({resp.status_code}): {email} — {resp.text}")
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Remove users from an Okta group using a CSV of email addresses."
    )
    parser.add_argument(
        "--file", required=True, help="Path to a CSV file with one email per line (no header)."
    )
    parser.add_argument(
        "--group-id", required=True, help="Okta group ID to remove users from."
    )
    args = parser.parse_args()

    domain = os.environ.get("OKTA_DOMAIN", "").rstrip("/")
    api_token = os.environ.get("OKTA_API_TOKEN", "")

    if not domain or not api_token:
        print("Error: Set OKTA_DOMAIN and OKTA_API_TOKEN environment variables.")
        sys.exit(1)

    emails = load_emails_from_csv(args.file)
    if not emails:
        print("No valid email addresses found in the CSV file.")
        sys.exit(1)

    headers = {
        "Authorization": f"SSWS {api_token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    print(f"Removing {len(emails)} user(s) from group {args.group_id} in Okta ({domain}) …\n")

    success = 0
    failed = 0
    for email in emails:
        user_id = get_user_id_by_email(domain, headers, email)
        if not user_id:
            failed += 1
            continue
        if remove_user_from_group(domain, headers, args.group_id, user_id, email):
            success += 1
        else:
            failed += 1

    print(f"\nDone. {success} removed, {failed} failed.")


if __name__ == "__main__":
    main()
