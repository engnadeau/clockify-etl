import calendar
import datetime
import json
import logging

import luigi
import pandas as pd
from dateutil.relativedelta import relativedelta

import clockify
from config import settings
from utils import _build_output_path, _datetime_to_year_month, _time_entries_to_df

TODAY = datetime.date.today()
NUM_MONTHS = 3
START_MONTH = TODAY + relativedelta(months=-NUM_MONTHS)


class MonthlyTimeEntries(luigi.Task):
    month = luigi.MonthParameter()

    def output(self):
        return luigi.LocalTarget(
            _build_output_path(
                components=[
                    "time-entries",
                    _datetime_to_year_month(self.month),
                ],
                extension=".json",
            )
        )

    def run(self):
        # get last date of month
        last_day = calendar.monthrange(self.month.year, self.month.month)[1]  # type: ignore
        last_date = datetime.date(self.month.year, self.month.month, last_day)  # type: ignore

        # convert start and end dates to datetime objects
        start_dt = datetime.datetime.combine(self.month, datetime.time.min)  # type: ignore
        end_dt = datetime.datetime.combine(last_date, datetime.time.max)  # type: ignore

        # extract and save time entries
        logging.info(
            f"Fetching time entries for {_datetime_to_year_month(self.month)} from {start_dt} to {end_dt}"
        )
        data = clockify.get_timesheet_report(
            start_date=start_dt,
            end_date=end_dt,
        )

        # save time entries to json
        time_entries_path = self.output().path
        logging.info(f"Saving time entries to {time_entries_path}")
        with open(time_entries_path, "w") as f:
            json.dump(data, f, indent=4, sort_keys=True)


class MonthlyClients(luigi.Task):
    month = luigi.MonthParameter()

    def requires(self):
        return MonthlyTimeDF(month=self.month)

    def output(self):
        return luigi.LocalTarget(
            _build_output_path(
                components=[
                    "clients",
                    _datetime_to_year_month(self.month),
                ],
                extension=".csv",
            )
        )

    def run(self):
        # load time entries
        df = pd.read_csv(self.input().path)

        # groupby clients and total duration
        df = (
            df.groupby(settings.data.columns.client)[settings.data.columns.duration]
            .sum()
            .reset_index()
        )

        # add total row
        total_row = (
            pd.Series(
                {
                    settings.data.columns.client: "Total",
                    settings.data.columns.duration: df[
                        settings.data.columns.duration
                    ].sum(),
                }
            )
            .to_frame()
            .T
        )
        df = pd.concat(
            [
                df,
                total_row,
            ],
            ignore_index=True,
        )

        # save clients to csv
        output_path = self.output().path
        logging.info(f"Saving clients to {output_path}")
        df.to_csv(output_path, index=False)


class MonthlyTimeDF(luigi.Task):
    month = luigi.MonthParameter()

    def requires(self):
        return MonthlyTimeEntries(month=self.month)

    def output(self):
        return luigi.LocalTarget(
            _build_output_path(
                components=[
                    "time-entries",
                    _datetime_to_year_month(self.month),
                ],
                extension=".csv",
            )
        )

    def run(self):
        # load time entries
        time_entries_path = self.input().path
        logging.info(f"Loading time entries from {time_entries_path}")

        with open(time_entries_path, "r") as f:
            data = json.load(f)

        # transform time entries and save to csv
        if data["timeentries"]:
            df = _time_entries_to_df(data=data["timeentries"])
        else:
            logging.info("No time entries found")
            df = pd.DataFrame(columns=settings.data.columns.values())

        # save time entries to csv
        output_path = self.output().path
        logging.info(f"Saving time entries to {output_path}")
        df.to_csv(output_path, index=False)


class MonthlyClientProjectDF(luigi.Task):
    month = luigi.MonthParameter()
    client = luigi.Parameter()
    project = luigi.Parameter()

    def requires(self):
        return MonthlyTimeDF(month=self.month)

    def output(self):
        return luigi.LocalTarget(
            _build_output_path(
                components=[
                    self.client,
                    self.project,
                    _datetime_to_year_month(self.month),
                ],
                extension=".csv",
            )
        )

    def run(self):
        # load time entries
        time_entries_path = self.input().path
        logging.info(f"Loading time entries from {time_entries_path}")

        df = pd.read_csv(time_entries_path)

        # filter by client/project
        df = df.query(
            f"{settings.data.columns.client} == '{self.client}' and {settings.data.columns.project} == '{self.project}'"
        )

        # save client/project pairs to csv
        output_path = self.output().path
        logging.info(f"Saving client/project pairs to {output_path}")
        df.to_csv(output_path, index=False)


class MonthlyClientProjects(luigi.Task):
    month = luigi.MonthParameter()

    def requires(self):
        return MonthlyTimeDF(month=self.month)

    def output(self):
        return luigi.LocalTarget(
            _build_output_path(
                components=[
                    "client-projects",
                    _datetime_to_year_month(self.month),
                ],
                extension=".csv",
            )
        )

    def run(self):
        # load time entries
        time_entries_path = self.input().path
        logging.info(f"Loading time entries from {time_entries_path}")

        df = pd.read_csv(time_entries_path)

        # groupby client/project pairs and sum duration
        df = (
            df.groupby(
                [
                    settings.data.columns.client,
                    settings.data.columns.project,
                ]
            )[
                settings.data.columns.duration
            ]  # type: ignore
            .sum()
            .reset_index()
        )

        # save client/project pairs to csv
        output_path = self.output().path
        logging.info(f"Saving client/project pairs to {output_path}")
        df.to_csv(output_path, index=False)


class AllMonthlyClientProjectDFs(luigi.WrapperTask):
    month = luigi.MonthParameter()

    def requires(self):
        return {
            "client-projects": MonthlyClientProjects(month=self.month),
            "time-entries": MonthlyTimeDF(month=self.month),
        }

    def run(self):
        # load client/project pairs
        df = pd.read_csv(self.input()["client-projects"].path)

        # iterate over client/project pairs
        for _, row in df.iterrows():
            client = row[settings.data.columns.client]
            project = row[settings.data.columns.project]
            yield MonthlyClientProjectDF(
                month=self.month, client=client, project=project
            )


class AllReports(luigi.WrapperTask):
    start_month = luigi.MonthParameter(default=START_MONTH)

    def requires(self):
        logging.info(
            f"Generating reports from {_datetime_to_year_month(self.start_month)} to {_datetime_to_year_month(TODAY)}"
        )

        logging.info("Generating MonthlyClients reports...")
        yield [
            MonthlyClients(month=TODAY),
            luigi.tools.range.RangeMonthly(
                of=MonthlyClients,
                start=self.start_month,
            ),
        ]

        logging.info("Generating MonthlyClientProjects reports...")
        yield [
            MonthlyClientProjects(month=TODAY),
            luigi.tools.range.RangeMonthly(
                of=MonthlyClientProjects,
                start=self.start_month,
            ),
        ]

        logging.info("Generating MonthlyTimeDF reports...")
        yield [
            MonthlyTimeDF(month=TODAY),
            luigi.tools.range.RangeMonthly(
                of=MonthlyTimeDF,
                start=self.start_month,
            ),
        ]

        logging.info("Generating MonthlyClientProjectDF reports...")
        yield [
            AllMonthlyClientProjectDFs(month=TODAY),
            luigi.tools.range.RangeMonthly(
                of=AllMonthlyClientProjectDFs,
                start=self.start_month,
            ),
        ]
