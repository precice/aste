# aste
Artificial Solver Testing Environment for preCICE.
aste consists of compiled C++ Modules and of Python modules.
## Python modules
### eval_mesh.py
Reads a mesh as either `.vtk` or `.txt` and evaluates a function given by `-f` on it. The function gets the mesh points a numpy array of the form `x = [[x_1, y_1, z_1], ...]` and should store the result in `y`.
### partition_mesh.py
Reads a mesh as either `.vtk` or `.txt`, partitions it and stores the parts in a directory like `dirname/0, 1, ...`. 
This python module needs the C++ module `libmetisAPI.so`.
### join_mesh.py
Reads a partitioned mesh from a directory like `dirname/0, 1, ...` and saves it to a `.vtk` or `.txt` file.

## Dependencies
### C++ modules
- preCICE
- Eigen3
- MPI
- CMake
- METIS
### Python modules
- NumPy
- tqdm
- vtk (Visualization Toolkit)
## Building
Make sure to have all the dependencies installed. Then do:
```
mkdir build
cd build
cmake ..
make
```
If precice is not installed in `$PRECICE_ROOT/build` do `cmake -DCMAKE_LIBRARY_PATH=$PRECICE_INSTALL_DIR ..` with the correct installation directory.
## Demo
A demonstration of aste can be run with `./demo.sh`.
