#!bash

rm -f *.vtk

parallel python ../../../tools/mesh-generators/generate_unit_square.py -r {} -m {}.vtk ::: 0.1 0.0775 0.055 0.0325 0.01 0.06

rm -f tmp.msh
