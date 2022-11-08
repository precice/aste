# Mesh Generators

## Unit square & unit cube mesh generator

These scripts can generate mesh of a unit square/cube (with triangles or tetrahedral elements) with specified resolution.
Run with output file name and target mesh size as arguments. For instance :

```bash
python generate_unit_cube.py --mesh  coarse.vtk --resolution 0.2
```

This requires the `gmsh` and `meshio` Python packages.

## Unit grid mesh generator

These script can generate a unit grid with given amount of point in dimensions x,y,z.
Run with output file name and mesh sizes.
Defaults are `x=10`, `y=10`, `z=1`.

```bash
# 10x10 2D grid with z coordinate of 0
python generate_unit_grid.py --mesh name.vtu
# 100x100 2D grid with z=0
python generate_unit_grid.py --mesh name.vtu -x 100 -y 100
# 100x100x2 3D grid
python generate_unit_grid.py --mesh name.vtu -x 100 -y 100 -z 2
```

This requires the `meshio` and `numpy` Python packages.

## Halton points mesh generator

This script can generate a mesh bounded in a unit square/cube (without any connectivity information) with given number of points.
Run with output file name, number of points and space dimension as arguments, optionally seed for Halton generator can be passed. For instance :

```bash
python generate_halton_mesh.py --mesh halton_cube.vtk --numpoints 1000 --dimension 3
python generate_halton_mesh.py --mesh halton_square.vtu --numpoints 500 --dimension 2 --seed 42
```

This requires the `scipy`, `numpy` and `meshio` Python packages.
