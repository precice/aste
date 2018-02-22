import json, pandas, sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

from ipdb import set_trace

rank = 0
fields = ["PetRBF.fillA", "PetRBF.fillC", "PetRBF.preallocA", "PetRBF.preallocC"]
colors = {f : c for (f, c) in zip(fields,
                                  matplotlib.cm.get_cmap()(np.linspace(0, 1, len(fields)))) }
labels = {"PetRBF.fillA" : "Filling Matrix A",
          "PetRBF.fillC" : "Filling Matrix C",
          "PetRBF.preallocA" : "Preallocation Matrix A",
          "PetRBF.preallocC" : "Preallocation Matrix C" }

ticks_labels = {"off" : "No preallocation", 
                "compute" : "Explicitly computed",
                "saved" : "Computed and saved",
                "tree" : "Using of spatial tree" }


run_name = sys.argv[1] # like 2018-02-12T16:45:25.141337_testeins
participant = "B"
plot_rank = 0
    
f_timings = "{run}-{participant}.timings".format(run = run_name, participant = participant)
info = json.load(open(run_name + ".meta"))

df = pandas.read_csv(f_timings, index_col = [0], comment = "#", parse_dates = [0])

ticks = []
x_locs = []
x = -1

for idx, time in enumerate(df.index.unique()):
    x += 1
    if idx == 4: x += 0.3
    cdf = df.loc[time]
    y_bottom = 0
    for f in fields:
        y = cdf[(cdf.Name == f) & (cdf.Rank == rank)].Avg
        if len(y) == 0: y = 0
        plt.bar(x, y, bottom = y_bottom, color = colors[f], label = labels[f] if idx==0 else "")
        print("y =", int(y), " for ", f)
        y_bottom += y
        
    x_locs.append(x)
    ticks.append(ticks_labels[info["preallocations"][idx]])


plt.ylabel("Time [ms]")
plt.xticks(x_locs, ticks)
plt.legend()
plt.gca().yaxis.grid()
plt.show()
    
    


