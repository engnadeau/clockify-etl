# clockify_etl.py
import csv
import json

import luigi
import requests
from config import settings
from pathlib import Path


class ExtractTask(luigi.Task):
    def output(self):
        return luigi.LocalTarget(
            Path(settings.working_dir) / settings.data.timesheets_target
        )

    def run(self):
        api_key = settings.clockify.CLOCKIFY_API_KEY
        workspace_id = settings.clockify.CLOCKIFY_WORKSPACE_ID
        headers = {"x-api-key": api_key}
        url = f"https://reports.api.clockify.me/v1/workspaces/{workspace_id}/reports/detailed"
        payload = {
            "dateRangeEnd": "2023-08-24T14:15:22Z",
            "dateRangeStart": "2023-04-01T14:15:22Z",
        }
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        with self.output().open("w") as output_file:
            json.dump(response.json(), output_file)


class TransformTask(luigi.Task):
    def requires(self):
        return ExtractTask()

    def output(self):
        return luigi.LocalTarget(
            Path(settings.working_dir) / settings.data.projects_target
        )

    def run(self):
        with self.input().open("r") as input_file:
            data = json.load(input_file)

        data_by_project = {}
        for entry in data:
            project_id = entry["projectId"]
            if project_id not in data_by_project:
                data_by_project[project_id] = []
            data_by_project[project_id].append(entry)

        with self.output().open("w") as output_file:
            json.dump(data_by_project, output_file)


class LoadTask(luigi.Task):
    def requires(self):
        return TransformTask()

    def run(self):
        with self.input().open("r") as input_file:
            data_by_project = json.load(input_file)

        for project_id, entries in data_by_project.items():
            with open(
                f"project_{project_id}_timesheet.csv", "w", newline=""
            ) as csvfile:
                fieldnames = ["id", "start", "end", "duration", "description"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for entry in entries:
                    writer.writerow(
                        {
                            "id": entry["id"],
                            "start": entry["timeInterval"]["start"],
                            "end": entry["timeInterval"]["end"],
                            "duration": entry["timeInterval"]["duration"],
                            "description": entry["description"],
                        }
                    )


def test_connection():
    api_key = settings.clockify.CLOCKIFY_API_KEY
    workspace_id = settings.clockify.CLOCKIFY_WORKSPACE_ID
    headers = {"x-api-key": api_key}
    url = "https://api.clockify.me/api/v1/user"

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


if __name__ == "__main__":
    # test_connection()
    luigi.build([LoadTask()], local_scheduler=True)
