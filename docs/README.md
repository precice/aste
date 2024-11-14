---
title: Artificial Solver Testing Environment (ASTE)
permalink: tooling-aste.html
keywords: tooling, aste
summary: "ASTE is a lightweight wrapper around the preCICE API, which allows emulating participants to investigate simulation setups."
---

## Motivation

ASTE is a collection of tools that can be used to reproduce and evaluate particular setups without using actual solver codes. There are two common use-cases, where this is particularly useful:

1. Reproducing a specific mapping setup of a coupled case, e.g., a case crashes since the mapping fails or the mapping seems to behave unexpected. ASTE allows to rerun such a case (in parallel if needed) and investigate the mapping in terms of accuracy as well as runtime.

2. Replay mode, where we replace a participant in a coupled setup with ASTE resulting in a uni-directional coupling. This is useful for debugging, for developing new adapters, but also for efficiency reasons (explicit instead of implicit coupling, no computationally demanding solver needs to be executed).

## Citing

If you use this software, please cite our article in the Journal of Open Source Software:

DOI: [10.21105/joss.07127](https://doi.org/10.21105/joss.07127)

[![DOI](https://joss.theoj.org/papers/10.21105/joss.07127/status.svg)](https://doi.org/10.21105/joss.07127)

## Installation

The core module, which interfaces with preCICE, is called `precice-aste-run` and written in C++. In addition, ASTE offers several tools for pre- and post-processing purposes written in python.

### Dependencies

The C++ core module of ASTE depends on a C++ compiler, `CMake`, `MPI`, `Boost`, `VTK` and `preCICE`. Many of these dependencies are similar to dependencies of preCICE itself. In particular, the C++ compiler, `CMake`, `MPI` and `Boost`. Have a look at the [corresponding preCICE documentation](https://precice.org/installation-source-dependencies.html) for required versions and on how to install these dependencies if needed. In addition, ASTE relies on `preCICE` (version >= 3.0) and the `VTK` library (version >= 7) to handle mesh files.

Detailed installation instructions for the preCICE library are available in the preCICE [installation documentation](https://precice.org/installation-overview.html). On Ubuntu, e.g., [system packages](https://precice.org/installation-packages.html#ubuntu) are availble through [GitHub releases](https://github.com/precice/precice/releases) and can be installed through the package manager, e.g.,

```bash
wget https://github.com/precice/precice/releases/download/<VERSION>/libprecice<VERSION>.deb
sudo apt install ./libprecice<VERSION>.deb
```

The VTK library can be installed using the package manager directly (`libvtk<VERSION>-dev`), e.g., on Ubuntu

```bash
sudo apt install libvtk9-dev
```

{% important %}
The VTK package also installs a compatible python interface to VTK, which is used in ASTE. If you already have a python VTK installation on your system (e.g. through pip), make sure that your python-vtk version is compatible with your C++ VTK version.
{% endimportant %}

However, a packaged VTK version combined with the python interface is known to be rather fragile:

- For VTK 9, particularly the [vtkXMLParser](https://github.com/precice/aste/pull/182#issuecomment-2012144407) is broken.
- For VTK 7, the python interface is incompatible with more recent versions of numpy (messages like `np.bool` was a deprecated alias for the builtin `bool`...) and the `xmlParser` might not work either.

Therefore, a [manual installation of VTK](https://docs.vtk.org/en/latest/build_instructions/build.html#obtaining-the-sources) is the safest way to install VTK on your operating system. Once the sources are downloaded, you can use `cmake` to configure and build the project as follows:

```bash
cmake -DCMAKE_INSTALL_PREFIX="/path/to/install" -DVTK_WRAP_PYTHON="ON" -DVTK_USE_MPI="ON" -DCMAKE_BUILD_TYPE=Release ..
```

This configuration installs the required python bindings along with VTK. The python bindings will be installed in your `CMAKE_INSTALL_PREFIX/lib/<PYTHON-VERSION>/site-packages` (as opposed to the pip packages, which are typically installed in the `dist-packages` directory). You might need to add the `site-package` directory to your `PYTHONPATH` to make it discoverable for python:

```bash
export PYTHONPATH="CMAKE_INSTALL_PREFIX/lib/<PYTHON-VERSION>/site-packages:$PYTHONPATH"
```

As an optional dependency for pre-processing, METIS can be installed. METIS is a graph partitioning library used for topological partitioning in the mesh partitioner and can be installed similarly via apt

```bash
sudo apt install libmetis-dev
```

The python tools require

- NumPy
- sympy (optional)
- jinja2 (optional)
- scipy (optional)

which can be installed directly using pip and the `requirements.txt` file in the repository

```bash
pip3 install -r requirements.txt
```

### Building and installation

In order to build ASTE, download the [latest release](https://github.com/precice/aste/releases/latest) (or clone the `master` branch of the project repository) and use the usual `CMake` steps to steer the installation procedure:

```bash
git clone --branch master https://github.com/precice/aste.git
cd aste && mkdir build && cd build
cmake .. && make
```

{% tip %}
You can use `ctest` in order to check that the building procedure succeeded: Run `ctest`. If you face failing tests, `ctest --output-on-failure` helps to boil down the issue. Make sure you read the [notes on VTK](https://precice.org/tooling-aste.html#dependencies).
{% endtip %}

In order to install ASTE and the associated tools system-wide, execute

```bash
make install
```

which might require root permission.

## Command line interface

After the installation procedure, the following executables are available

- `precice-aste-run`: core module interfacing with preCICE
- `precice-aste-evaluate`: python tool to compute and store data on mesh files
- `precice-aste-partition`: python tool to partition a single mesh file into several ones for parallel runs
- `precice-aste-join`: python tool to join several mesh files into a single mesh file for parallel runs.

All ASTE tools are executed from the command line and running a particular executable with `--help` prints a complete list of available command line arguments and their meaning. There is also an ASTE tutorial [in the preCICE tutorials](https://precice.org/tutorials-aste-turbine.html).

The following subsections explain each part of ASTE in more detail. All ASTE modules have the following three command line arguments in common

| Flag       | Explanation          |
| ---------- | -------------------- |
| `--mesh`   | The mesh filename/prefix used as input |
| `--data`   | Name of data array (input or output depending on the module)  |
| `--output` | The mesh filename used to store the output mesh      |

### precice-aste-run

`precice-aste-run` calls the preCICE API and can be executed in serial as well as in parallel (using MPI). As stated in the introduction, there are two different use-cases, one for investigating mappings and one for replacing participants in a coupled scenario (replay mode). Configuring the replay mode in ASTE relies on a `json` configuration file (see further below). Therefore, the replay mode takes usually only the `--aste-config <FILE.json>` option as a command line argument. All other command line arguments are mostly used for reproducing mappings.

| Flag            | Explanation                                                            |
| --------------- | ---------------------------------------------------------------------- |
| `--aste-config` | ASTE configuration file (only used for replay mode)                    |
| `-v`            | Enables verbose logging output from preCICE                            |
| `-a`            | Enables additional logging from all secondary ranks                    |
| `-c`            | To specify preCICE configuration file (default=`"precice-config.xml"`) |
| `-p`            | Participant name, which can take the arguments `A` or `B`              |
| `--vector`      | A bool switch to specify vector data (default=`False`)                 |

{% note %}
The input mesh filename passed with the `--mesh` option does not need to coincide with the mesh names defined in the preCICE configuration file.
{% endnote %}

For example, mapping the data "dummyData" from a mesh named `fine_mesh.vtk` to an output mesh `coarse_mesh.vtk` and saving the resulting mesh into the variable "mappedData" on the mesh `mappedMesh` would read as follows:

```bash
precice-aste-run -p A --mesh fine_mesh --data "dummyData"
precice-aste-run -p B --mesh coarse_mesh --data "mappedData" --output mappedMesh
```

While the example above executes the mapping in serial, `precice-aste-run` can be executed in parallel (using MPI). However, this requires a partitioned mesh (one per parallel rank). In order to decompose a single mesh appropriately, the tools `precice-aste-partition` and `precice-aste-join` can be used.

{% tip %}
If you want to reproduce a specific setup of your solvers, you can use the [export functionality](https://precice.org/configuration-export.html#enabling-exporters) of preCICE and use the generated meshes directly in `precice-aste-run`. If you run your solver in parallel, preCICE exports the decomposed meshes directly, so that no further partitioning is required.
{% endtip %}

### precice-aste-partition

Reads a single mesh file (either `.vtk` or `.vtu` extension) and partitions it into several mesh files. The resulting mesh files are are stored as `output_1.vtu, output_2.vtu, ...`. There are three algorithms available in order to execute the partitioning. The `meshfree` and `uniform` algorithm are rather simple algorithms, which don't require any mesh topology information. The `topological` algorithm relies on the optional dependency METIS and is more powerful, but needs topology information.

| Flag          | Explanation                                                                                 |
| ------------- | ------------------------------------------------------------------------------------------- |
| `--directory` | Output directory (optional)                                                                 |
| `--numparts`  | The number of parts to split the mesh into                                                  |
| `--algorithm` | Algorithm used for determining the partitioning (options="meshfree", "topology", "uniform") |

Example: to divide a mesh into two parts using the `topological` partitioning and store it in a directory:

```bash
precice-aste-partition --mesh MeshA.vtk --algorithm topology --numparts 2 --output fine_mesh --directory partitioned_mesh
```

{% note %}
METIS is written in C++ and used through a library interface called `libMetisAPI`. Please check your ASTE installation in case you face issues with `libMetisAPI`.
{% endnote %}

{% note %}
`precice-aste-partition` creates also a `recovery.json` file in order to store connectivity information between the individual mesh files. The recovery file is optional and allows to restore the original connectivity information.
{% endnote %}

### precice-aste-join

Reads a partitioned mesh from a given prefix (looking for `<prefix>_<#filerank>.vtu)`) and saves it to a single `.vtk` or `.vtu` file.
The `-r` flag also recovers the connectivity information across several ranks from a mesh, partitioned using `precice-aste-partition`.

| Flag         | Explanation                                                                           |
| ------------ | ------------------------------------------------------------------------------------- |
| `--recovery` | The path to the recovery file to fully recover connectivity information across ranks. |
| `--numparts` | The number of parts to read from the input mesh. By default, the entire mesh is read. |
| `--log`      | Logging level (default="INFO")                                                        |

For example, to join a partitioned mesh using a recovery file:

```bash
precice-aste-join --mesh partitoned_mesh_directory/partitioned_mesh --recovery partitioned_directory --output rejoined_mesh.vtk
```

### precice-aste-evaluate

While the previous two tools of ASTE handled the meshes for parallel runs, `precice-aste-evaluate` takes care of pre- and postprocessing the actual data on the meshes. `precice-aste-evaluate` reads a mesh as either `.vtk` or `.vtu`, evaluates a function on the mesh given by `--function` on it and stores the resulting data on this particular mesh. When using the `--diff` flag, the tool can also compute the difference between the data values already stored on the mesh and the function values (usually applied after a mapping). The `diff` flag also reports common error metrics such as the l2-norm and minimum or maximum errors on the mesh

| Flag               | Explanation                                                                         |
| ------------------ | ----------------------------------------------------------------------------------- |
| `--function`       | The function which should be evaluated on the mesh (see below for examples).        |
| `--list-functions` | Prints a list of predefined functions.                                              |
| `--diff`           | Calculates the difference between `--diffdata` and the given function.              |
| `--diffdata`       | The name of the data to compute the difference used in `diff` mode. If not given, --data is used. |
| `--log`            | Logging level (default="INFO")                                                      |
| `--dir`            | Output directory (optional)                                                         |
| `--stat`           | Store statistics of the difference calculation in a separate file called `mesh.stats.json` |
| `--gradient`       | Calculate and store gradient data in addition to the given input function on the mesh.|

The predefined functions are a collection of common interpolation functions, which are usually too cumbersome for the command line:

| Function   | Explanation                                                                             |
| ---------- | --------------------------------------------------------------------------------------- |
| franke     | Franke's function has two Gaussian peaks of different heights, and a smaller dip.       |
| eggholder  | A function with many local extrema.                          |
| rosenbrock | A function having a global minimum in a narrow, parabolic valley. |

All function provided have 3D and 2D variants (which should be applied depending on your mesh topology). Example: calculate and store the Eggholder function on given mesh

```bash
precice-aste-evaluate --mesh 3DMesh.vtk --function "eggholder3d" --data "EggHolder"
precice-aste-evaluate --mesh 2DMeshonXY.vtk --function "eggholder2d(xy)" --data "EggHolder"
precice-aste-evaluate --mesh 2DMeshonXZ.vtk --function "eggholder2d(xz)" --data "EggHolder"
precice-aste-evaluate --mesh 2DMeshonYZ.vtk --function "eggholder2d(yz)" --data "EggHolder"
```

Example: calculating the function "sin(x)+exp(y)" on mesh `MeshA` and store the result in "MyFunc"

```bash
precice-aste-evaluate --mesh MeshA.vtk --function "sin(x)+exp(y)" --data "MyFunc"
```

Example: calculating the difference between `MappedData` and the analytic function "sin(x)" and storing the resulting difference data in the variable "Error":

```bash
precice-aste-evaluate --mesh Mapped.vtk --function "sin(x)" --diff --diffdata "MappedData" --data "Error"
```

### Replay mode

The replay mode is a bit different from the scenarios we have seen so far. Here, we emulate the behavior of individual participants in a coupled simulation. In order to configure such a scenario, each participant you want to replace needs a configuration file in JSON format with the following attributes:

```json
{
  "participant": "Participant-Name",
  "startdt": "PreCICE mesh dt number (>= 1)",
  "meshes": [
    {
      "mesh": "Mesh name in preCICE config file",
      "meshfileprefix": "/path/to/mesh/file/with/prefix/Mesh-Participant-A",
      "read-data": {
        "vector": ["Vector dataname in preCICE config which has a read type"],
        "scalar": ["Scalar dataname in preCICE config which has a read type"]
      },
      "write-data": {
        "vector": ["Vector dataname in preCICE config which has a write type"],
        "scalar": ["Scalar dataname in preCICE config which has a write type"]
      }
    }
  ],
  "precice-config": "/path/to/precice/config/file/precice-config.xml"
}
```

The JSON configuration file is similar to an adapter configuration file. The above configuration file is an example of a participant with one mesh. The user can add as many meshes as required.

{% important %}
The first entry `mesh` refers to the mesh name in the precice configuration file (e.g. `Solid-Mesh`), whereas the second argument refers to the actual filenames on your system, which are usually generated by preCICE.
{% endimportant %}

#### Step-by-step guide for replay mode

{% note %}
The replay mode only supports explicit coupling schemes.
{% endnote %}

##### Step 1: Setup export of your original coupling

In a first step we have to generate the required mesh and data files of the participant we want to emulate with ASTE. Therefore, we use the [export functionality](https://precice.org/configuration-export.html) of preCICE. After adding the `export` tag in the precice configuration file, start the coupled simulation and run as many time-steps as you need.

As an example, we replace the `Fluid` participant of the [`perpendicular-flap`](https://precice.org/tutorials-perpendicular-flap.html) tutorial by ASTE. Therefore, we first set the export tag on the fluid participant in the configuration file (see below) and then run the simulation with one of the available fluid solvers (e.g. `fluid-openfoam` coupled to `solid-fenics`).

```xml
    <participant name="Fluid">
      ...
      <export:vtk directory="exported-meshes" />
    </participant>
```

##### Step 2: Prepare ASTE and preCICE configuration files

Prepare an ASTE configuration for the solver you want to replace. See above for the corresponding ASTE configuration format. If your previous simulation used an implicit coupling, make sure to change the configuration to an explicit coupling.

Referring to our example: once the simulation is done, the directory `exported-meshes` contains all necessary coupling data in order to use ASTE for the coupled simulation. We create a new directory in the `perpendicular-flap` directory called `fluid-aste` and move the `exported-meshes` into the new directory in order to run ASTE from a separate directory. Since ASTE supports only `explicit` coupling schemes, we switch from an `implicit` coupling scheme to an `explicit` coupling scheme in the preCICE configuration file:

```xml
<coupling-scheme:parallel-explicit>
  <time-window-size value="0.01" />
  <max-time value="5" />
  <participants first="Fluid" second="Solid" />
  <exchange data="Force" mesh="Solid-Mesh" from="Fluid" to="Solid" />
  <exchange data="Displacement" mesh="Solid-Mesh" from="Solid" to="Fluid" />
</coupling-scheme:parallel-explicit>
```

In addition, we create and configure the `aste-config.json` file in the `fluid-aste` directory according to the data names in the `precice-config.xml` file:

```json
{
  "participant": "Fluid",
  "startdt": "1",
  "meshes": [
    {
      "mesh": "Fluid-Mesh",
      "meshfileprefix": "./exported-meshes/Fluid-Mesh-Fluid",
      "read-data": {
        "vector": ["Displacement"]
      },
      "write-data": {
        "vector": ["Force"]
      }
    }
  ],
  "precice-config": "../precice-config.xml"
}
```

##### Step 3: Run your solver and ASTE

Run your solver and ASTE as usual, e.g., execute `myFluidSolver` in one shell and `precice-aste-run` in another shell:

```bash
./myFluidSolver &
precice-aste-run --aste-config solid-config.json
```

ASTE picks up the correct mesh files, extracts the data and passes the data to preCICE.

For our example above, the fluid solver emulation via ASTE can be started by executing

```bash
 precice-aste-run --aste-config aste-config.json
```

in the `fluid-aste` directory. Simply start any solid solver alongside (e.g. `solid-fenics`).
