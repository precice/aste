---
title: 'ASTE: An artificial solver testing environment for partitioned coupling with preCICE'
tags:
  - C++
  - Python
  - multiphysics
  - partitioned coupling
  - preCICE
authors:
  - name: David Schneider
    orcid: 0000-0002-3487-9688
    corresponding: true # (This is how to denote the corresponding author)
    affiliation: "1" # (Multiple affiliations must be quoted)
  - name: Kürşat Yurt
    orcid: 0000-0001-6497-3184
    affiliation: "2"
  - name: Frédéric Simonis
    orcid: 0000-0003-3390-157X
    affiliation: "1"
  - name: Benjamin Uekermann
    orcid: 0000-0002-1314-9969
    affiliation: "1" # (Multiple affiliations must be quoted)
affiliations:
 - name: Institute for Parallel and Distributed Systems, University of Stuttgart, Germany
   index: 1
 - name: TUM School of Engineering and Design, Technical University of Munich, Germany
   index: 2
date: 13 August 2017
bibliography: paper.bib

# Optional fields if submitting to a AAS journal too, see this blog post:
# https://blog.joss.theoj.org/2018/12/a-new-collaboration-with-aas-publishing
---

<!-- A summary describing the high-level functionality and purpose of the software for a diverse, non-specialist audience. -->

# Summary

Simulating multi-physics phenomena for real-world applications states various challenges in scientific computing.
The behavior of individual physical domains involved is often described through distinct partial-differential equations, which need to be solved in a certain subdomain.
Their interaction is then achieved through bidirectional exchange of suitable coupling data between all subdomains.
Partitioned coupling tackles multi-physics simulations by glueing together separate models, typically implemented in separate software environments.
To facilitate such partitioned multi-physics simulations effectively, so-called coupling libraries offer commonly required functionality.
We focus in particular on coupling through the open-source library preCICE [@precice-reference], which offers functionality for data communication, data mapping, coupling schemes, and more.
In the most basic setup, at least two executables call preCICE to perform a coupled simulation.
As additional software components, so-called adapters bridge the gap between the preCICE API and the software environments used by the coupled models.
Creating and using this overall setup for early development purposes is not only cumbersome, but also very inefficient.
The artificial solver testing environment (ASTE) allows to replace and imitate models coupled via preCICE by artificial ones, potentially in parallel distributed across multiple ranks on distributed memory.
This helps in the development of preCICE, adapters, or simulation setups by reducing the necessary software components and simplifying execution workflows.
In addition, ASTE provides performance and accuracy metrics of the configured simulation setup.

# Statement of need

<!-- We need to put the figure first, otherwise the reference won't be rendered correctly -->
![Dependency graph for a coupled simulation with FEniCS and OpenFOAM compared to a dependency graph using ASTE.\label{fig:dependency-graph}](dependency-graph.pdf)

\autoref{fig:dependency-graph} illustrates the software stack required for a coupled simulation setup using FEniCS and OpenFOAM as examples, and compares it to a simulation setup using ASTE.
Beside preCICE itself, core ingredients for practical applications are preCICE API language bindings, preCICE adapters, the simulation frameworks and their dependencies.
Note that the framework dependencies are usually heavy by themselves, e.g., packages such as PETSc or Trilinos.
ASTE, on the other hand, replaces coupled models and only requires a reduced set of dependencies.
It abstracts the computational complexity of the models away by extracting the relevant information from VTK files instead and passing extracted data to preCICE, potentially in parallel on distributed memory.
While the VTK files may stem from actual simulations, ASTE can also generate artificial VTK files with prescribed coupling data.
This makes ASTE a lightweight and valuable tool for the development of preCICE to test new features on real-world applications in an artificial solver-like setup, e.g., for developing new communication algorithms [@Lindner2019; @Totounferoush2021] or to develop new mapping methods, e.g., [@Ariguib2022; @precice-reference; @Martin2022; @Schneider2023].
In fact, testing and developing preCICE was the use case behind the first prototype of ASTE, which was developed as part of @Lindner2019.
Beyond the development in preCICE, ASTE also fosters the development of new adapter codes to be coupled via preCICE, as it aids in debugging and enhances the transparency of data flow.

Another crucial argument for emulating models is computational efficiency.
For coupled simulations, the main computational load is typically carried by the models instead of the coupling library.
Hence, running the original models repeatedly for development purposes of preCICE or adapter components is inefficient.
However, this does not only hold for software development, but also for parameter tuning for real-world applications, where the execution of involved models might become prohibitively expensive already due to the problem size.
In this regard, the entire tool chain of ASTE enables to easily alter the simulation setup through different partitioning schemes or different configuration settings of preCICE.
For the configuration of data mappings particularly, ASTE can evaluate additional accuracy metrics.
Combined with the performance instrumentation of preCICE itself, this enables finding appropriate settings for specific scenarios (e.g. as demonstrated in the large-scale example in @ExaFSA2020).

Lastly, ASTE provides a reproducible environment which enables to share and rerun scenarios, regardless of the availability of involved software components (e.g. through the [preCICE forum](https://precice.discourse.group/)).

# Functionality & Use

The central interface of ASTE is given through a VTK mesh file, which contains information about the geometric shape of the model we emulate.
The VTK files can be generated from mesh generation tools (e.g., GMSH [@gmsh]), [Python scripts](https://github.com/precice/aste/tree/develop/tools/mesh-generators) or directly [retrieved from preCICE](https://precice.org/configuration-export.html).
Given a VTK file, ASTE offers different algorithms to repartition them (e.g., through METIS [@METIS]) for parallel runs.
Moreover, ASTE can generate artificial data on the geometry and store them in the VTK file format.
The core module of ASTE then reads the VTK file and passes the data to preCICE, potentially in every time step of the coupled simulation.
Once the simulation is finished, the generated data is stored in another VTK file and can be compared against the originial artificial data.
Performance metrics are accessible through the [preCICE performance framework](https://precice.org/tooling-performance-analysis.html).

While the core module of ASTE is written in C++, the pre- and postprocessing scripts are implemented in Python.
The core module relies on VTK [@vtkBook], [Boost](https://boost.org/) and MPI for parallel execution.
It provides a command line interface for simple simulations and can be configured in JSON [@lohmann2023] for more complex scenarios.

ASTE is hosted on [GitHub](https://github.com/precice/aste) and releases are published using [GitHub releases](https://github.com/precice/aste/releases).
The documentation is part of the [ASTE repository](https://github.com/precice/aste/blob/develop/docs/README.md) and rendered on [the preCICE website](https://precice.org/tooling-aste.html).
In addition, a [tutorial](https://precice.org/tutorials-aste-turbine.html) and [ready-to-use examples](https://github.com/precice/aste/tree/develop/examples) are available.
Building is handled via [CMake](https://cmake.org/) and, as part of the preCICE distribution [@preciceDistribution], ASTE can be used through a [Vagrant box](https://github.com/precice/vm).

# Acknowledgements

The authors are funded by the Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) under project number 515015468 and under Germany's Excellence Strategy - EXC 2075 -- 390740016. We acknowledge the support of the Stuttgart Center for Simulation Science (SimTech).

# References
