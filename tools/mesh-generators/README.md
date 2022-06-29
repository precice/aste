# Unit square & unit cube mesh generator

These scripts can generate mesh of a unit square/cube (with triangles or tetrahedral elements) with specified resolution.
Run with output file name and target mesh size as arguments. For instance : 

```
python generate_unit_cube.py coarse.vtk 0.2
```

This requires the `gmsh` and `meshio` Python packages.