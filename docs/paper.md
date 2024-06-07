---
title: 'ASTE: An artificial solver testing environment for partitioned coupling'
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
  - name: Benjamin Uekermann
    orcid: 0000-0002-1314-9969
    affiliation: "1" # (Multiple affiliations must be quoted)
affiliations:
 - name: Institute for Parallel and Distributed Systems, University of Stuttgart, Germany
   index: 1
 - name: Institution Name, Country
   index: 2
 - name: Independent Researcher, Country
   index: 3
date: 13 August 2017
bibliography: paper.bib

# Optional fields if submitting to a AAS journal too, see this blog post:
# https://blog.joss.theoj.org/2018/12/a-new-collaboration-with-aas-publishing
---

<!-- TODO: Make sure we don't exceed 35 lines in the markdown file -->
<!-- A summary describing the high-level functionality and purpose of the software for a diverse, non-specialist audience. -->

# Summary

Simulating multi-physics phenomenon for real-world applications states various challenges in scientific computing.
The behavior of individual physical domains involved is described through distinct partial-differential equations, which need to be solved in each subdomain.
Their interaction is then achieved through the bidirectional exchange of suitable boundary conditions between all subdomains.
Partitioned coupling tackles multi-physics simulations by glueing together separate models, typically implemented in a separate software environemnt, which solve one subdomain.
Coupling libraries offer common functionality to facilitate such partitioned multi-phyics simulations.
We focus in particular on the coupling library preCICE [@precice-reference], which offers functionality for data communication, data mapping, coupling schemes and more.
The artificial solver testing environment (ASTE) allows to replace models coupled via preCICE by artificial ones, giving users insight into performance and accuracy metrics of their coupled simulation as well as helping in development.

# Statement of need

ASTE fits a variety of use cases.

- configuration of a specific scenario [@ExaFSA2020]
- adapter development
- preCICE development [e.g., @Lindner2019; @Totounferoush2021] [@Schneider2023] [@Martin2022] [Ariguib2022]
- reproducibility [@preciceDistribution]

Configuring a coupled simulation and the options offered by preCICE from the user perspective might become a challenging task.
 especially for large-scale scenarios, where executing the individual models becomes prohibitevly expensive.
A Statement of need section that clearly illustrates the research purpose of the software and places it in the context of related work.

# Functionality & Use

[@vtkBook] [@METIS]
JSON[@lohmann2023]
MPI
[Boost](https://boost.org/).
Mention (if applicable) a representative set of past or ongoing research projects using the software and recent scholarly publications enabled by it. (Here?)
Given this format, a “full length” paper is not permitted, and software documentation such as API (Application Programming Interface) functionality should not be in the paper and instead should be outlined in the software documentation.

via [GitHub releases](https://github.com/precice/aste/releases)
[documentation](https://precice.org/tooling-aste.html)
written in C++ and Python, hosted on [GitHub](https://github.com/precice/aste), uses [CMake](https://cmake.org/)

# Acknowledgements

The authors are funded by the Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) under project number 515015468 and under Germany's Excellence Strategy - EXC 2075 -- 390740016. We acknowledge the support of the Stuttgart Center for Simulation Science (SimTech).

# References
