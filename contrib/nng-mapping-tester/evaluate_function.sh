
cd meshes/original
for m in $( find -name "*.vtk"); do
	FILE="$m"
	FILE="${FILE##*/}"
	FILE="${FILE%.vtk}"
        vtk_calculator.py -m $m -f $1 -d $1 -o ../evaluated/$FILE.vtu
done;	
