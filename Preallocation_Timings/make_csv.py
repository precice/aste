#!/usr/bin/env python3
""" Create suitable CSV files for pgfplots from timing output. """

import argparse, csv
import pandas as pd
from ipdb import set_trace

parser = argparse.ArgumentParser()
parser.add_argument('--file', help = "Timings file")
args = parser.parse_args()


df = pd.read_csv(args.file, comment = "#", parse_dates = [0])

# Fields in a row
fields = ["initialize/map.pet.fillA.FromMeshAToMeshB",
          "initialize/map.pet.fillC.FromMeshAToMeshB",
          "initialize/map.pet.preallocA.FromMeshAToMeshB",
          "initialize/map.pet.preallocC.FromMeshAToMeshB"]

# Labels for the rows
labels = ["off", "compute", "saved", "tree"]

with open(args.file + ".csv", 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["preallocationType"] + fields)

    for ts, prealloc in zip(df.Timestamp.unique(), labels):
        this_run = df[(df.Timestamp == ts) & (df.Rank == 0)]
        values = []
        for f in fields:
            series = this_run[this_run.Name == f].Total
            if len(series) == 0:
                values.append(0)
            else:
                values += series.tolist()

        writer.writerow([prealloc] + values)

