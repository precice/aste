#!/bin/bash
#SBATCH --time=24:00:00
#SBATCH -J aste-test
#Output and error (also --output, --error):
#SBATCH -o ./%x.%j.out
#SBATCH -e ./%x.%j.err
#Initial working directory (also --chdir):
#SBATCH -D ./
#SBATCH --exclusive
#SBATCH --partition=all
#SBATCH --nodes=3
#SBATCH --ntasks-per-node=8
#SBATCH --account=ariguiba

# Partition nodes

echo "JOB ID   ${SLURM_JOBID}"
echo

SUFFIX=".${SLURM_JOBID}"

# Parition the SLURM session
rm -f simultan.machines$SUFFIX A.hosts$SUFFIX B.hosts$SUFFIX

for h in $(scontrol show hostname $SLURM_JOB_NODELIST); do
  # This format is specific to Intel MPI
  echo "$h" >> simultan.machines$SUFFIX
done

head -n 1 simultan.machines$SUFFIX > A.hosts$SUFFIX
tail -n +2 simultan.machines$SUFFIX > B.hosts$SUFFIX

# Load your environment here
. /use/local.nfs/Modules/4.7.1/init/profile.sh

# Set the hostfile for pariticipants A and B
export ASTE_A_MPIARGS="-hostfile $(pwd)/A.hosts$SUFFIX"
export ASTE_B_MPIARGS="-hostfile $(pwd)/B.hosts$SUFFIX"

#Run all cases
bash testcases/turbine-small/cases/runall.sh

# Run the postprocessing
bash testcases/turbine-small/cases/postprocessall.sh
