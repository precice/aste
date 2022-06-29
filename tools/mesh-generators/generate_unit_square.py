import gmsh
import meshio
import sys

def generate_unit_square_vtk(out, resolution):

    gmsh.initialize()

    gmsh.model.add("t1")

    lc = resolution
    gmsh.model.geo.addPoint(0,0,0, lc, 1)
    gmsh.model.geo.addPoint(1,0,0, lc, 2)
    gmsh.model.geo.addPoint(1,1,0, lc, 3)
    gmsh.model.geo.addPoint(0,1,0, lc, 4)

    gmsh.model.geo.addLine(1, 2)
    gmsh.model.geo.addLine(2, 3)
    gmsh.model.geo.addLine(3, 4)
    gmsh.model.geo.addLine(4, 1)

    gmsh.model.geo.addCurveLoop([1, 2, 3, 4], 1)

    surface = gmsh.model.geo.addPlaneSurface([1], 1)

    gmsh.model.geo.synchronize()

    # Add groups
    gmsh.model.addPhysicalGroup(2, [surface], name = "Surface")

    gmsh.model.mesh.generate(3)
    gmsh.write("tmp.msh")

    gmsh.finalize()

    # Convert 

    mesh = meshio.read("tmp.msh")
    mesh.write(out) 

def print_usage():
    print("Usage: generate_unit_cube.py filename.vtk/vtu mesh_resolution. Example: generate_unit_cube.py coarse.vtk 0.25")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print_usage()
    else:
        output = sys.argv[1]
        res = float(sys.argv[2])
        generate_unit_square_vtk(output, res)
