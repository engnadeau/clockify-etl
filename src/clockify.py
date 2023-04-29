import logging
from datetime import datetime

import requests

from config import settings

HEADERS = {"X-Api-Key": settings.clockify.api_key}
CLOCKIFY_DATE_FMT = "%Y-%m-%dT%H:%M:%SZ"


def get_timesheet_report(start_date: datetime, end_date: datetime):
    logging.info(f"Getting timesheet report from {start_date} to {end_date}...")
    start_date = start_date.strftime(CLOCKIFY_DATE_FMT)
    end_date = end_date.strftime(CLOCKIFY_DATE_FMT)

    # Set up the API request
    url = f"https://reports.api.clockify.me/v1/workspaces/{settings.clockify.workspace_id}/reports/detailed"
    payload = {
        "dateRangeStart": start_date,
        "dateRangeEnd": end_date,
        "dateFormat": "YYYY-MM-DD",
        "detailedFilter": {"pageSize": 1000},
    }

    # Send the API request and handle the response
    response = requests.post(url, headers=HEADERS, json=payload)
    logging.info(f"Query URL: {response.url}")
    response.raise_for_status()

    # extract timeentries
    return response.json()


def get_user_info():
    logging.info("Getting user info...")
    url = "https://api.clockify.me/api/v1/user"
    response = requests.get(
        url,
        headers=HEADERS,
    )
    response.raise_for_status()
    return response.json()


def get_user_id():
    logging.info("Getting user ID...")
    return get_user_info()["id"]
