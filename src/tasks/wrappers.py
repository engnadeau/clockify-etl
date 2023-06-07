import datetime
from dateutil.relativedelta import relativedelta
from config import settings
import pandas as pd
from tasks.dataframes import (
    MonthlyClientProjectDF,
    MonthlyClientProjects,
    MonthlyClients,
    MonthlyTimeDF,
)
from utils import _datetime_to_year_month


import luigi


import logging

NUM_MONTHS = 3
TODAY = datetime.date.today()
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
