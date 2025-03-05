#! /usr/bin/env python3

import argparse
import itertools
import json
import os
import pathlib
import shutil
import subprocess


def parseArguments(args):
    parser = argparse.ArgumentParser(description="Prepares meshes for a test suite")
    parser.add_argument(
        "-o",
        "--outdir",
        default="cases",
        help="Directory to generate the test suite in.",
        type=pathlib.Path,
    )
    parser.add_argument(
        "-s",
        "--setup",
        type=argparse.FileType("r"),
        default="setup.json",
        help="The test setup file to use.",
    )
    parser.add_argument(
        "-f", "--force", action="store_true", help="Remove existing meshes."
    )

    return parser.parse_args(args)


def prepareMainMesh(
    meshdir: pathlib.Path, name, file: pathlib.Path, function, force=False
):
    mainDir = meshdir / name / "1"
    mainMesh = mainDir / f"{name}.vtu"
    print(f"Preparing Mesh {name} in {mainDir}")

    if mainDir.is_dir():
        if force:
            print("  Regenerating the mesh.")
            shutil.rmtree(mainDir)
        else:
            print("  Mesh already exists.")
            return

    mainDir.mkdir(exist_ok=True, parents=True)
    data_name = f"{function}"
    subprocess.run(
        [
            "precice-aste-evaluate",
            "--mesh",
            file,
            "--function",
            function,
            "--data",
            data_name,
            "--directory",
            mainMesh.parent,
            "-o",
            mainMesh.name,
        ]
    )


def preparePartMesh(meshdir: pathlib.Path, name, p, force=False):

    if p == 1:
        return

    mainMesh = meshdir / name / "1" / f"{name}.vtu"
    partDir = meshdir / name / str(p)
    partMesh = partDir / name
    print("Preparing Mesh {} with {} paritions in {}".format(name, p, partDir))

    if partDir.is_dir():
        if force:
            print("  Regenerating the partitioned mesh.")
            shutil.rmtree(partDir)
        else:
            print("  Partitioned mesh already exists.")
            return

    partDir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "precice-aste-partition",
            "--mesh",
            mainMesh,
            "--algorithm",
            "topology",
            "-o",
            partMesh,
            "--directory",
            partMesh.parent,
            "-n",
            str(p),
        ]
    )


def main(argv):
    args = parseArguments(argv[1:])
    setup = json.load(args.setup)
    outdir: pathlib.Path = args.outdir

    if outdir.is_dir():
        print(f'Warning: outdir "{outdir}" already exisits.')
    meshdir = outdir / "meshes"
    function = setup["general"]["function"]

    partitions = set(
        [int(rank) for pranks in setup["general"]["ranks"].values() for rank in pranks]
    )

    for name, file in set(
        itertools.chain(
            setup["general"]["meshes"]["A"].items(),
            setup["general"]["meshes"]["B"].items(),
        )
    ):
        file = pathlib.Path(os.path.expandvars(file))

        if not file.is_file():
            raise Exception(f'\033[91m Unable to open file called "{file}".\033[0m')
        prepareMainMesh(meshdir, name, file, function, args.force)

        for p in partitions:
            preparePartMesh(meshdir, name, p, args.force)

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv))
