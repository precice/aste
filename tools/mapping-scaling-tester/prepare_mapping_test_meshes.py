#! /usr/bin/env python3

import argparse
import itertools
import json
import os
import shutil
import subprocess


def parse_arguments(args):
    parser = argparse.ArgumentParser(description="Prepares meshes for a test suite")
    parser.add_argument(
        "-o",
        "--outdir",
        default="cases",
        help="Directory to generate the test suite in.",
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


def prepare_main_mesh(meshdir, name, file, function, force=False):
    main_dir = os.path.join(meshdir, name, "1")
    main_mesh = os.path.join(main_dir, name + ".vtu")
    print("Preparing Mesh {} in {}".format(name, main_dir))

    if os.path.isdir(main_dir):
        if force:
            print("  Regenerating the mesh.")
            shutil.rmtree(main_dir)
        else:
            print("  Mesh already exists.")

            return

    os.makedirs(main_dir, exist_ok=True)
    data_name = "{}".format(function)
    [path_name, tmpfilename] = os.path.split(os.path.normpath(main_mesh))
    subprocess.run(
        [
            "precice-aste-evaluate",
            "--mesh",
            os.path.expandvars(file),
            "--function",
            function,
            "--data",
            data_name,
            "--directory",
            path_name,
            "-o",
            tmpfilename,
        ]
    )


def prepare_part_mesh(meshdir, name, p, force=False):

    if p == 1:
        return

    main_mesh = os.path.join(meshdir, name, "1", name + ".vtu")
    part_dir = os.path.join(meshdir, name, str(p))
    part_mesh = os.path.join(part_dir, name)
    print("Preparing Mesh {} with {} paritions in {}".format(name, p, part_dir))

    if os.path.isdir(part_dir):
        if force:
            print("  Regenerating the partitioned mesh.")
            shutil.rmtree(part_dir)
        else:
            print("  Partitioned mesh already exists.")

            return

    os.makedirs(part_dir, exist_ok=True)
    [path_name, tmpfilename] = os.path.split(os.path.normpath(part_mesh))
    subprocess.run(
        [
            "precice-aste-partition",
            "--mesh",
            main_mesh,
            "--algorithm",
            "meshfree",
            "-o",
            part_mesh,
            "--directory",
            path_name,
            "-n",
            str(p),
        ]
    )


def main(argv):
    args = parse_arguments(argv[1:])
    setup = json.load(args.setup)
    outdir = os.path.normpath(args.outdir)

    if os.path.isdir(outdir):
        print('Warning: outdir "{}" already exisits.'.format(outdir))
    meshdir = os.path.join(outdir, "meshes")
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

        if not os.path.isfile(os.path.expandvars(file)):
            raise Exception(f'\033[91m Unable to open file called "{file}".\033[0m')
        prepare_main_mesh(meshdir, name, file, function, args.force)

        for p in partitions:
            prepare_part_mesh(meshdir, name, p, args.force)

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main(sys.argv))
