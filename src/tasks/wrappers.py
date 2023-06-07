import datetime
import logging

import luigi
import pandas as pd
from dateutil.relativedelta import relativedelta

from config import settings
from tasks.dataframes import (
    MergeAllMonthlyTimeDFs,
    MonthlyClientProjectDF,
    MonthlyClientProjects,
    MonthlyClients,
    MonthlyTimeDF,
)
from utils import _date_range_to_months, _datetime_to_year_month

TODAY = datetime.date.today()
NUM_MONTHS = 3
START_MONTH = TODAY + relativedelta(months=-NUM_MONTHS)


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
    end_month = luigi.MonthParameter(default=TODAY)

    def requires(self):
        logging.info(
            f"Generating reports from {_datetime_to_year_month(self.start_month)} to {_datetime_to_year_month(self.end_month)}"
        )

        # get months
        months = _date_range_to_months(start=self.start_month, end=self.end_month)

        # logging.info("Generating MonthlyClients reports...")
        yield [MonthlyClients(month=month) for month in months]

        # logging.info("Generating MonthlyClientProjects reports...")
        yield [MonthlyClientProjects(month=month) for month in months]

        # logging.info("Generating MonthlyTimeDF reports...")
        yield [MonthlyTimeDF(month=month) for month in months]

        # logging.info("Generating MonthlyClientProjectDF reports...")
        yield [AllMonthlyClientProjectDFs(month=month) for month in months]

        # logging.info("Generating MergeAllMonthlyTimeDFs...")
        yield MergeAllMonthlyTimeDFs(
            start_month=self.start_month, end_month=self.end_month
        )
