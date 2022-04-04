#!/bin/bash
#
#SBATCH --job-name=astetests
#SBATCH --output=result-turbine.txt
#SBATCH --ntasks=8
#SBATCH --ntasks-per-node=4
#SBATCH --time=3:00:00

source ../../../load.sh
# Set the hostfile for pariticipants A and B
export ASTE_A_MPIARGS=""
export ASTE_B_MPIARGS=""

# Run all cases
bash testcases/$1/cases/runall.sh

# Run the postprocessing
bash testcases/$1/cases/postprocessall.sh

