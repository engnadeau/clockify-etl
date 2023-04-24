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


class ClockifyTimeEntries(luigi.Task):
    date_interval = luigi.DateIntervalParameter()

    def output(self):
        # fname = f"{settings.data.target_fname}_{self.date_interval.start}-{self.date_interval.end}.json"
        fname = f"{settings.data.target_fname}.json"
        path = WORKING_DIR / fname
        logging.info(f"Saving output to {path}")
        return luigi.LocalTarget(path)

    def run(self):
        json_data = clockify.get_timesheet_report(
            start_date=str(self.date_interval.start),
            end_date=str(self.date_interval.end),
        )

        with self.output().open("w") as outfile:
            json.dump(json_data, outfile)


class TimeEntriesToDataFrame(luigi.Task):
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
