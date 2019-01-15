#!/usr/bin/zsh
set -e
set -x
#cp ../eval_mesh.py ../join_mesh.py ../read_mesh.py ../preciceDist ../precice.xml ../libmetisAPI.so .
test -f rbc.vtk || wget "https://people.sc.fsu.edu/~jburkardt/data/vtk/rbc_001.vtk" -O rbc.vtk
test -f bunny.vtk || wget -q "https://www.ece.lsu.edu/xinli/Meshing/Data/bunny.vtk" -O bunny.vtk
python eval_mesh.py bunny.vtk -o colored.vtk -f "y = x[:,1]"
python partition_mesh.py colored.vtk -n 2
python partition_mesh.py rbc.vtk -n 2
mpirun -n 2 preciceDist -p A --meshFile colored&
mpirun -n 2 preciceDist -p B --meshFile rbc --output mapped
python join_mesh.py mapped -o result.vtk
