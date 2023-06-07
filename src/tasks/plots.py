import luigi
import pandas as pd
import plotly.express as px

from config import settings
from tasks.dataframes import AllTimeEntries


class PlotTimeEntriesByWeek(luigi.Task):
    start_month = luigi.MonthParameter()
    end_month = luigi.MonthParameter()

    def requires(self):
        return AllTimeEntries(start_month=self.start_month, end_month=self.end_month)

    def output(self):
        return luigi.LocalTarget("build/plot.html")

    def run(self):
        df = pd.read_csv(self.input().path)

        # Convert the timeInterval.start column to datetime
        df[settings.data.columns.datetime] = pd.to_datetime(
            df[settings.data.columns.datetime]
        )

        # Add week column to the DataFrame
        df["week"] = df[settings.data.columns.datetime].dt.isocalendar().week

        # Add year column to the DataFrame
        df["year"] = df[settings.data.columns.datetime].dt.isocalendar().year

        # Group by week and clientName, and calculate the total duration for each group
        grouped = (
            df.groupby(["year", "week", settings.data.columns.client])[
                settings.data.columns.duration
            ]
            .sum()
            .reset_index()
        )

        # Add a column for the week start date
        grouped["week_start"] = pd.to_datetime(
            grouped["year"].astype(str) + grouped["week"].astype(str) + "1",
            format="%Y%W%w",
        )

        # Create a stacked bar chart with Plotly Express
        fig = px.bar(
            grouped,
            x="week_start",
            y=settings.data.columns.duration,
            color=settings.data.columns.client,
            title="Weekly Duration by Client",
            labels={"timeInterval.duration": "Duration (Hours)"},
        )
        fig.update_layout(barmode="stack")

        # Create HTML file
        fig.write_html(self.output().path)
