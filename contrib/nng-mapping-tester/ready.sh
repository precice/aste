
source ../../../load.sh
export ASTE_MESHES=/home/ariguiba/aste/contrib/nng-mapping-tester/meshes/turbine/
./generate.py -s setup-$1.json -o testcases/$1/cases
#mkdir -p meshes/$1/partitioned
#ln -s /home/ariguiba/aste/contrib/nng-mapping-tester/meshes/$1/partitioned /home/ariguiba/aste/contrib/nng-mapping-tester/testcases/$2/cases/meshes
./preparemeshes.py -s setup-$1.json -o testcases/$1/cases 

