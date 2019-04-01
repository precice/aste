#!env python3
import contextlib, datetime, multiprocessing, os, time, subprocess, sys, socket, json
from pathlib import Path
from shutil import copy

import numpy as np

# try:
    # from ipdb import set_trace
# except ImportError:
    # from pdb import set_trace


def get_mpi_cmd(platform):
    if platform == "hazelhen":
        return "aprun -p fl_domain"
    elif platform == "supermuc":
        return "mpiexec"
    elif platform == "mpich-opt":
        return "/opt/mpich/bin/mpiexec --prepend-rank"
    elif platform == "mpich":
        return "mpiexec.mpich"
    else:
        return "mpiexec"

def generate_test_sizes(mpisize, platform):
    node_numbers = [1, 2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24, 28, 32, 40, 48, 56, 64, 72, 80, 88, 96,
                    104, 112, 128,  144, 160, 176, 192, 208, 224, 240, 256, 272, 288, 304]
    if platform == "hazelhen":
        # Hazelhen node size is 24, only one mpi job per node.
        sizes = [24*i for i in node_numbers]
    elif platform == "supermuc":
        sizes = [28*i for i in node_numbers]
    else:
        sizes = range(2, mpisize+1)

    return [i for i in sizes if i <= mpisize]



def removeEventFiles(participant):
    p = Path(participant)
    try:
        Path(p / ("precice-%s-events.json" % participant)).unlink()
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
    mesh = "../outmesh" if participant == "A" else "../inmesh"
    os.chdir(participant)
    
    cmd = [mpirun, "-n", ranks, "../../build/preciceMap",
           "--precice-config", "../precice.xml",
           "--mesh", mesh,
           "--participant", participant]

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
    cmd = "../build/make_mesh.py --nx {0} --ny {0} mesh".format(size)
    subprocess.run(cmd, shell = True, check = True)
    
def partitionMesh(partitions, outname):
    cmd = "../build/partition_mesh.py --algorithm uniform --numparts {} --out {} mesh.txt".format(partitions, outname)
    subprocess.run(cmd, shell = True, check = True)


def doScaling(name, ranksA, ranksB, mesh_sizes, ms, preallocations):
    assert(len(ranksA) == len(ranksB) == len(mesh_sizes) == len(ms) == len(preallocations))

    removeEventFiles("A")
    removeEventFiles("B")

    file_info = { "date" : datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                  "name" : name,
                  "meshMin": min(mesh_sizes), "meshMax": min(mesh_sizes)}
    
    file_pattern = "{date}-{name}-{participant}-ranks{ranks}.{suffix}"
    
    for rankA, rankB, mesh_size, m, preallocation in zip(ranksA, ranksB, mesh_sizes, ms, preallocations):
        print("Running on ranks = {}/{}, mesh size = {}, m = {}".format(rankA, rankB, mesh_size, m))
        file_info["ranks"] = rankB
        createMesh(mesh_size)
        partitionMesh(rankA, "outmesh")
        partitionMesh(rankB, "inmesh")
        prepareConfigTemplate(shape_parameter(mesh_size, m), preallocation)
        launchRun(rankA, rankB,
                  file_pattern.format(suffix = "out", participant = "A", **file_info),
                  file_pattern.format(suffix = "out", participant = "B", **file_info))                  

    
        copy("A/precice-A-events.json", file_pattern.format(suffix = "json", participant = "A", **file_info))
        copy("B/precice-B-events.json", file_pattern.format(suffix = "json", participant = "B", **file_info))

    with open("{date}-{name}.meta".format(**file_info), "w") as f:
        json.dump({"name"  : name,
                   "date" : file_info["date"],
                   "host" : socket.getfqdn(),
                   "ranksA" : ranksA, "ranksB" : ranksB,
                   "mesh_sizes" : mesh_sizes,
                   "m" : m,
                   "preallocation" : preallocations},
                  f, indent = 4)
                


# Global: Name of mpirun command
mpirun = ""


if __name__ == "__main__":
    max_size = 64
    platform = None

    ranks = generate_test_sizes(max_size, platform)
    mpirun = get_mpi_cmd(platform)

    print("Using MPI command:", mpirun)
    print("Running upscaling on ranks =", ranks)

    multiplicity = len(ranks)
    
    ranksA = [2] * multiplicity
    ranksB = ranks
    ms = [4] * multiplicity
    mesh_sizes = [75] * multiplicity
    preallocations = ["tree"] * multiplicity

    # preallocations = ["tree"] * len(ranksB)
    doScaling("strongscaling", ranksA, ranksB, mesh_sizes, ms, preallocations)
