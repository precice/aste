# Mapping tester

The mapping tester is a collection of scripts and templates that lets you generate, run, post-process and collect a huge catersian product of settings.

Settings include: ranks, meshes, and mappings and their settings

For performance profiling, it allows enabling synchronization and configuring repetitions
For mapping tests, it provides post-processing scripts and a configurable reference function

## config-template.xml

This is the setup of ASTE, which will be used.
This doesn't need to be changed for most scenarios.

## setup.json

This describes the setup including general information and execution groups.

General information includes, repetitions, the function to generate data, the rank configuration, and solver meshes.

Each execution group specifies which mapping and constraint to run using which meshes.
This is necessary for running a range of RBFs with mesh-specific configurations.

## generate.py

This generates all cases including run scripts in the given outdir based on `setup.json` and `config-template.xml`.
Meshes are prepared in the next step.

## preparemeshes.py

This looks up input meshes in the general section, evaluates the function to generate data and then partitions them for all requested rank configurations.
These meshes are the written to `outdir/meshes`.
When handling multiple cases, you can symlink them to a single directory to prevent duplication.

## Running

You can use environment variables `ASTE_A_MPIARGS` and `ASTE_B_MPIARGS` to pass custom arguments to `mpirun` for each solver.
This is useful to pin CPUs on a local node or pass hostfiles on a cluster / in a SLURM session.
See more information [on running simulations in our docs](https://precice.org/running-overview.html).

Each case can be run individually using its `run.sh` or every case in sequence using `outdir/runall.sh`.

A finished run generates a file called `done` in the case directory. This allows you to see the amount of finished jobs using:

```bash
find -name done | wc -l
```

## Post processing

This post-processes the mapped meshes and evaluates accuracy metrics of the mapping accuracy.
Hence, this step is only required if you are looking for mapping accuracy results.
Each case can be run individually using its `post.sh` or every case in sequence using `outdir/postprocessall.sh`.

This however can take a very long time. Consider running all post-processing scripts in parallel using GNU parallel:

```bash
find -name post.sh | parallel --bar bash {}
```

Use the saved time to cite the project.

## gatherstats.py

This generates various statistics for each case and aggregates them into a single CSV file.

## plotconv.py

This reads the stats file, averages the runs and plots various convergence statistics.
