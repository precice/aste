#! /usr/bin/env python3

import argparse
import json
import os
import shutil
import subprocess
import sys


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
    parser.add_argument("-g", "--generator", help="The generator to use.")
    parser.add_argument("-d", "--dim", default=3, help="The dimension of the mesh.")
    parser.add_argument("--seed", default=0, help="The seed for the mesh generator.")
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
    [path_name, _] = os.path.split(os.path.normpath(part_mesh))
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


def create_mesh(halton_generator_script, file, points, dim=3, seed=0):
    # Ensure the output directory exists
    directory = os.path.dirname(file)
    if not os.path.exists(directory):
        os.mkdir(directory)

    subprocess.run(
        [
            "python3",
            os.path.abspath(halton_generator_script),
            "--mesh",
            file,
            "--numpoints",
            str(points),
            "--dimension",
            str(dim),
            "--seed",
            str(seed),
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
    for points in set(
        [
            setup["general"]["numberofpointsperrank"]["A"],
            setup["general"]["numberofpointsperrank"]["B"],
        ]
    ):
        for partition in partitions:
            filepoints = int(points) * int(partition)
            file = os.path.join(meshdir, f"{filepoints}.vtk")

            create_mesh(args.generator, file, points, args.dim, args.seed)

            if not os.path.isfile(os.path.expandvars(file)):
                raise Exception(f'\033[91m Unable to open file called "{file}".\033[0m')
            prepare_main_mesh(meshdir, str(filepoints), file, function, args.force)

            prepare_part_mesh(meshdir, str(filepoints), partition, args.force)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
