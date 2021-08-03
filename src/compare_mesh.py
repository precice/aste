#!/usr/bin/env python3
import argparse
import logging
import numpy as np
from mesh_io import read_mesh, printable_cell_type
from scipy import spatial
import itertools



def group_sizes(iterable):
    res = {k: 0 for k in set(iterable)}
    for elem in iterable:
        res[elem] += 1
    return  res

def unique_edges(cells):

    def to_edges(cell):
        if len(cell) == 2:
            return list(tuple(cell))
        else:
            return list(map(tuple, zip(cell, cell[1:])))

    return set(map(lambda e: e if e[0] < e[1] else (e[1], e[0]), itertools.chain.from_iterable(map(to_edges, cells))))


def print_histogram(nphisto):
    histo, bin_edges = nphisto
    bins = zip(bin_edges, bin_edges[1:])

    total = np.sum(histo)
    headerFmt =" {:^20} {:^20}  {:>10}  {:>7} {:>7}"
    tableFmt = "[{:>20.15f},{:>20.15f}] {:>10}  {:7.2%} {:7.2%}"

    print(headerFmt.format("Lower bound", "upper bound", "content", "relative", "cumulative"))
    cumulative = 0.0
    for content, bin in zip(histo, bins):
        relative = content/total
        cumulative += relative
        print(tableFmt.format(bin[0], bin[1], content, relative, cumulative))
    print(headerFmt.format("", "Total", total, "100.00%", ""))


def describe_edge_lengths(points, cells):

    def edge_length(edge):
        a = points[edge[0]]
        b = points[edge[1]]
        return np.linalg.norm(a-b)

    edges = unique_edges(cells)
    histo = np.histogram(list(map(edge_length, edges)), bins=10)
    print_histogram(histo)


def describe_distances(fromPoints, toPoints):
    distances, indices = spatial.KDTree(toPoints).query(fromPoints)
    bins = np.unique(np.append(np.histogram_bin_edges(distances, 17), [0, 0.0001, 0.001]))

    histo = np.histogram(distances, bins=bins)
    print_histogram(histo)



def describe_mesh(points, cells, cell_types):
    print("Vertices: {}".format(len(points)))
    print("Enclosing bounding box:")
    min, max = np.amin(points, 0), np.amax(points, 0)
    print("    min  ({:>20.12f}, {:>20.12f}, {:>20.12f})".format(*min))
    print("    max  ({:>20.12f}, {:>20.12f}, {:>20.12f})".format(*max))
    print("    size ({:>20.12f}, {:>20.12f}, {:>20.12f})".format(*(max-min)))
    print("Cells: " + ", ".join([ "{}: {}".format(printable_cell_type(type), size) for type, size in group_sizes(cell_types).items() ]))
    print("Distribution of all unique edges by length:")
    describe_edge_lengths(points, cells)

def print_header(s):
    print(s)
    print("-"*len(s))


def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.logging))

    apoints, acells, acell_types, _ = map(np.array, read_mesh(args.mesha))
    bpoints, bcells, bcell_types, _ = map(np.array, read_mesh(args.meshb))

    print_header("Mesh A")
    print("Loaded from file: "+args.mesha)
    describe_mesh(apoints, acells, acell_types)
    print()

    print_header("Mesh B")
    print("Loaded from file: "+args.meshb)
    describe_mesh(bpoints, bcells, bcell_types)
    print()

    print_header("MeshA => MeshB (consistent mapping)")
    print("Distribution of distances to nearest-neighbours:")
    describe_distances(apoints, bpoints)
    print()

    print_header("MeshA <= MeshB (conservative mapping)")
    print("Distribution of distances to nearest-neighbours:")
    describe_distances(bpoints, apoints)

def parse_args():
    parser = argparse.ArgumentParser(description="Compares mesh a against mesh b.")
    parser.add_argument("mesha", metavar="mesha", help="The mesh to compare.")
    parser.add_argument("meshb", metavar="meshb", help="The mesh to compare against.")
    parser.add_argument("--log", "-l", dest="logging", default="INFO", 
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], help="""Set the log level. 
            Default is INFO""")

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    main()
