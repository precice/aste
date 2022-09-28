# Unit square & unit cube mesh generator

These scripts can generate mesh of a unit square/cube (with triangles or tetrahedral elements) with specified resolution.
Run with output file name and target mesh size as arguments. For instance :

```bash
python generate_unit_cube.py --mesh  coarse.vtk --resolution 0.2
```

This requires the `gmsh` and `meshio` Python packages.
