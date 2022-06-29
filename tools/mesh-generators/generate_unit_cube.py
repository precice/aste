import gmsh
import meshio
import sys

def generate_unit_cube_vtk(out, resolution):

    gmsh.initialize()

    gmsh.model.add("t1")

    lc = resolution
    gmsh.model.geo.addPoint(0,0,0, lc, 1)
    gmsh.model.geo.addPoint(1,0,0, lc, 2)
    gmsh.model.geo.addPoint(1,1,0, lc, 3)
    gmsh.model.geo.addPoint(0,1,0, lc, 4)
    gmsh.model.geo.addPoint(0,0,1, lc, 5)
    gmsh.model.geo.addPoint(1,0,1, lc, 6)
    gmsh.model.geo.addPoint(1,1,1, lc, 7)
    gmsh.model.geo.addPoint(0,1,1, lc, 8)

    # Lower face
    ab = gmsh.model.geo.addLine(1, 2)
    bc = gmsh.model.geo.addLine(2, 3)
    cd = gmsh.model.geo.addLine(3, 4)
    da = gmsh.model.geo.addLine(4, 1)
    
    # Upper face
    ef = gmsh.model.geo.addLine(5, 6)
    fg = gmsh.model.geo.addLine(6, 7)
    gh = gmsh.model.geo.addLine(7, 8)
    he = gmsh.model.geo.addLine(8, 5)

    # Verticla edges, from bottom to top
    ae = gmsh.model.geo.addLine(1, 5)
    bf = gmsh.model.geo.addLine(2, 6)
    cg = gmsh.model.geo.addLine(3, 7)
    dh = gmsh.model.geo.addLine(4, 8)
    

    gmsh.model.geo.addCurveLoop([ab, bc, cd, da], 1)
    gmsh.model.geo.addCurveLoop([ef, fg, gh, he], 2)
    gmsh.model.geo.addCurveLoop([ab, bf, -ef, -ae], 3)
    gmsh.model.geo.addCurveLoop([bc, cg, -fg, -bf], 4)
    gmsh.model.geo.addCurveLoop([cd, dh, -gh, -cg], 5)
    gmsh.model.geo.addCurveLoop([da, ae, -he, -dh], 6)


    gmsh.model.geo.addPlaneSurface([1], 1)
    gmsh.model.geo.addPlaneSurface([2], 2)
    gmsh.model.geo.addPlaneSurface([3], 3)
    gmsh.model.geo.addPlaneSurface([4], 4)
    gmsh.model.geo.addPlaneSurface([5], 5)
    gmsh.model.geo.addPlaneSurface([6], 6)
    surfaceLoop = gmsh.model.geo.addSurfaceLoop([1, 2, 3, 4, 5, 6])
    gmsh.model.geo.addVolume([surfaceLoop], 1)

    gmsh.model.geo.synchronize()

    # Add groups
    gmsh.model.addPhysicalGroup(3, [1], name = "Volume")

    gmsh.model.mesh.generate(3)
    gmsh.write("tmp.msh")

    gmsh.finalize()

    # Convert 

    mesh = meshio.read("tmp.msh")
    mesh.write(out, binary=True) 

def print_usage():
    print("Usage: generate_unit_cube.py filename.vtk/vtu mesh_resolution. Example: generate_unit_cube.py coarse.vtk 0.25")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print_usage()
    else:
        output = sys.argv[1]
        res = float(sys.argv[2])
        generate_unit_cube_vtk(output, res)
