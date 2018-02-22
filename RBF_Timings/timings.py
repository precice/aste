#!env python3
import contextlib, datetime, multiprocessing, os, time, subprocess, sys, socket, json
from pathlib import Path

import numpy as np

try:
    from ipdb import set_trace
except ImportError:
    from pdb import set_trace



def removeEventFiles(participant):
    p = Path(participant)
    try:
        Path(p / ("Events-%s.log" % participant)).unlink()
        Path(p / ("EventTimings-%s.log" % participant)).unlink()
    except FileNotFoundError:
        pass
        

def shape_parameter(mesh_size, m):
    """ Computes the shape parameter for Gaussians for a given m and mesh size. """
    h = 1 / mesh_size
    s = np.sqrt(- np.log(1e-9)) / (m * h)
    print("################## mesh_size =", mesh_size, ', m =', m, ", h =", h, ", s =", s, "##################")
    return s

def launchSingleRun(participant, ranks, outfile = None):
    ostream = open(outfile, "a") if outfile else sys.stdout
    mesh = "../outMesh.txt" if participant == "A" else "../inMesh.txt"
    os.chdir(participant)
    
    cmd = [mpirun, "-n", ranks, "../../readMesh", "-a", "-c", "../precice.xml", mesh, participant]
    with contextlib.redirect_stdout(ostream):
        cp = subprocess.run(cmd, stdout = sys.stdout, stderr = subprocess.STDOUT, check = True)
    

def launchRun(rankA, rankB, outFileA = None, outFileB = None):
    pA = multiprocessing.Process(target=launchSingleRun, daemon=True, args=("A", str(rankA), outFileA))
    pB = multiprocessing.Process(target=launchSingleRun, daemon=True, args=("B", str(rankB), outFileB))
    pA.start(); pB.start()
    pA.join();  pB.join()
    if (pA.exitcode != 0) or (pB.exitcode != 0):
        raise Exception
    
    
def prepareConfigTemplate(shape_parameter, preallocation):
    print("Prepare config template: preallocation =", preallocation, ", shape parameter =", shape_parameter)
    with open("precice.xml.template") as f:
        template = f.read()
    with open("precice.xml", "w") as f:
        f.write(template.format(shape_parameter = shape_parameter, preallocation = preallocation))

        
def createMesh(size):
    cmd = "../make_mesh.py {0} {0}".format(size)
    subprocess.run(cmd, shell = True, check = True)


def doScaling(name, ranksA, ranksB, mesh_sizes, ms, preallocations):
    assert(len(ranksA) == len(ranksB) == len(mesh_sizes) == len(ms) == len(preallocations))

    removeEventFiles("A")
    removeEventFiles("B")

    file_info = { "date" : datetime.datetime.now().isoformat(),
                  "name" : name,
                  "meshMin": min(mesh_sizes), "meshMax": min(mesh_sizes)}
    
    file_pattern = "{date}-{name}-{participant}.{suffix}"
    
    for rankA, rankB, mesh_size, m, preallocation in zip(ranksA, ranksB, mesh_sizes, ms, preallocations):
        print("Running on ranks = {}/{}, mesh size = {}, m = {}".format(rankA, rankB, mesh_size, m))
        createMesh(mesh_size)
        prepareConfigTemplate(shape_parameter(mesh_size, m), preallocation)
        launchRun(rankA, rankB,
                  file_pattern.format(suffix = "out", participant = "A", **file_info),
                  file_pattern.format(suffix = "out", participant = "B", **file_info))                  

    
    Path("A" / Path("Events-A.log")).rename(file_pattern.format(suffix = "events", participant = "A",
                                                                **file_info))
    Path("A" / Path("EventTimings-A.log")).rename(file_pattern.format(suffix= "timings", participant = "A",
                                                                      **file_info))        
    Path("B" / Path("Events-B.log")).rename(file_pattern.format(suffix = "events", participant = "B",
                                                                **file_info))
    Path("B" / Path("EventTimings-B.log")).rename(file_pattern.format(suffix= "timings", participant = "B",
                                                                      **file_info))

    with open("{date}-{name}.meta".format(**file_info), "w") as f:
        json.dump({"name"  : name, "date" : file_info["date"], "host" : socket.getfqdn(),
                   "ranksA" : ranksA, "ranksB" : ranksB,
                   "mesh_sizes" : mesh_sizes, "m" : m,
                   "preallocation" : preallocations},
                  f)
                


ppn = 24 # Processors per nodes, 24 for hazelhen, 28 for supermuc

# mpirun = "aprun" # for HazelHen
mpirun = "mpirun" # for SuperMUC and anywhere else

# nodes = 3
# ranksB = [(nodes-1)*ppn]
# ranksA = [ppn] * len(ranksB)
# mesh_sizes = [150] * len(ranksA)


mesh_sizes = [50] * 4 + [60] * 4
preallocations = ["off", "compute", "saved", "tree"] * 2 # tree, saved, estimate, compute, off
ranksA = [2] * 8
ranksB = [4] * 8
ms = [6] * 8


# preallocations = ["off", "compute", "saved", "tree"]
preallocations = ["tree"] * len(ranksB)
ms = [6] * len(ranksB)
doScaling("prealloc", ranksA, ranksB, mesh_sizes, ms, preallocations)
