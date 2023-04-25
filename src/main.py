import logging
from config import settings
import luigi
import tasks
import toml
import datetime

# load logging config
logging.config.dictConfig(settings.logging)


class AllReports(luigi.WrapperTask):
    month_start = luigi.DateParameter(default=datetime.date.today().replace(day=1))

    def requires(self):
        logging.info(f"Running pipeline for {self.month_start}...")
        yield tasks.FetchMonthlyClockifyTimeEntries(self.month_start)
