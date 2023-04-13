import random
from collections import defaultdict

import luigi


class Streams(luigi.Task):
    """
    Faked version right now, just generates bogus data.
    """

    date = luigi.DateParameter()

    def run(self):
        """
        Generates bogus data and writes it into the :py:meth:`~.Streams.output` target.
        """
        with self.output().open("w") as output:
            for _ in range(1000):
                output.write(
                    "{} {} {}\n".format(
                        random.randint(0, 999),
                        random.randint(0, 999),
                        random.randint(0, 999),
                    )
                )

    def output(self):
        """
        Returns the target output for this task.
        In this case, a successful execution of this task will create a file in the local file system.
        :return: the target output for this task.
        :rtype: object (:py:class:`luigi.target.Target`)
        """
        return luigi.LocalTarget(self.date.strftime("data/streams_%Y_%m_%d_faked.tsv"))


class CollectTimesheet(luigi.Task):
    date_interval = luigi.DateIntervalParameter()

    def output(self):
        return luigi.LocalTarget(f"data/artist_streams_{self.date_interval}.tsv")

    def requires(self):
        return [Streams(date) for date in self.date_interval]

    def run(self):
        artist_count = defaultdict(int)

        for input in self.input():
            with input.open("r") as in_file:
                for line in in_file:
                    timestamp, artist, track = line.strip().split()
                    artist_count[artist] += 1

        with self.output().open("w") as out_file:
            for artist, count in artist_count.iteritems():
                print >> out_file, artist, count
