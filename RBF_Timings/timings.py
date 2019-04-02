#!env python3
import argparse, contextlib, datetime, multiprocessing, os, time, subprocess, sys, socket, json
from pathlib import Path
from shutil import copy
import numpy as np

# try:
    # from ipdb import set_trace
# except ImportError:
    # from pdb import set_trace

def get_mpi_cmd(platform):
    if platform == "hazelhen":
        return "aprun"
    elif platform == "supermuc":
        return "mpiexec"
    elif platform == "mpich-opt":
        return "/opt/mpich/bin/mpiexec --prepend-rank"
    elif platform == "mpich":
        return "mpiexec.mpich"
    else:
        return "mpiexec"

def split_file(inputfile, lines1, lines2, output1, output2):
    """ Split inputfile in two files, each containing linesN lines. Used for MPI machine files."""
    with open(inputfile) as f:
        lines = f.readlines()

    with open(output1, "w") as f:
        for i in range(0, lines1):
            f.write(lines[i])

    with open(output2, "w") as f:
        for i in range(lines1, lines1 + lines2):
            f.write(lines[i])
    
def get_machine_file(platform, sizeA, sizeB, inputfile):
    if platform == "supermuc":
        split_file(inputfile, sizeA, sizeB, "mfile.A", "mfile.B")
        return "-f mfile.A", "-f mfile.B"
    else:
        return ["", ""]
    

def get_platform_node_size(platform):
    if platform == "hazelhen":
        return 24
    elif platform == "supermuc":
        return 28
    else:
        return 2

def get_platform_network_interface(platform):
    if platform == "hazelhen":
        return "ipogif0"
    elif platform == "supermuc":
        return "ib0"
    else:
        return "lo"
    

def generate_test_sizes(mpisize, platform):
    node_numbers = [1, 2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 24, 28, 32, 40, 48, 56, 64, 72, 80, 88, 96,
                    104, 112, 128,  144, 160, 176, 192, 208, 224, 240, 256, 272, 288, 304]
    if platform == "hazelhen" or platform == "supermuc":
        sizes = [get_platform_node_size(platform)*i for i in node_numbers]
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

def launchSingleRun(cmd ,participant,  outfile = None):
    ostream = open(outfile, "a") if outfile else sys.stdout
    # mesh = "../outmesh" if participant == "A" else "../inmesh"
    os.chdir(participant)
    
    # cmd = [mpirun, "-n", ranks, "../../build/preciceMap",
           # "--precice-config", "../precice.xml",
           # "--mesh", mesh,
           # "--participant", participant]

    with contextlib.redirect_stdout(ostream):
        cp = subprocess.run(cmd, shell = True, stdout = sys.stdout, stderr = subprocess.STDOUT, check = True)
    

def launchRun(cmdA, cmdB, outFileA = None, outFileB = None):
    pA = multiprocessing.Process(target=launchSingleRun, daemon=True, args=(cmdA, "A", outFileA))
    pB = multiprocessing.Process(target=launchSingleRun, daemon=True, args=(cmdB, "B", outFileB))
    pA.start(); pB.start()
    pA.join();  pB.join()
    if (pA.exitcode != 0) or (pB.exitcode != 0):
        raise Exception
    
    
def prepareConfigTemplate(platform, shape_parameter, preallocation):
    print("Prepare config template: preallocation =", preallocation, ", shape parameter =", shape_parameter)
    with open("precice.xml.template") as f:
        template = f.read()
    with open("precice.xml", "w") as f:
        f.write(template.format(shape_parameter = shape_parameter,
                                preallocation = preallocation,
                                network = get_platform_network_interface(platform)))

        
def createMesh(size):
    cmd = "../build/make_mesh.py --nx {0} --ny {0} mesh".format(size)
    subprocess.run(cmd, shell = True, check = True)
    
def partitionMesh(partitions, outname):
    cmd = "../build/partition_mesh.py --algorithm uniform --numparts {} --out {} mesh.txt"
    cmd = cmd.format(partitions, outname)
    subprocess.run(cmd, shell = True, check = True)


def doScaling(args, ranksA, ranksB, mesh_sizes, ms, preallocations):
    assert(len(ranksA) == len(ranksB) == len(mesh_sizes) == len(ms) == len(preallocations))

    removeEventFiles("A")
    removeEventFiles("B")

    file_info = { "date" : datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                  "name" : args.name,
                  "meshMin": min(mesh_sizes), "meshMax": min(mesh_sizes)}
    
    file_pattern = "{date}-{name}-{participant}-ranks{ranks}.{suffix}"
    
    for rankA, rankB, mesh_size, m, preallocation in zip(ranksA, ranksB, mesh_sizes, ms, preallocations):
        print("Running on ranks = {}/{}, mesh size = {}, m = {}".format(rankA, rankB, mesh_size, m))
        cmd = "{mpi} -n {size} {machinefile} ../../build/preciceMap --precice-config ../precice.xml --participant {participant} --mesh {mesh}"
        machine_file = get_machine_file(args.platform, ranksA, ranksB, args.mfile)
        cmdA = cmd.format(
            mpi = get_mpi_cmd(args.platform),
            size = rankA,
            machinefile = machine_file[0],
            participant = "A",
            mesh = "../outmesh")
        cmdB = cmd.format(
            mpi = get_mpi_cmd(args.platform),
            size = rankB,
            machinefile = machine_file[1],
            participant = "B",
            mesh = "../inmesh")

        if args.debug:
            print("Command A:", cmdA)
            print("Command B:", cmdB)

        
        file_info["ranks"] = rankB
        createMesh(mesh_size)
        partitionMesh(rankA, "outmesh")
        partitionMesh(rankB, "inmesh")
        prepareConfigTemplate(args.platform, shape_parameter(mesh_size, m), preallocation)
        launchRun(cmdA, cmdB,
                  file_pattern.format(suffix = "out", participant = "A", **file_info),
                  file_pattern.format(suffix = "out", participant = "B", **file_info))                  

    
        copy("A/precice-A-events.json", file_pattern.format(suffix = "json", participant = "A", **file_info))
        copy("B/precice-B-events.json", file_pattern.format(suffix = "json", participant = "B", **file_info))
        
        time.sleep(1) # sleep one second, sometimes the network ifaces are not free otherwise

    with open("{date}-{name}.meta".format(**file_info), "w") as f:
        json.dump({"name"  : args.name,
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", help = "A name for that run.", default = "upscaling")
    parser.add_argument("--mfile", help = "MPI machine file to use.")
    parser.add_argument("--mpisize", help = "Maximum MPI size per participant", type = int, required = True)
    parser.add_argument("--platform", choices = ["supermuc", "hazelhen", "mpich-opt", "mpich", "none"], default = "none")
    parser.add_argument("--debug", action = "store_true", default = False)
    args = parser.parse_args()

    ranks = generate_test_sizes(args.mpisize, args.platform)
    mpirun = get_mpi_cmd(args.platform)

    print("Name        =", args.name)
    print("Platform    =", args.platform)
    print("MPI command =", mpirun)
    print("Ranks       =", ranks)

    multiplicity = len(ranks)
    
    ranksA = [get_platform_node_size(args.platform)] * multiplicity
    ranksB = ranks
    ms = [6] * multiplicity
    mesh_sizes = [100] * multiplicity
    preallocations = ["tree"] * multiplicity

    doScaling(args, ranksA, ranksB, mesh_sizes, ms, preallocations)
