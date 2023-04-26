import calendar
import json
import logging
import math
import datetime
from pathlib import Path

import luigi
import pandas as pd

import clockify
from config import settings

WORKING_DIR = Path(settings.data.working_dir)


class FetchDailyTimeEntries(luigi.Task):
    date = luigi.DateParameter(default=datetime.date.today())

    def output(self):
        fname = f"{settings.data.timeentries_prefix}_{self.date}.json"
        path = WORKING_DIR / settings.data.timeentries_prefix / fname
        return luigi.LocalTarget(path)

    def run(self):
        logging.info(f"Fetching time entries for {self.date}")
        start = datetime.datetime.combine(self.date, datetime.time.min)
        end = datetime.datetime.combine(self.date, datetime.time.max)
        json_data = clockify.get_timesheet_report(
            start=start,
            end=end,
        )

        local_target = self.output()
        logging.info(f"Saving time entries to {local_target.path}")
        with local_target.open("w") as outfile:
            json.dump(json_data, outfile, indent=4, sort_keys=True)


class ConvertTimeEntriesToDataFrame(luigi.Task):
    time_entries = luigi.Parameter()

    def output(self):
        return luigi.LocalTarget(self.time_entries.replace(".json", ".csv"))

    def run(self):
        # read the JSON file into a pandas dataframe
        df = pd.read_json(self.time_entries)

        # save the dataframe to a CSV file
        df.to_csv(self.output().path, index=False)

        # convert to pandas dataframe
        df = pd.json_normalize(self.time_entries)
        df = df.filter(
            items=[
                "description",
                "userName",
                "projectName",
                "clientName",
                "timeInterval.start",
                "timeInterval.duration",
            ]
        )

        # convert duration seconds to hours
        df["timeInterval.duration"] = df["timeInterval.duration"] / (60 * 60)

        # round up to the nearest tenth of an hour
        df["timeInterval.rounded"] = df["timeInterval.duration"].apply(
            lambda x: math.ceil(x * 10) / 10
        )

        df.to_csv(self.output(), index=False)
