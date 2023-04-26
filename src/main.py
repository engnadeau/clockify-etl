import logging
from config import settings
import luigi
import tasks
import toml
import datetime

logging.config.dictConfig(settings.logging)


class AllReports(luigi.WrapperTask):
    date = luigi.DateParameter(default=datetime.date.today())

    def requires(self):
        yield tasks.FetchDailyTimeEntries(self.date)
