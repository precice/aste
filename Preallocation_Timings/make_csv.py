import argparse, itertools, pandas as pd
from ipdb import set_trace
import numpy as np


parser = argparse.ArgumentParser()
parser.add_argument('--file', help = "File names of log file", nargs = "+")
args = parser.parse_args()


def avg_and_delete_outliers(a):
    print("Averaging series with standard deviation of", a.std())
    a = a.drop(a.idxmax())
    a = a.drop(a.idxmin())
    return a.mean()

# Fields in a row
fields = ["initialize/map.pet.fillA.FromMeshAToMeshB",
          "initialize/map.pet.fillC.FromMeshAToMeshB",
          "initialize/map.pet.preallocA.FromMeshAToMeshB",
          "initialize/map.pet.preallocC.FromMeshAToMeshB"]

fieldNames = ["fillA", "fillC", "preallocA", "preallocC"]
# Translates long fields to shorter fieldNames in output
translator = dict(zip(fields, fieldNames))

# Labels for the rows
labels = ["off", "computed", "saved", "tree"]

dfs = [pd.read_csv(f, parse_dates = [0], comment = "#") for f in args.file]
df = pd.concat(dfs, keys = args.file, names = ["File"])
df = df[df.Rank == 0]

# Add empty column
df["Preallocation"] = ""

groups = df.groupby("Timestamp")

for grouping, label in zip(groups, itertools.cycle(labels)):
    name = grouping[0]
    df.loc[df.Timestamp == name, "Preallocation"] = label


output = pd.DataFrame(index = labels)
    
for name, group in df.groupby(["Preallocation", "Name"]):#
    if name[1] in fields:
        output.loc[name] = avg_and_delete_outliers(group.Total)


output = output.fillna(0)
output = output.rename(translator, axis = "columns")
output.to_csv("data.csv", index_label = "Type")
print(output)
