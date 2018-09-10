#!/usr/bin/env python3

import argparse, itertools, pandas as pd
from ipdb import set_trace
import numpy as np


parser = argparse.ArgumentParser()
parser.add_argument('--files', help = "File names of log file", nargs = "+")
args = parser.parse_args()


def drop_and_mean(x):
    return x.mask((x.index == x.idxmax()) | (x.index == x.idxmin())).mean()



# Fields in a row
fields = { "initialize/map.pet.fillA.FromMeshAToMeshB" : "fillA",
           "initialize/map.pet.fillC.FromMeshAToMeshB" : "fillC",
           "initialize/map.pet.preallocA.FromMeshAToMeshB" : "preallocA",
           "initialize/map.pet.preallocC.FromMeshAToMeshB" : "preallocC" }

dfs = [pd.read_csv(f, parse_dates = [0], comment = "#") for f in args.files]
df = pd.concat(dfs)
df = df.reset_index()
df = df[df.Rank == 0]

df = df.groupby(["RunName", "Name"], as_index = False).aggregate(drop_and_mean)

df = df.pivot(index = "RunName", columns = "Name", values = "Total")

df = df.rename(columns = fields)

df.to_csv("data.csv", index_label = "Type", columns = fields.values())

