#!/usr/bin/env python3
import argparse, logging, math, os
import numpy as np
import shutil
from ctypes import *
import mesh_io

def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.logging))
    if len(args.in_meshname) > 1 and args.out_meshname:
        logging.warn("--out ignored")
    mesh_names = args.in_meshname
    for mesh_name in mesh_names:
        assert os.path.isfile(mesh_name), ("Invalid filename: "  + mesh_name)
    algorithm = args.algorithm
    if not algorithm:
        logging.info("No algorithm given. Defaulting to \"meshfree\"")
        algorithm = "meshfree"
    rootmesh = read_mesh(mesh_names[0], args.tag)
    if args.numparts > 1:
        part = partition(rootmesh, args.numparts, algorithm)
    else:
        part = [0] *  len(rootmesh.points)
        
    for mesh_name in mesh_names:
        logging.info("Processing mesh " + mesh_name)
        mesh = read_mesh(mesh_name, args.tag)
        logging.debug("Checking if meshes are matching...")
        assert mesh.points == rootmesh.points, ("Non-matching meshes detected!")
        meshes = apply_partition(mesh, part, args.numparts)
        if len(mesh_names) > 1 or not args.out_meshname:
            out_meshname = os.path.splitext(mesh_name)[0]
            logging.info("Writing output to: " + out_meshname)
            # logging.info("No --out given. Setting output to: " + out_meshname)
        else:
            out_meshname = args.out_meshname
        write_meshes(meshes, out_meshname)

    
class Mesh:
    """
    A Mesh consists of:
        - Points: A list of tuples of floats representing coordinates of points
        - Cells: A list of tuples of ints representing mesh elements
        - Pointdata: A list of floats representing data values at the respective point
    """
    def __init__(self, points = None, cells = None, cell_types = None, pointdata = None):
        if points is not None:
            self.points = points
        else:
            self.points = []
        if cells is not None:
            assert(cell_types is not None)
            self.cells = cells
            self.cell_types = cell_types
        else:
            self.cells = []
            self.cell_types = []
        if pointdata is not None:
            self.pointdata = pointdata
        else:
            self.pointdata = []

    def __str__(self):
        return "Mesh with {} Points and {} Cells ({} Cell Types)".format(len(self.points), len(self.cells), len(self.cell_types))


def read_mesh(filename, tag):
    points, cells, cell_types, pointdata = mesh_io.read_mesh(filename, tag)
    return Mesh(points, cells, cell_types, pointdata)



def partition(mesh, numparts, algorithm):
    """
    Partitions a mesh using METIS or kmeans. This does not call METIS directly, 
    but instead uses a small C++ Wrapper libmetisAPI.so for convenience. 
    This shared library must be provided if this function should be called.
    """
    if algorithm == "meshfree":
        return partition_kmeans(mesh, numparts)
    elif algorithm == "topology":
        return partition_metis(mesh, numparts)
    elif algorithm == "uniform":
        labels = partition_uniform(mesh, numparts)
        if labels is None:
            return partition(mesh, numparts, "meshfree")
        return labels

    
def partition_kmeans(mesh, numparts):
    """ Partitions a mesh using k-means. This is a meshfree algorithm and requires scipy"""
    from scipy.cluster.vq import kmeans2
    points = np.copy(mesh.points)
    points = reduce_dimension(points)
    _, label = kmeans2(points, numparts)
    return label


def reduce_dimension_simple(mesh):
    """
    A simple, efficient algorithm for a dimension reduction for a mesh 
    with one or more "dead dimensions"
    """
    testP = mesh[0]
    dead_dims = np.argwhere(np.abs(np.array(testP)) < 1e-9)
    for point in mesh:
        current_dead_dims = np.argwhere(np.abs(np.array(point)) < 1e-9)
        dead_dims = np.intersect1d(dead_dims, current_dead_dims)
        if len(dead_dims) == 0:
            return mesh
    mesh = np.array(mesh)
    full = np.array([0,1,2])
    mask = np.setdiff1d(full, dead_dims)
    return mesh[:,mask]


