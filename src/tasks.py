import calendar
import datetime
import json
import logging
import math
from datetime import date
from pathlib import Path

import luigi
import pandas as pd

import clockify
from config import settings

WORKING_DIR = Path(settings.data.working_dir)


class FetchMonthlyClockifyTimeEntries(luigi.Task):
    month_start = luigi.DateParameter(default=datetime.date.today().replace(day=1))

    def output(self):
        month = self.month_start.strftime("%Y-%m")
        fname = f"{settings.data.target_fname}_{month}.json"
        path = WORKING_DIR / fname
        logging.info(f"Saving output to {path}")
        return luigi.LocalTarget(path)

    def run(self):
        logging.info(f"Fetching time entries for {self.month_start}")
        start_date = self.month_start
        _, last_day = calendar.monthrange(self.month_start.year, self.month_start.month)
        end_date = self.month_start.replace(day=last_day)
        json_data = clockify.get_timesheet_report(
            start_date=start_date,
            end_date=end_date,
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
