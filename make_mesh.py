#!/usr/bin/env python3

import os, itertools

import numpy as np
import matplotlib.pyplot as plt

import pdb

in_dimensions = (-10, 10, 500)
out_dimensions = (-10, 10, 500)
test_dimensions = (-10, 10, 2000)
MPI_size = 4

fun = lambda xx = 0, yy = 0, zz = 0 : np.sin(xx) + np.cos(2*yy)
# fun = lambda xx = 0, yy = 0, zz = 0 : xx + yy

def gauss_pulse(xx, yy, zz = 0):
    rho_0 = 1.225
    rho_pulse = 2
    d = 0.2
    x_0 = y_0 = 0
    return rho_0 + rho_pulse * np.exp( -(np.power(xx + x_0, 2) + np.power(yy + y_0, 2))) / d + np.log(2)

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
    """ Generates an 2d, quadratic mesh on [start, end]² on points² """
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
        for i, value, fx, fy in zip(itertools.count(), flat_values, xx.flatten(), yy.flatten()):
            if i % nodes_per_rank == 0:
                current_rank += 1
                
            str = "{!s} {!s} {!s} {!s} {!s}".format(0, fx, fy, value, current_rank)
            print(str, file = f)

    
def main():
    write_file("inMesh", *in_dimensions)
    print("Wrote inMesh, dimensions,", in_dimensions);
    
    write_file("outMesh", *out_dimensions)
    print("Wrote outMesh dimensions,", out_dimensions);
    
    write_file("testMesh", *test_dimensions)
    print("Wrote testMesh, dimensions,", test_dimensions);
    
    print("Wrote meshes for", MPI_size, "ranks.")
        
    # plt.contour(x, y, values)
    # plt.grid()
    # plt.show()

    # x,y,v,rank

  

    # plt.plot(fv)
    # plt.show()

if __name__== "__main__":
    main()
