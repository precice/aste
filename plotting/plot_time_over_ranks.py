import json, os, sys, pandas
import matplotlib.pyplot as plt
from ipdb import set_trace

fields = ["PetRBF.fillA", "PetRBF.fillC", "PetRBF.preallocA", "PetRBF.preallocC"]

labels = {"_GLOBAL" : "Total",
          "PetRBF.fillA" : "Filling evaluation",
          "PetRBF.fillC" : "Filling interpolation",
          "PetRBF.preallocA" : "Preallocation evaluation",
          "PetRBF.preallocC" : "Preallocation interpolation" }


run_name = sys.argv[1] # like 2018-02-12T16:45:25.141337_testeins
participant = "B"
    
f_timings = "{run}-{participant}.timings".format(run = run_name, participant = participant)
    
info = json.load(open(run_name + ".meta"))

df = pandas.read_csv(f_timings, comment = "#")

for field in fields:
    ys = []
    for ts in df["Timestamp"].unique():
        ys.append( df[(df.Timestamp == ts) & (df.Name == field)].Avg.max() ) # Find the maximum time across all ranks
        
    plt.plot(info["ranks" + participant], ys, label = labels[field])
    

plt.grid()
plt.xlabel("Processors")
plt.ylabel("Time [ms]")

plt.legend()
plt.show()
