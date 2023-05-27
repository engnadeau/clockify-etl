import datetime
import logging
import math
from pathlib import Path
from typing import List, Union

import luigi
import pandas as pd
from slugify import slugify

from config import settings


def _build_output_path(
    components: List[str],
    extension: str,
) -> str:
    # slug components
    components = [slugify(c) for c in components]

    # build filename
    fname = "_".join(components)
    path = Path(settings.data.working_dir) / f"{fname}{extension}"  # type: ignore

    # create directory if it doesn't exist
    path.parent.mkdir(parents=True, exist_ok=True)

    return str(path.resolve())


def _datetime_to_year_month_day(
    dt: Union[datetime.datetime, luigi.DateParameter]
) -> str:
    return dt.strftime("%Y-%m-%d")  # type: ignore


def _datetime_to_year_month(dt: Union[datetime.datetime, luigi.DateParameter]) -> str:
    return dt.strftime("%Y-%m")  # type: ignore


def _time_entries_to_df(data: dict) -> pd.DataFrame:
    logging.info("Transforming time entries")
    df = pd.json_normalize(data)

    # convert date column to datetime
    df[settings.data.columns.datetime] = pd.to_datetime(
        df[settings.data.columns.datetime], utc=True
    )

    # filter columns
    df = df.filter(items=settings.data.columns.values())

    # convert duration seconds to hours
    df[settings.data.columns.duration] = df[settings.data.columns.duration] / (60 * 60)

    # round up to the nearest tenth of an hour
    df[settings.data.columns.duration] = df[settings.data.columns.duration].apply(
        lambda x: math.ceil(x * 10) / 10
    )

    logging.info(f"Found {len(df)} time entries")

    return df