def reduce_dimension(mesh):
    """
    This function gets a list of points in 3d and if all of them are within one plane it
    returns a list of 2d points in the plane, else the unmodified list is returned.
    """
    pA, pB = mesh[:2]
    pC = mesh[-1]
    pA = np.array(pA)
    AB = pB - pA
    AC = pC - pA
    n = np.cross(AB, AC)
    # Every point x in the plane must fulfill (x - pA) * n = 0
    for x in mesh:
        if not np.dot(x - pA, n) == 0:
            return mesh
    else: # All Points within plane
        # Transform mesh so all points have form (0, y, z)
        # Compute Euler-Rodrigues rotation matrix
        n /= np.linalg.norm(n) # Normalize
        zUnit = np.array((0,0,1))
        phi = math.acos(np.dot(n, zUnit))
        logging.info("Rotating mesh with phi = " + str(360 * phi/(2 * math.pi)) + " degrees.")
        axis = np.cross(n, zUnit)
        axis /= np.linalg.norm(axis)
        a = math.cos(phi/2)
        b = math.sin(phi/2) * axis[0]
        c = math.sin(phi/2) * axis[1]
        d = math.sin(phi/2) * axis[2]
        rotMat = np.array((
                (a**2 + b**2 - c**2 - d**2, 2*(b*c - a*d),              2*(b*d + a*c)),
                (2*(b*c + a*d),             a**2 + c**2 - b**2 - d**2,  2*(c*d - a*b)),
                (2*(b*d - a*c),             2*(c*d + a*b),              a**2 + d**2 - b**2 - c**2)))
        for i, x in enumerate(mesh): # Translate & Rotate
            x -= pA
            x = x @ rotMat
            mesh[i] = x
        return mesh[:,:-1]

    
def partition_metis(mesh, numparts):
    """
    Partitions a mesh using METIS. This does not call METIS directly, 
    but instead uses a small C++ Wrapper libmetisAPI.so for convenience. 
    This shared library must be provided if this function should be called.
    """
    cellPtr = [0]
    cellData = []
    if len(mesh.cells) == 0:
        logging.warning("No topology information provided. Partitioning with metis will likely provide bad partition");
    for i in range(len(mesh.cells)):
        cell = mesh.cells[i]
        cellData += list(cell)
        cellPtr.append(cellPtr[-1] + len(cell))
    libmetis = cdll.LoadLibrary(os.path.abspath("libmetisAPI.so"))
    idx_t = c_int if libmetis.typewidth() == 32 else c_longlong
    cell_count = idx_t(len(mesh.cells))
    point_count = idx_t(len(mesh.points))
    num_parts = idx_t(numparts)
    partition = (idx_t * len(mesh.points))()
    cell_ptr = (idx_t * len(cellPtr))(*cellPtr)
    cell_data = (idx_t * len(cellData))(*cellData)
    libmetis.partitionMetis(cell_count, point_count, cell_ptr, cell_data, num_parts, partition)
    arr = np.ctypeslib.as_array(partition)
    return arr

