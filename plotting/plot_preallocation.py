import json, pandas, sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

publication = True

if publication:
    import plot_helper
    plot_helper.set_save_fig_params()


fields = ["PetRBF.fillA", "PetRBF.fillC", "PetRBF.preallocA", "PetRBF.preallocC"]
colors = {f : c for (f, c) in zip(fields,
                                  matplotlib.cm.get_cmap()(np.linspace(0, 1, len(fields)))) }
labels = {"PetRBF.fillA" : "Filling evaluation",
          "PetRBF.fillC" : "Filling interpolation",
          "PetRBF.preallocA" : "Preallocation evaluation",
          "PetRBF.preallocC" : "Preallocation interpolation" }

ticks_labels = {"off" : "No preallocation", 
                "compute" : "Explicitly computed",
                "saved" : "Computed and saved",
                "tree" : "Using of spatial tree" }


run_name = sys.argv[1] # like 2018-02-12T16:45:25.141337_testeins
participant = "B"
    
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
        y = cdf[(cdf.Name == f)].Avg.max()
        if np.isnan(y): y = 0 # When there is no Prealloc field
        plt.bar(x, y, bottom = y_bottom, color = colors[f], label = labels[f] if idx==0 else "")
        y_bottom += y
        
    x_locs.append(x)
    ticks.append(ticks_labels[info["preallocation"][idx]])


plt.ylabel("Time [ms]")
plt.xticks(x_locs, ticks, rotation = 20)
plt.legend()
plt.gca().yaxis.grid()


if publication:
    plot_helper.set_save_fig_params()
    # plt.gca().tick_params(axis='x', which='major', pad=15)
    plt.subplots_adjust(bottom=0.15)
    plt.savefig("preallocation_timings.pdf")
else:
    plt.show()
    
    


