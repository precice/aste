import multiprocessing, os, time, sys
from subprocess import run

import numpy as np
import pandas
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from plot_helper import set_save_fig_params

try:
    from ipdb import set_trace
except ImportError:
    pass

# sys.path.append("/data/scratch/lindnefn/precice/tools")
sys.path.append(os.environ['PRECICE_ROOT'] + "/tools")
import EventTimings

colors = [ i['color'] for i in plt.rcParams['axes.prop_cycle'] ]

def shapeParameter(mesh_size, m):
    h = 1 / mesh_size
    s = np.sqrt(- np.log(1e-9)) / (m * h)
    print("################## mesh_size =", mesh_size, ', m =', m, ", h =", h, ", s =", s, "##################")
    return s

def launchSingleRun(participant, ranks):
    mesh = "../outMesh.txt" if participant == "A" else "../inMesh.txt"
    os.chdir(participant)
    run(["mpirun", "-n", ranks, "../../readMesh", "-a", "-c", "../precice.xml", mesh, participant],
        check = True)

def launchRun(ranks):
    pA = multiprocessing.Process(target=launchSingleRun, daemon=True, args=("A", str(ranks)))
    pB = multiprocessing.Process(target=launchSingleRun, daemon=True, args=("B", str(ranks)))
    pA.start()
    pB.start()
    pA.join()
    pB.join()

    
def prepareConfigTemplate(shape_parameter, preallocation):
    with open("precice.xml.template") as f:
        template = f.read()
    with open("precice.xml", "w") as f:
        f.write(template.format(shape_parameter = shape_parameter, preallocation = preallocation))
        
def createMesh(size):
    cmd = "../make_mesh.py {0} {0}".format(size)
    run(cmd, shell = True, check = True)

def getLatestTimings():
    last_run = EventTimings.parseEventlog("B/EventTimings-B.log", timings_format = 'pandas')[-1]
    # Select fields and reorder them
    return last_run["timings"]

            
def measureStrongScaling():
    ms = [4, 6, 8]
    
    # mesh_size = 200
    # ranks = [2, 3, 4, 6, 8, 10, 14, 18, 24, 28, 32, 36]
    
    mesh_size = 20
    ranks = [2, 3, 4, 5]

    createMesh(mesh_size)
    set_save_fig_params(rows = 3)
    
    # Use preallocation
    fields = ['PetRBF.fillC', 'PetRBF.fillA', 'PetRBF.PostFill',
              'map', 'PetRBF.PreallocC', 'PetRBF.PreallocA']
    fig, ax = plt.subplots(len(ms), sharex = True)
    for i, m in enumerate(ms):
        prepareConfigTemplate(shapeParameter(mesh_size, m), True)
        data = pandas.DataFrame()
        
        for rank in ranks:
            launchRun(rank)
            timings = getLatestTimings(fields)['avg']
            timings.name = rank
            data = data.append(timings)

        data = data.reindex(columns = fields)
        data.plot(ax = ax[i], logy = True, legend = False, style = '-d', sharex = True)
        ax[i].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax[i].set_ylabel("Time [ms]")
        ax[i].set_title('m = {}'.format(m))

    
    ax[0].legend()
    ax[-1].set_xlabel("Processors")
    plt.savefig('strong-scaling-prealloc.pdf')
    plt.savefig('strong-scaling-prealloc.pgf')
    plt.close()

    # Do NOT use preallocation
    fields = ['PetRBF.fillC', 'PetRBF.fillA', 'PetRBF.PostFill', 'map']
    fig, ax = plt.subplots(len(ms), sharex = True)
    for i, m in enumerate(ms):
        prepareConfigTemplate(shapeParameter(mesh_size, m), False)
        data = pandas.DataFrame()
        
        for rank in ranks:
            launchRun(rank)
            timings = getLatestTimings(fields)['avg']
            timings.name = rank
            data = data.append(timings)

        data = data.reindex(columns = fields)
        data.plot(ax = ax[i], logy = True, legend = False, style = '-d', sharex = True)
        ax[i].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax[i].set_ylabel("Time [ms]")
        ax[i].set_title('m = {}'.format(m))

    ax[0].legend()
    ax[-1].set_xlabel("Processors")
    plt.savefig('strong-scaling-noprealloc.pdf')
    plt.savefig('strong-scaling-noprealloc.pgf')
    plt.close()

def save_plot(filename, **kwargs):
    fn = filename.format(**kwargs)
    plt.savefig(fn + '.pdf')
    plt.savefig(fn + '.pgf')

def measureRanks(ranks, prealloce, mesh_size_func, m):
    data = pandas.DataFrame()
    for rank in ranks:
        mesh_size = int(mesh_size_func(rank))
        createMesh(mesh_size)
        prepareConfigTemplate(shapeParameter(mesh_size, m), True)
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



# measureStrongScaling()

measureScaling(lambda ranks: 200, 'strong-scaling-{prealloc}-mesh200')
measureScaling(lambda ranks: np.sqrt(ranks * 100), 'weak-scaling-{prealloc}-mesh100')
