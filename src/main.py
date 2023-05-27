import logging
import logging.config

import luigi

import tasks
from config import settings


def main():
    luigi.build(
        [
            tasks.AllReports(),
        ],
        local_scheduler=True,
        logging_conf_file=settings.logging.file_config,  # type: ignore
    )


if __name__ == "__main__":
    logging.config.fileConfig(settings.logging.file_config)  # type: ignore
    main()
