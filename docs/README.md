---
title: Artificial Solver Testing Environment (ASTE)
permalink: tooling-aste.html
keywords: tooling, aste
summary: "ASTE is a lightweight wrapper around the preCICE API, which allows you to emulate participants and investigate your simulation setups."
---

## Motivation

ASTE is a collection of tools that can be used to reproduce and evaluate particular setups without using actual solver codes. There are two common use-cases, where this is particularly useful:

1. Reproducing a specific mapping setup of a coupled case, e.g., a case crashes since the mapping fails or the mapping seems to behave unexpected. ASTE allows to rerun such a case (in parallel if needed) and investigate the mapping in terms of accuracy as well as runtime.

2. Replay mode, where we replace a participant in a coupled setup with ASTE resulting in a uni-directional coupling. This is useful for debugging, for developing new adapters, but also for efficiency reasons (explicit instead of implicit coupling, no computationally demanding solver needs to be executed).

## Installation

The core module, which interfaces with preCICE, is called `precice-aste-run` and written in C++. In addition, ASTE offers several tools for pre- and post-processing purposes written in python.

### Dependencies

The C++ core module of ASTE uses similar dependencies as preCICE itself. In particular, ASTE requires a C++ compiler, CMake, MPI and Boost. Have a look at the [corresponding preCICE documentation](https://precice.org/installation-source-dependencies.html) for required versions and on how to install these dependencies if needed. In addition, ASTE relies on preCICE (version >= 2.0) and the VTK library (version >= 7) in order to handle mesh files. The VTK library can be installed using the package manager (`libvtk<VERSION>-dev`), e.g., on Ubuntu

```bash
sudo apt install libvtk9-dev
```

As an optional dependency for pre-processing, METIS can be installed. METIS is a graph partitioning library used for topological partitioning in the mesh partitioner and can be installed similarly via apt

```bash
sudo apt install libmetis-dev
```

The python tools require

- NumPy
- VTK (Visualization Toolkit)
- sympy (optional)

which can be installed directly using pip and the `requirements.txt` file in the repository

```bash
pip3 install -r requirements.txt
```

### Building and installation

In order to build ASTE, clone the project repository and use the usual `CMake` steps to steer the installation procedure: 

```bash
git clone https://github.com/precice/aste.git
mkdir build && cd build
cmake .. && make
```
{% tip %}
You can use `ctest` in order to check that the building procedure succeeded.
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

All ASTE tools are executed from the command line and running a particular executbale with `--help` prints a complete list of available command line arguments and their meaning. There is also an ASTE tutorial [in the preCICE tutorials](https://precice.org/tutorials-aste-turbine.html).

The following subsections explain each part of ASTE more in detail. All ASTE modules have thwe following three command line arguments in common

| Flag     | Explanation          |
| -------- | -------------------- |
| --mesh   | The mesh filename/prefix used as input |
| --data   | Name of data array (input or output depending on the module)  |
| --output | The mesh filename used to store the output mesh      |


### precice-aste-run

`precice-aste-run` calls the preCICE API and can be executed in serial as well as in parallel. As stated in the introduction, there are two different use-cases, one for investigating mappings and one for replacing particiapnts in a coupled scenario (replay mode). Configuring the replay mode in ASTE relies on a `json` configuration file (see further below). Therefore, the replay mode takes usually only the `--aste-config <FILE.json>` option as a command line argument. All other command line arguments are mostly used for reproducing mappings.

| Flag          | Explanation                                                   |
| ------------- | ------------------------------------------------------------- |
| --aste-config | ASTE configuration file (only used for replay mode)           |
| -v            | Enables verbose logging output from preCICE                   |
| -c            | To specify preCICE config file (default="precice-config.xml") |
| -p            | Participant name, which can take the arguemnts `A` or `B`     |
| --vector      | A bool switch to specify vector data (default=`False`)       |

{% important %}
The `--mesh` option here can be different from the mesh defined in the configuration file. ASTE expects here the filename (prefix) of the mesh file (VTK or VTU), which is different from meshes defined in the simulation setup.
{% endimportant %}

For example, mapping the data "dummyData" from a mesh named `fine_mesh.vtk` to an output mesh `coarse_mesh.vtk` and saving the resulting mesh into the variable "mappedData" on the mesh `mappedMesh` would read as follows:

```bash
precice-aste-run -p A --mesh fine_mesh --data "dummyData"
precice-aste-run -p B --mesh coarse_mesh --data "mappedData" --output mappedMesh
```

### precice-aste-evaluate

Reads a mesh as either `.vtk` or `.vtu` and evaluates a function given by `--function` on it. Using the `--diff` flag can compute the difference between the mesh values and the values of the analytical solution (usually applied after a mapping).

| Flag             | Explanation                                                                         |
| ---------------- | ----------------------------------------------------------------------------------- |
| --function       | The function which will be calculated on mesh                                       |
| --list-functions | Prints a list of predefined functions                                               |
| --diffdata       | The name for difference data. Used in diff mode. If not given, --data is used.      |
| --log            | Logging level (default="INFO")                                                      |
| --dir            | Output directory (optional)                                                         |
| --diff           | Calculates the difference between --diffdata and given function.                    |
| --stat           | Store stats of the difference calculation as the separate file inputmesh.stats.json |
| --gradient       | Calculates gradient data for given input function                                   |

There are also some predefined common interpolation functions can by specified here a list of them:

| Function   | Explanation                                                                             |
| ---------- | --------------------------------------------------------------------------------------- |
| franke     | Franke's function has two Gaussian peaks of different heights, and a smaller dip.       |
| eggholder  | A function has many local maxima. It is difficult to optimize.                          |
| rosenbrock | A function that is unimodal, and the global minimum lies in a narrow, parabolic valley. |

All function provided has 3D and 2D variants. For example, to calculate Egg-Holder function on different meshes:

```bash
precice-aste-evaluate --mesh 3DMesh.vtk --function "eggholder3d" --data "EggHolder"
precice-aste-evaluate --mesh 2DMeshonXY.vtk --function "eggholder2d(xy)" --data "EggHolder"
precice-aste-evaluate --mesh 2DMeshonXZ.vtk --function "eggholder2d(xz)" --data "EggHolder"
precice-aste-evaluate --mesh 2DMeshonYZ.vtk --function "eggholder2d(yz)" --data "EggHolder"
```

For example, calculate function "sin(x)+exp(y)" on mesh MeshA and store in "MyFunc" or calculation of difference between mapped data and function "x+y" and "MappedData" and store it in "Error":

```bash
precice-aste-evaluate --mesh MeshA.vtk --function "sin(x)+exp(y)" --data "MyFunc"
precice-aste-evaluate --mesh Mapped.vtk --function "x+y" --data "Error" --diffdata "MappedData" --diff
```

### precice-aste-partition

Reads a mesh either `.vtk` or `.vtu` , partitions it and stores the parts `output_1.vtu, output_2.vtu, ...`. For partitioning, there are there algorithms available. The meshfree and uniform algorithm does not need any mesh topology information, whereas the topological algorithm needs topology information. This python module needs the C++ module `libmetisAPI.so` if the topological algorithm is used.

| Flag        | Explanation                                                                                 |
| ----------- | ------------------------------------------------------------------------------------------- |
| --directory | Output directory (optional)                                                                 |
| --numparts  | The number of parts to split into                                                           |
| --algorithm | Algorithm used for determining the partitioning (options="meshfree", "topology", "uniform") |

For example, to divide a mesh into 2 parts using topological partitioning and store it in a directory:

```bash
precice-aste-partition --mesh MeshA.vtk --algorithm topology --numparts 2 --output fine_mesh --directory partitioned_mesh
```

#### libMetisAPI

This is a small C++ wrapper around METIS. It is only required if `precice-aste-partition` should use a topological algorithm.

### precice-aste-join

Reads a partitioned mesh from a given prefix (looking for `<prefix>_<#filerank>.vtu)`) and saves it to a single `.vtk` or `.vtu` file.
The `-r` flag also recovers the connectivity information from a mesh. Notice that for recovery, partitions should contain `GlobalIDs` data.

| Flag       | Explanation                                                                           |
| ---------- | ------------------------------------------------------------------------------------- |
| --recovery | The path to the recovery file to fully recover its state.                             |
| --numparts | The number of parts to read from the input mesh. By default, the entire mesh is read. |
| --log      | Logging level (default="INFO")                                                        |

For example, to join a partitioned mesh using a recovery file:

```bash
precice-aste-join --mesh partitoned_mesh_directory/partitioned_mesh --recovery partitioned_directory --output rejoined_mesh.vtk
```

#### Replay mode

For the Replay mode ASTE uses a configuration file in JSON format as follows

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

The above configuration file is an example of a participant with one mesh. The user can add as many meshes as required.

#### Step by Step Guide for Replay Mode

The replay mode only supports explicit coupling schemes.

##### Step 1: Setup export of your original coupling

Set vtk or vtu export of the participant you want to replace using preCICE export flag see [Export Configuration](https://precice.org/configuration-export.html)

##### Step 2: Prepare your ASTE Configuration file

Prepare an ASTE configuration for the solver which will be replaced. See above for ASTE configuration format.

#### Step 3: Run your solver and ASTE

Run your solver and ASTE as usual preCICE coupling. At this stage ASTE would work like a solver. Instead of calculation it would just only read from your export mesh data and use them for coupling.
