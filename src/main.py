import datetime
import json
import logging
import logging.config
import math
from pathlib import Path
from typing import List

import fire
import pandas as pd
from slugify import slugify

import clockify
from config import settings


def _build_output_path(
    name_components: List[str],
    date_components: List[datetime.datetime],
    extension: str,
) -> str:
    # build filename
    date_interval = "-".join([x.strftime("%Y-%m-%d") for x in date_components])
    name_components.append(date_interval)
    fname = "_".join(name_components)
    path = Path(settings.data.working_dir) / f"{fname}{extension}"

    # create directory if it doesn't exist
    path.parent.mkdir(parents=True, exist_ok=True)

    return path


def main(start_date: str, end_date: str):
    # convert start and end dates to datetime objects
    start_dt = datetime.datetime.combine(
        datetime.date.fromisoformat(start_date), datetime.time.min
    )
    end_dt = datetime.datetime.combine(
        datetime.date.fromisoformat(end_date), datetime.time.max
    )

    # extract and save time entries
    logging.info(f"Fetching time entries for {start_dt} to {end_dt}")
    data = clockify.get_timesheet_report(
        start_date=start_dt,
        end_date=end_dt,
    )

    time_entries_path = _build_output_path(
        name_components=["time-entries"],
        date_components=[start_dt, end_dt],
        extension=".json",
    )

    logging.info(f"Saving time entries to {time_entries_path}")
    with open(time_entries_path, "w") as outfile:
        json.dump(data, outfile, indent=4, sort_keys=True)

    # transform time entries and save to csv
    df = transform_time_entries(data=data["timeentries"])
    df.to_csv(time_entries_path.with_suffix(".csv"), index=False)

    # extract and save clients
    clients = extract_clients(df=df)
    clients_path = _build_output_path(
        name_components=["clients"],
        date_components=[start_dt, end_dt],
        extension=".csv",
    )
    clients.to_csv(clients_path, index=False)

    # split time entries
    dfs = split_dataframe_by_client_project(df=df)
    dump_dataframes_by_periods(dfs=dfs)


def dump_dataframes_by_periods(dfs: List[pd.DataFrame]) -> List[pd.DataFrame]:
    # iterate over client/project dataframes
    for df in dfs:
        client = df[settings.data.client_column].iloc[0]
        project = df[settings.data.project_column].iloc[0]
        logging.info(f"Splitting periodic dataframe for: {client} / {project}")

        # split by periodic intervals
        try:
            grouped = df.groupby(pd.Grouper(key=settings.data.date_column, freq="2W"))
        except TypeError as e:
            logging.error(f"Error grouping dataframe:\n{df}")
            logging.error(f"Dataframe dtypes:\n{df.dtypes}")
            df.to_csv("error.csv", index=False)
            raise e
        for group_name, group_df in grouped:
            logging.info(f"Splitting by group: {group_name.date()}")

            # skip if group is empty
            if len(group_df) == 0:
                logging.info(f"Skipping empty group: {group_name.date()}")
                continue

            # build path
            path = _build_output_path(
                name_components=[slugify(client), slugify(project)],
                date_components=[group_name],
                extension=".csv",
            )
            logging.info(f"Saving to: {path}")
            group_df.to_csv(path, index=False)


def split_dataframe_by_client_project(df: pd.DataFrame) -> List[pd.DataFrame]:
    dfs = []
    client_projects = df[
        [settings.data.client_column, settings.data.project_column]
    ].drop_duplicates()
    for client, project in client_projects.itertuples(index=False):
        logging.info(f"Splitting dataframe by client/project: {client} / {project}")
        client_project_df = df.pipe(
            lambda x: x[x[settings.data.client_column] == client]
        ).pipe(lambda x: x[x[settings.data.project_column] == project])
        dfs.append(client_project_df)
    return dfs


def extract_clients(df: pd.DataFrame) -> pd.DataFrame:
    logging.info("Extracting clients")

    # get unique clients
    df = df[settings.data.client_column].drop_duplicates()

    logging.info(f"Found {len(df)} clients")

    return df


def transform_time_entries(data: dict) -> pd.DataFrame:
    logging.info("Transforming time entries")
    df = pd.json_normalize(data)

    # convert date column to datetime
    df[settings.data.date_column] = pd.to_datetime(
        df[settings.data.date_column], utc=True
    )

    # filter columns
    df = df.filter(items=settings.data.time_entries_columns)

    # convert duration seconds to hours
    df[settings.data.duration_column] = df[settings.data.duration_column] / (60 * 60)

    # round up to the nearest tenth of an hour
    df[settings.data.duration_column] = df[settings.data.duration_column].apply(
        lambda x: math.ceil(x * 10) / 10
    )

    logging.info(f"Found {len(df)} time entries")

    return df


if __name__ == "__main__":
    logging.config.dictConfig(settings.logging)
    fire.Fire(main)
