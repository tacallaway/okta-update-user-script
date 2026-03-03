#!/usr/bin/env python3
"""Generate a sample users.xlsx file for testing."""

import openpyxl

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Users"

ws.append(["FirstName", "LastName", "Email"])
ws.append(["Jane", "Doe", "jane.doe@example.com"])
ws.append(["John", "Smith", "john.smith@example.com"])
ws.append(["Alice", "Johnson", "alice.johnson@example.com"])

wb.save("users.xlsx")
print("Created users.xlsx")
