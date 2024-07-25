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
    orcid: xxxxxxxxxxxxx
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
The behavior of individual physical domains involved is described through distinct partial-differential equations, which need to be solved in each subdomain.
Their interaction is then achieved through the bidirectional exchange of suitable coupling data between all subdomains.
Partitioned coupling tackles multi-physics simulations by glueing together separate models, typically implemented in separate software environments.
To facilitate such partitioned multi-physics simulations effectively, so-called coupling libraries offer commonly required functionality.
We focus in particular on coupling through the open-source library preCICE [@precice-reference], which offers functionality for data communication, data mapping, coupling schemes and more.
In the most basic setup, at least two executables call preCICE to perform a coupled simulation.
As an additional software component, a so-called adapter bridges the gap between the preCICE API and the software environment used by the coupled models.
Creating and using this setup for development purposes is not only cumbersome, but also very inefficient.
The artificial solver testing environment (ASTE) allows to replace and imitate models coupled via preCICE by artificial ones, potentially in parallel distributed across multiple ranks on distributed memory.
This helps in the development of preCICE, adapters or simulation setups by reducing the necessary software components and simplifying execution workflows.
In addition, ASTE provides performance and accuracy metrics of the configured simulation setup.

# Statement of need

ASTE fits a variety of use cases for users as well as developers.
From the user perspective, configuring a coupled simulation and the options offered by preCICE might become a challenging task.
The main computational load is typically carried by the models instead of the coupling, such that for large-scale scenarios, executing the individual models to tune the coupling becomes prohibitively expensive..
ASTE abstracts the computational complexity of the models away by emulating the original model behavior, potentially in parallel on distributed memory.
Furthermore, the entire tool chain of ASTE enables to easily alter the simulation setup through different partitioning schemes or different configuration settings of preCICE.
Combined with the performance instrumentation of preCICE itself, users can find appropriate setting for their own scenarios (e.g. as demonstrated in the large-scale example in [@ExaFSA2020]).
In addition, replacing participants of a coupled simulation fosters the development of new adapter codes to be coupled via preCICE, as it aids in debugging, but also for efficiency reasons.
However, ASTE is also a valuable tool for preCICE developer to test new features in an artificial solver-like setup, e.g., for developing new communication algorithms [@Lindner2019; @Totounferoush2021] or to develop new mapping methods [e.g. @Schneider2023; @Schrader2023; @Martin2022; @Ariguib2022].
Lastly, ASTE bridges the gap between users, who report malicious behavior of preCICE (e.g. through the [preCICE forum](https://precice.discourse.group/)), and developers by providing a reproducible environment.

# Functionality & Use

The central interface of ASTE is given through a VTK mesh file, which contains information about the geometric shape of the model we emulate.
The VTK files can be generated from mesh generation tools (e.g., GMSH [@gmsh]), [Python scripts](https://github.com/precice/aste/tree/develop/tools/mesh-generators) or directly [retrieved from preCICE](https://precice.org/configuration-export.html).
Given the VTK file, ASTE offers different algorithms to repartition them (e.g., through METIS [@METIS]) for parallel runs.
Moreover, ASTE can generate artificial data on the geometry and store them in the VTK file format.
The core module of ASTE then reads the VTK file and passes the data to preCICE, potentially in every time step of the coupled simulation.
Once the simulation is finished, the generated data is stored on a VTK file and can be compared against an analytic solution via ASTE.
Performance metrics are accessible through the [preCICE performance framework](https://precice.org/tooling-performance-analysis.html).

While the core module of ASTE is written in C++, the pre- and postprocessing scripts are implemented in Python.
The core module relies on VTK [@vtkBook], [Boost](https://boost.org/) and MPI for parallel execution.
It provides a command line interface for simple simulations and can be configured in JSON [@lohmann2023] for more complex scenarios.

ASTE is hosted on [GitHub](https://github.com/precice/aste) and releases are published using [GitHub releases](https://github.com/precice/aste/releases).
The documentation is part of the [ASTE repository](https://github.com/precice/aste/blob/develop/docs/README.md) and rendered on [the preCICE website](https://precice.org/tooling-aste.html).
In addition, a [well-documented tutorial](https://precice.org/tutorials-aste-turbine.html) as well as [ready-to-use examples](https://github.com/precice/aste/tree/develop/examples) are available.
Building is handled via [CMake](https://cmake.org/) and, as part of the preCICE distribution [@preciceDistribution], ASTE can be used through a [Vagrant box](https://github.com/precice/vm).

# Acknowledgements

The authors are funded by the Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) under project number 515015468 and under Germany's Excellence Strategy - EXC 2075 -- 390740016. We acknowledge the support of the Stuttgart Center for Simulation Science (SimTech).

# References
