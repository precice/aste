import contextlib, datetime, multiprocessing, os, time, subprocess, sys, socket, json
from pathlib import Path

import numpy as np
# import pandas
# import matplotlib.pyplot as plt
# import matplotlib.ticker as ticker
# # from plot_helper import set_save_fig_params

try:
    from ipdb import set_trace
except ImportError:
    from pdb import set_trace

sys.path.append(os.environ['PRECICE_ROOT'] + "/tools")
import EventTimings

# colors = [ i['color'] for i in plt.rcParams['axes.prop_cycle'] ]

def removeEventFiles(participant):
    p = Path(participant)
    try:
        Path(p / ("Events-%s.log" % participant)).unlink()
        Path(p / ("EventTimings-%s.log" % participant)).unlink()
    except FileNotFoundError:
        pass
        

def shape_parameter(mesh_size, m):
    h = 1 / mesh_size
    s = np.sqrt(- np.log(1e-9)) / (m * h)
    print("################## mesh_size =", mesh_size, ', m =', m, ", h =", h, ", s =", s, "##################")
    return s

def launchSingleRun(participant, ranks, outfile = None):
    ostream = open(outfile, "w+") if outfile else sys.stdout
    mesh = "../outMesh.txt" if participant == "A" else "../inMesh.txt"
    os.chdir(participant)
    
    cmd = ["mpirun", "-n", ranks, "../../readMesh", "-a", "-c", "../precice.xml", mesh, participant]
    with contextlib.redirect_stdout(ostream):
        cp = subprocess.run(cmd, stdout = sys.stdout, stderr = subprocess.STDOUT, check = True)
    

def launchRun(ranks, outFileA = None, outFileB = None):
    pA = multiprocessing.Process(target=launchSingleRun, daemon=True, args=("A", str(ranks), outFileA))
    pB = multiprocessing.Process(target=launchSingleRun, daemon=True, args=("B", str(ranks), outFileB))
    pA.start(); pB.start()
    pA.join();  pB.join()
    if (pA.exitcode != 0) or (pB.exitcode != 0):
        raise Exception
    
    
def prepareConfigTemplate(shape_parameter, preallocation):
    with open("precice.xml.template") as f:
        template = f.read()
    with open("precice.xml", "w") as f:
        f.write(template.format(shape_parameter = shape_parameter, preallocation = preallocation))
        
def createMesh(size):
    cmd = "../make_mesh.py {0} {0}".format(size)
    subprocess.run(cmd, shell = True, check = True)


def save_plot(filename, **kwargs):
    fn = filename.format(**kwargs)
    plt.savefig(fn + '.pdf')
    plt.savefig(fn + '.pgf')

def measureRanks(ranks, prealloc, mesh_size_func, m):
    data = pandas.DataFrame()
    for rank in ranks:
        mesh_size = int(mesh_size_func(rank))
        createMesh(mesh_size)
        prepareConfigTemplate(shape_parameter(mesh_size, m), prealloc)
        launchRun(rank)
        timings = getLatestTimings()['avg']
        timings.name = rank
        data = data.append(timings)

    return data


def measureUni(ranks, sizes, prealloc, m):
    data = pandas.DataFrame()
    for rank, size in zip(ranks, sizes):
        createMesh(size)
        prepareConfigTemplate(shape_parameter(size, m), prealloc)
        launchRun(rank)
        timings = getLatestTimings()['avg']
        timings.name = rank
        data = data.append(timings)

    return data

    

def measureScaling(mesh_size_func, filename):
    ms = [4, 6, 8]
    
    ranks = [2, 3, 4, 6, 8, 10, 14, 18, 24, 28, 32, 36]
    # ranks = [2, 3, 4, 5]

    set_save_fig_params(rows = 3)
    
    # Use preallocation
    fields = ['PetRBF.fillC', 'PetRBF.fillA', 'PetRBF.PostFill',
              'map', 'PetRBF.PreallocC', 'PetRBF.PreallocA']
    fig, ax = plt.subplots(len(ms), sharex = True)
    for i, m in enumerate(ms):
        data = measureRanks(ranks, True, mesh_size_func, m)
        # set_trace()
        # data = data.reindex(columns = fields)
        data[fields].plot(ax = ax[i], logy = True, legend = False, style = '-d', sharex = True)
        ax[i].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax[i].set_ylabel("Time [ms]")
        ax[i].set_title('m = {}'.format(m))

    
    ax[0].legend()
    ax[-1].set_xlabel("Processors")
    save_plot(filename, prealloc = "prealloc")
    plt.close()

    # Do NOT use preallocation
    fields = ['PetRBF.fillC', 'PetRBF.fillA', 'PetRBF.PostFill', 'map']
    fig, ax = plt.subplots(len(ms), sharex = True)
    for i, m in enumerate(ms):
        data = measureRanks(ranks, False, mesh_size_func, m)
        # data = data.reindex(columns = fields)
        data[fields].plot(ax = ax[i], logy = True, legend = False, style = '-d', sharex = True)
        ax[i].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax[i].set_ylabel("Time [ms]")
        ax[i].set_title('m = {}'.format(m))

    ax[0].legend()
    ax[-1].set_xlabel("Processors")
    save_plot(filename, prealloc = "noprealloc")
    plt.close()


