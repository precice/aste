import numpy as np

def GC(order, element_size, domain_size, domain_start = 0):
    """ Returns coordinates for a 2d Gauss-Chebyshev mesh. """
    assert(domain_size % element_size == 0)
    nodes = np.arange( 1, order + 1 )
    cheb = 0.5 * element_size * np.cos( np.pi * (2*nodes-1)/ (2*order) )
    coords = np.array([])
    for element in range(int(domain_size/element_size)):
        coords = np.append(coords, cheb + ((0.5+element) * element_size))

    coords += domain_start
    np.ndarray.sort(coords)
    print("Gauss-Chebyshev mesh with", len(coords), "points, h_max =", np.max(coords[1:] - coords[:-1]))
    return coords

def GaussChebyshev_1D(order, element_size, domain_size, domain_start = 0):
    """ Returns coordinates for a 1d Gauss-Chebyshev mesh. """
    assert(domain_size % element_size == 0)
    nodes = np.polynomial.chebyshev.chebgauss(order)[0] # Get GC points on [-1;1]
    nodes *= element_size / 2 # Scale from [-1;1] to element_size

    coords =  np.array([])
    for element in range(int(domain_size // element_size)):
        coords = np.append(coords, nodes + (0.5 + element) * element_size)

    coords += domain_start
    np.ndarray.sort(coords)
    print("Gauss-Chebyshev mesh with", len(coords), "points, h_max =", np.max(coords[1:] - coords[:-1]))
    return coords


def GaussChebyshev_2D(order, element_size, domain_size, domain_start = 0):
    """ Returns a 2d quadratic Gauss-Chebyshev mesh grid """
    x = GaussChebyshev_1D(order, element_size, domain_size, domain_start)
    y = GaussChebyshev_1D(order, element_size, domain_size, domain_start)
    xx, yy = np.meshgrid(x,y)
    return xx, yy



if __name__ == "__main__":
    import pdb; pdb.set_trace()
    assert(np.all(GaussChebyshev_1D(4, 2, 2, 0) == GC(4, 2, 2, 0)))
    assert(np.all(GaussChebyshev_1D(4, 2, 2, 5) == GC(4, 2, 2, 5)))
    assert(np.all(GaussChebyshev_1D(10, 2, 2, 5) == GC(10, 2, 2, 5)))
    assert(np.all(GaussChebyshev_1D(4, 1, 2, 0) == GC(4, 1, 2, 0)))
    assert(np.all(GaussChebyshev_1D(6, 3, 9, 8) == GC(6, 3, 9, 8)))

