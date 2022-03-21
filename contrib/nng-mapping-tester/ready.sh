
source ../../../load.sh
export ASTE_MESHES=/home/ariguiba/aste/contrib/nng-mapping-tester/meshes/$1/
./generate.py -s setup-$2.json -o testcases/$2/cases
#mkdir -p meshes/$1/partitioned
#ln -s /home/ariguiba/aste/contrib/nng-mapping-tester/meshes/$1/partitioned /home/ariguiba/aste/contrib/nng-mapping-tester/testcases/$2/cases/meshes
./preparemeshes.py -s setup-$2.json -o testcases/$2/cases --gradient
