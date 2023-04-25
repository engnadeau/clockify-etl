import json
import logging
from datetime import datetime

import requests

from config import settings


HEADERS = {"X-Api-Key": settings.clockify.api_key}


def get_timesheet_report(start_date: datetime.date, end_date: datetime.date):
    logging.info(f"Getting timesheet report from {start_date} to {end_date}...")
    start_date = start_date.strftime(settings.clockify.datetime_fmt)
    end_date = end_date.strftime(settings.clockify.datetime_fmt)

    # Set up the API request
    url = f"https://reports.api.clockify.me/v1/workspaces/{settings.clockify.workspace_id}/reports/detailed"
    payload = {
        "dateRangeStart": start_date,
        "dateRangeEnd": end_date,
        "dateFormat": "YYYY-MM-DD",
        "detailedFilter": {"groups": ["PROJECT", "TASK"]},
        "exportType": "JSON",
    }

    # Send the API request and handle the response
    response = requests.post(url, headers=HEADERS, json=payload)
    response.raise_for_status()

    # extract timeentries
    return response.json()["timeentries"]


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
