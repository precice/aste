#!/usr/bin/env python

import os

import numpy as np
import matplotlib.pyplot as plt

import pdb

in_dimensions = (-10, 10, 50)
out_dimensions = (-10, 10, 50)
MPI_size = 4

fun = lambda xx = 0, yy = 0, zz = 0 : np.sin(xx) + np.cos(2*yy)
# fun = lambda xx = 0, yy = 0, zz = 0 : xx + yy

def lookup_from_coords(x, y, table):
    return table[table[0]==x][table[1]==y]

def read_data(directory, geometry = (0,2), val_col_offset = 1):
    """ Reads data from directory
    geometry: Colums that hold 2D geometry information.
    val_col_offset: Offset from geometry col to value col 

    Returns coords, vals and analytical solution (from fun) 
    in meshgrid like notation, """

    usecols = geometry + (val_col_offset + geometry[-1], )
    out = np.empty((0, len(usecols)))

    if os.path.isdir(directory):
        for file in sorted(os.listdir(directory)):
            print("Read from", file)
            out = np.vstack((out,
                             np.loadtxt(os.path.join(directory, file), usecols = usecols)))
    elif os.path.isfile(directory):
        print("Read from", directory)
        out = np.vstack((out,
                         np.loadtxt(directory, usecols = usecols)))
        
    cidx = range(len(geometry)) # Indizes of coordinates in out
    # Unscramble the array
    out = out[np.lexsort(np.fliplr( out[:,cidx] ).T)]
    
    size = int(np.sqrt(len(out)))
    out = out.reshape(size, size, -1)
    coords = []
    for i in cidx:
        coords.append(out[..., i])

    vals = out[..., -1]
    solution = fun(*coords)
    
    return coords, vals, solution


def rmse(indata, outdata):
    return np.sqrt( ((outdata.flatten() - indata.flatten())**2).mean() )

def gen_data(start, end, points):
    x = np.linspace(start, end, points)
    y = np.linspace(start, end, points)
    xx, yy = np.meshgrid(x, y)
    values = fun(xx, yy)

    return x,y, xx, yy, values

def write_file(filename, start, end, points):
    x, y, xx, yy, values = gen_data(start, end, points)

    flat_values = values.flatten()

    nodes_per_rank = int(len(flat_values) / MPI_size)

    current_rank = -1
    with open(filename, "w") as f:
        for i, value in enumerate(flat_values):
            if i % nodes_per_rank == 0:
                current_rank += 1
                
            str = "{!s} {!s} {!s} {!s} {!s}".format(0,
                                                    xx.flatten()[i],
                                                    yy.flatten()[i],
                                                    value,
                                                    current_rank)
            print(str, file = f)

    
def main():
    write_file("inMesh", *in_dimensions)
    write_file("outMesh", *out_dimensions)
    print("Wrote meshes for", MPI_size, "ranks.")
    print("inMesh dimensions,", in_dimensions);
    print("outMesh dimensions,", out_dimensions);
    
    # plt.contour(x, y, values)
    # plt.grid()
    # plt.show()

    # x,y,v,rank

  

    # plt.plot(fv)
    # plt.show()

if __name__== "__main__":
    main()