def partition_uniform(mesh, numparts):
    """
    Partitions a mesh assuming it is uniform. It must be two-dimensional 
    but is allowed to be layed out anyhow in three dimensions.
    """
    mesh = mesh.points[:]
    mesh = reduce_dimension(np.array(mesh))
    if len(mesh[0]) == 3:
        logging.warning("Mesh is not uniform. Falling back to meshfree method")
        return None
    min_point = np.amin(mesh, 0)
    max_point = np.amax(mesh, 0)
    big_dim = 0 if max_point[0] - min_point[0] >= max_point[1] - min_point[1] else 1
    small_dim = 1 - big_dim

    def prime_factors(n):
        """ Straight from SO"""
        i = 2
        factors = []
        while i * i <= n:
            if n % i:
                i += 1
            else:
                n //= i
                factors.append(i)
        if n > 1:
            factors.append(n)
        return factors

    def greedy_choose(factors):
        """ Greedily choose "best" divisors"""
        small = big = 1
        for factor in reversed(factors):
            if big <= small:
                big *= factor
            else:
                small *= factor
        return small, big

    small, big = greedy_choose(prime_factors(numparts))
    small_interval = (max_point[small_dim] - min_point[small_dim]) / small
    big_interval = (max_point[big_dim] - min_point[big_dim]) / big
    labels = []
    logging.info("Uniform partioning of mesh size {} into {} x {} partitions.".format(
        len(mesh), small, big))
    for point in mesh:
        small_offset = point[small_dim] - min_point[small_dim]
        small_index = int(small_offset / small_interval)
        small_index = min(small_index, small - 1)
        big_offset = point[big_dim] - min_point[big_dim]
        big_index = int(big_offset / big_interval)
        big_index = min(big_index, big - 1)
        partition_num = small_index * big + big_index
        labels.append(partition_num)
    return labels


def apply_partition(orig_mesh, part, numparts):
    """
    Partitions a mesh into many meshes when given a partition and a mesh.
    """
    meshes = [Mesh() for _ in range(numparts)]
    mapping = {}  # Maps global index to partition and local index
    print(orig_mesh)
    for i in range(len(orig_mesh.points)):
        partition = part[i]
        selected = meshes[partition]
        mapping[i] = (partition, len(selected.points))
        selected.points.append(orig_mesh.points[i])
        if orig_mesh.pointdata:
            selected.pointdata.append(orig_mesh.pointdata[i])

    assert(len(mapping) == len(orig_mesh.points))
    assert(len(orig_mesh.cells) == len(orig_mesh.cell_types))
    for cell, type in zip(orig_mesh.cells, orig_mesh.cell_types):
        partitions = list(map(lambda idx: mapping[idx][0], cell))
        if len(set(partitions)) == 1:
            meshes[partitions[0]].cells.append(tuple([mapping[gidx][1] for gidx in cell]))
            meshes[partitions[0]].cell_types.append(type)

    for m in meshes:
        print(m)

    return meshes


def write_meshes(meshes, dirname):
    """
    Writes meshes to given directory.
    """
    dirname = os.path.abspath(dirname)
    if os.path.exists(dirname):
        shutil.rmtree(dirname)
    os.mkdir(dirname)
    for i in range(len(meshes)):
        mesh = meshes[i]
        mesh_io.write_txt(dirname + "/" + str(i), mesh.points, mesh.cells, mesh.pointdata)

        
def parse_args():
    parser = argparse.ArgumentParser(description=
                                     "Read meshes, partition them and write them out in internal format.")
    parser.add_argument("in_meshname", metavar="inputmesh", nargs="+", help="The meshes used as input")
    parser.add_argument("--out", "-o", dest="out_meshname", help="The output mesh directory name. Only works if single in_mesh is given.")
    parser.add_argument("--numparts", "-n", dest="numparts", default=1, type=int, 
            help="The number of parts to split into")
    parser.add_argument("--tag", "-t", dest="tag", default=None,
            help="The PointData tag for vtk meshes")
    parser.add_argument("--algorithm", "-a", dest="algorithm", choices=["meshfree", "topology", "uniform"],
            help="""Change the algorithm used for determining a partition. 
            A meshfree algorithm works on arbitrary meshes without needing topological information. 
            A topology-based algorithm needs topology information 
            and is therefore useless on point clouds.

            A uniform algorithm will assume a uniform 2d mesh layed out somehow in 3d and partition accordingly.""")
    parser.add_argument("--log", "-l", dest="logging", default="INFO", 
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], 
            help="Set the log level. Default is INFO")
    return parser.parse_args()

if __name__ == "__main__":
    main()
