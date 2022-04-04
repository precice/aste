#!/bin/bash
#SBATCH --time=24:00:00
#SBATCH -J aste-run
#Output and error (also --output, --error):
#SBATCH -o ./%x.%j.out
#SBATCH -e ./%x.%j.err
#Initial working directory (also --chdir):
#SBATCH -D ./
#SBATCH --exclusive
#SBATCH --partition=PARTITION
#SBATCH --nodes=3
#SBATCH --ntasks-per-node=48
#SBATCH --account=ACCOUNT
#SBATCH --array=1-5

# Partition nodes

echo "JOB ID   ${SLURM_JOBID}"
echo "ARRAY ID ${SLURM_ARRAY_TASK_ID}"
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
. env.sh

# Set the hostfile for pariticipants A and B
export ASTE_A_MPIARGS="-hostfile $(pwd)/A.hosts$SUFFIX"
export ASTE_B_MPIARGS="-hostfile $(pwd)/B.hosts$SUFFIX"

# Run all cases
bash cases$SLURM_ARRAY_TASK_ID/runall.sh

# Run the postprocessing
bash cases$SLURM_ARRAY_TASK_ID/postprocess.sh
