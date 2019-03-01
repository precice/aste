#!/usr/bin/env python3

import argparse, itertools, logging, os
import mesh
import numpy as np


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

def read_data(directory, geometry = (0,2), val_col_offset = 1, value_function = fun):
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
    solution = value_function(*coords)
    
    return coords, vals, solution


def rmse(indata, outdata):
    return np.sqrt( ((outdata.flatten() - indata.flatten())**2).mean() )

def gen_data(x0, x1, nx, y0, y1, ny):
    """ Generates an 2d, quadratic mesh on [start, end]² on points² """
    logging.info("Generate mesh on [{},{}] x [{},{}] with {} x {} points.".format(x0, x1, y0, y1, nx, ny))
    x = np.linspace(x0, x1, nx)
    y = np.linspace(y0, y1, ny)
    xx, yy = np.meshgrid(x, y)
    values = fun(xx, yy)
    return xx, yy, values

def gen_data_GC(order, element_size, domain_size, domain_start = 0, value_function = fun):
    xx, yy = mesh.GaussChebyshev_3D(order, element_size, domain_size, domain_start)
    values = value_function(xx, yy)
    return xx, yy, values
    

def write_file(filename, xx, yy, values):
    flat_values = values.flatten()

    with open(filename, "w") as f:
        for value, fx, fy in zip(flat_values, xx.flatten(), yy.flatten()):
            str = "{!s} {!s} {!s} {!s}".format(0, fx, fy, value)
            print(str, file = f)


def parse_args():
    parser = argparse.ArgumentParser(description="Create a mesh",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("out_mesh", metavar="outmesh", help="Name of output mesh file")
    parser.add_argument("--x0", type = int, default = 0, help="Start coordinate in x-dimension")
    parser.add_argument("--x1", type = int, default = 1, help="End coordinate in x-dimension")
    parser.add_argument("--nx", type = int, default = 100, help="Number of elements in x-direction")
    parser.add_argument("--y0", type = int, default = 0, help="Start coordinate in y-dimension")
    parser.add_argument("--y1", type = int, default = 1, help="End coordinate in y-dimension")
    parser.add_argument("--ny", type = int, default = 100, help="Number of elements in y-direction")
    
    parser.add_argument("--log", "-l", dest="logging", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                        help="Log level")
    return parser.parse_args()


    
def main():
    args = parse_args()
    logging.basicConfig(level=getattr(logging, args.logging))
    
    GC = False

    if GC:
        write_file("inMeshGC.txt", *gen_data_GC(4, 0.5, 4, domain_start = -2, value_function = gauss_pulse))
        write_file("outMeshGC.txt", *gen_data_GC(10, 0.5, 4, domain_start = -2, value_function = gauss_pulse))
        
    else:
        write_file(args.out_mesh + ".txt", *gen_data(args.x0, args.x1, args.nx, args.y0, args.y1, args.ny))
        logging.info("Wrote mesh to %s", args.out_mesh + ".txt");

        
if __name__== "__main__":
    main()
