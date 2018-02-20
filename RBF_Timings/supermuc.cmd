#@ wall_clock_limit = 00:10:00
#@ job_type = MPICH
#@ job_name = ASTE_RBF
#@ class = test
#@ island_count = 1
#@ network.MPI = sn_all,not_shared,us
#@ node = 20
#@ tasks_per_node = 28
#@ energy_policy_tag = my_energy_tag
#@ minimize_time_to_solution = yes
#@ output = $(job_name).$(schedd_host).$(jobid).out
#@ error = $(job_name).$(schedd_host).$(jobid).err
#@ initialdir = .
#@ notification=always
#@ notify_user = florian.lindner@ipvs.uni-stuttgart.de
#@ queue

. /etc/profile
. /etc/profile.d/modules.sh

module swap python python/3.5_intel
module load gcc/6

module unload mpi.ibm
module unload mkl
module load mpi.intel

module load petsc/3.8
# ulimit -c unlimited
# export I_MPI_DEBUG_COREDUMP=1

python3 timings.py


# cd A
# mpirun -n 2 ../../readMesh -a -c ../precice.xml ../outMesh.txt A &
# cd ..

# cd B
# mpirun -n 2 ../../readMesh -a -c ../precice.xml ../inMesh.txt B
