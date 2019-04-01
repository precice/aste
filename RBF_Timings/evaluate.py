import pandas as pd, numpy as np, matplotlib.pyplot as plt

import glob, json, os, sys
from ipdb import set_trace

def drop_and_mean(x):
    set_trace()
    if len(x) >= 5:
        print("Masking outlier.")
        return x.mask((x.index == x.idxmax()) | (x.index == x.idxmin())).mean()
    else:
        print("Less than 5 values in series, only applying mean.")
        return x.mean()


files = glob.glob(os.path.join(sys.argv[1], "*-*-B-*.json"))
print("Number of files =", len(files))

events = [("_GLOBAL", "global"),
          ("initialize/map.pet.fillA.FromMeshAToMeshB", "fillA"),
          ("initialize/map.pet.fillC.FromMeshAToMeshB", "fillC"),
          ("initialize/map.pet.preallocA.FromMeshAToMeshB", "preallocA"),
          ("initialize/map.pet.preallocC.FromMeshAToMeshB", "preallocC"),
          ("initialize/map.pet.postFill.FromMeshAToMeshB", "postFill"),
          ("initialize/map.pet.computeRescaling.FromMeshAToMeshB", "computeRescaling"),
          ("initialize/map.pet.solverInit.FromMeshAToMeshB", "solverInit"),
          ("initialize/map.pet.computeMapping.FromMeshAToMeshB", "computeMapping"),
          ("initialize/map.pet.solveConsistent.FromMeshAToMeshB", "solveConsistent"),
          ("initialize/map.pet.mapData.FromMeshAToMeshB", "mapData")]

l = []

for f in files:
    j = json.load(open(f))
    size = len(j["Ranks"])
    for rno, rdata in enumerate(j["Ranks"]):
        for ev, evname in events:
            time = rdata["Timings"][ev]["Total"]
            l.append({"File": f, "Rank" : rno, "Size" : size, "Event": evname, "Time" : time})


df = pd.DataFrame(l)

# df_means = df.groupby(["Size", "Event"]).aggregate({"Time" : drop_and_mean})

# Taking mean amoung all ranks
df_means = df.groupby(["Size", "Event"], as_index = False)["Time"].max()
# df_means = df_means.reset_index(drop = True)
df_means = pd.pivot(df_means, index = "Size", columns = "Event", values = "Time")

df_means.to_csv(sys.argv[1] + ".csv")

# df_means.plot()
# plt.show()