def doScaling(name, ranks, mesh_sizes, ms):
    assert(len(ranks) == len(mesh_sizes))

    removeEventFiles("A")
    removeEventFiles("B")

    file_info = { "date" : datetime.datetime.now().isoformat(),
                  "name" : name,
                  "rankMin" : min(ranks), "rankMax" : max(ranks),
                  "meshMin": min(mesh_sizes), "meshMax": min(mesh_sizes)}
    
    file_pattern = "{date}-{name}-{participant}.{suffix}"
    
    for rank, mesh_size, m in zip(ranks, mesh_sizes, ms):
        print("Running on ranks = {}, mesh size = {}, m = {}".format(rank, mesh_size, m))
        createMesh(mesh_size)
        prepareConfigTemplate(shape_parameter(mesh_size, m), "tree")
        launchRun(rank,
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
                   "ranks" : ranks, "mesh_sizes" : mesh_sizes, "m" : m},
                  f)
                
    

def comparePreAllocVsNon(mesh_size_func, filename):
    ranks = [4, 6, 8, 10, 14, 18, 24, 28, 32, 36, 40]
    # ranks = [2,3,4]

    ms = [4, 6, 8]

    set_save_fig_params(rows = 3)
    
    fig, ax = plt.subplots(len(ms), sharex = True)
    for i, m in enumerate(ms):
        data = measureRanks(ranks, 'compute', mesh_size_func, m)
        data.plot(ax = ax[i], y = 'computeMapping', logy = True, legend = False, style = '-d',
                          sharex = True, label = "compute preallocation")
        
        data = measureRanks(ranks, 'mark', mesh_size_func, m)
        data.plot(ax = ax[i], y = 'computeMapping', logy = False, legend = False, style = '-d',
                          sharex = True, label = "saved preallocation")
        
        data = measureRanks(ranks, 'off', mesh_size_func, m)
        data.plot(ax = ax[i], y = 'computeMapping', logy = False, legend = False, style = '-d',
                          sharex = True, label = "without preallocation")

        data = measureRanks(ranks, 'tree', mesh_size_func, m)
        data.plot(ax = ax[i], y = 'computeMapping', logy = False, legend = False, style = '-d',
                          sharex = True, label = "tree preallocation")
        
        
        ax[i].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax[i].set_ylabel("Time [ms]")
        ax[i].set_title('m = {}'.format(m))
    
    ax[0].legend()
    ax[-1].set_xlabel("Processors")
    save_plot(filename)
    plt.close()


def problemUpscaling(filename):
    mesh_sizes = [10, 20, 50, 75, 125, 150, 175, 200, 225, 250, 275, 300]
    ranks = [8] * len(mesh_sizes)
    ms = [4, 6, 8]    

    set_save_fig_params(rows = 3)
    
    fig, ax = plt.subplots(len(ms), sharex = True)
    for i, m in enumerate(ms):
        data = measureUni(ranks, mesh_sizes, 'compute', m)
        ax[i].loglog(mesh_sizes, data["computeMapping"].values, "-d", label = "computed")
                
        data = measureUni(ranks, mesh_sizes, 'mark', m)
        ax[i].loglog(mesh_sizes, data["computeMapping"].values, "-d", label = "saved")
        
        data = measureUni(ranks, mesh_sizes, 'off', m)
        ax[i].loglog(mesh_sizes, data["computeMapping"].values, "-d", label = "without")
        
        data = measureUni(ranks, mesh_sizes, 'tree', m)
        ax[i].loglog(mesh_sizes, data["computeMapping"].values, "-d", label = "tree")
                
        
        # ax[i].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax[i].set_ylabel("Time [ms]")
        ax[i].set_title('ranks = {}, m = {}'.format(ranks[0], m))

    set_trace()

    ax[0].legend()
    ax[-1].set_xlabel("Mesh Size")
    save_plot(filename)
    plt.close()



# measureScaling(lambda ranks: 200, 'strong-scaling-{prealloc}-mesh200')
# measureScaling(lambda ranks: np.sqrt(ranks * 100), 'weak-scaling-{prealloc}-mesh100')
# comparePreAllocVsNon(lambda ranks: 200, 'comparision')
# problemUpscaling("problemupscaling")

ranks = [4, 6, 8, 10, 12, 14, 18, 22, 26, 30]
# ranks = [4]
mesh_sizes = [400] * len(ranks)
ms = [6] * len(ranks)
doScaling("testeins", ranks, mesh_sizes, ms)
