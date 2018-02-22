import json, os, sys, pandas
import matplotlib.pyplot as plt

fields = ["PetRBF.fillA", "PetRBF.fillC", "PetRBF.preallocA", "PetRBF.preallocC"]

run_name = sys.argv[1] # like 2018-02-12T16:45:25.141337_testeins
participant = "B"
plot_rank = 0
    
f_timings = "{run}-{participant}.timings".format(run = run_name, participant = participant)
    
info = json.load(open(run_name + ".meta"))

df = pandas.read_csv(f_timings)

import ipdb; ipdb.set_trace()

for field in fields:
    plt.plot(info["ranks" + participant],
             df[(df.Name == field) & (df.Rank == plot_rank)].Avg.tolist(),
             label = field)
    

plt.grid()
plt.xlabel("Processors")
plt.ylabel("Time [ms]")

plt.legend()
plt.show()
