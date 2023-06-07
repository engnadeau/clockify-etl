import datetime
import logging

import luigi
import pandas as pd
from dateutil.relativedelta import relativedelta

from config import settings
from tasks.dataframes import (
    AllTimeEntries,
    ClientProjectTimeEntriesByMonth,
    ClientProjectSummaryByMonth,
    ClientsByMonth,
    TimeEntriesByMonth,
)
from utils import _date_range_to_months, _datetime_to_year_month

TODAY = datetime.date.today()
NUM_MONTHS = 3
START_MONTH = TODAY + relativedelta(months=-NUM_MONTHS)


class AllMonthlyClientProjectDFs(luigi.WrapperTask):
    month = luigi.MonthParameter()

    def requires(self):
        return {
            "client-projects": ClientProjectSummaryByMonth(month=self.month),
            "time-entries": TimeEntriesByMonth(month=self.month),
        }

    def run(self):
        # load client/project pairs
        df = pd.read_csv(self.input()["client-projects"].path)

        # iterate over client/project pairs
        for _, row in df.iterrows():
            client = row[settings.data.columns.client]
            project = row[settings.data.columns.project]
            yield ClientProjectTimeEntriesByMonth(
                month=self.month, client=client, project=project
            )


class AllReports(luigi.WrapperTask):
    start_month = luigi.MonthParameter(default=START_MONTH)
    end_month = luigi.MonthParameter(default=TODAY)

    def requires(self):
        logging.info(
            f"Generating reports from {_datetime_to_year_month(self.start_month)} to {_datetime_to_year_month(self.end_month)}"
        )

        # get months
        months = _date_range_to_months(start=self.start_month, end=self.end_month)

        # logging.info("Generating MonthlyClients reports...")
        yield [ClientsByMonth(month=month) for month in months]

        # logging.info("Generating MonthlyClientProjects reports...")
        yield [ClientProjectSummaryByMonth(month=month) for month in months]

        # logging.info("Generating MonthlyTimeDF reports...")
        yield [TimeEntriesByMonth(month=month) for month in months]

        # logging.info("Generating MonthlyClientProjectDF reports...")
        yield [AllMonthlyClientProjectDFs(month=month) for month in months]

        # logging.info("Generating MergeAllMonthlyTimeDFs...")
        yield AllTimeEntries(
            start_month=self.start_month, end_month=self.end_month
        )
