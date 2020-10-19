#! python3

import json
import os
import argparse
import subprocess
import itertools

def parseArguments(args):
    parser = argparse.ArgumentParser(description="Prepares meshes for a test suite")
    parser.add_argument('-o', '--outdir', default="cases", help='Directory to generate the test suite in.')
    parser.add_argument('-s', '--setup', type=argparse.FileType('r'), default="setup.json", help='The test setup file to use.')
    parser.add_argument('-f', '--force', action="store_true", help='Remove existing meshes.')
    return parser.parse_args(args)


def prepareMainMesh(meshdir, name, file, function, force=False):
    mainDir = os.path.join(meshdir, name, "1")
    mainMesh = os.path.join(mainDir, name+".txt")
    print("Preparing Mesh {} in {}".format(name, mainDir))

    if os.path.isdir(mainDir):
        if force:
            print("  Regenerating the mesh.")
            os.removedirs(mainDir)
        else:
            print("  Mesh already exists.")
            return

    os.makedirs(mainDir, exist_ok=True)
    subprocess.run(["eval_mesh.py", file, "-o", mainMesh, function])


def preparePartMesh(meshdir, name, p, force=False):
    assert(p > 1)
    mainMesh = os.path.join(meshdir, name, "1", name+".txt")
    partDir = os.path.join(meshdir, name, str(p))
    partMesh = os.path.join(partDir, name+".txt")
    print("Preparing Mesh {} with {} paritions in {}".format(name, p, partDir))

    if os.path.isdir(partDir):
        if force:
            print("  Regenerating the partitioned mesh.")
            os.removedirs(partDir)
        else:
            print("  Partitioned mesh already exists.")
            return

    os.makedirs(partDir, exist_ok=True)
    subprocess.run(["partition_mesh.py", mainMesh, "-o", partMesh, "-n", str(p)])


def main(argv):
    args = parseArguments(argv[1:])
    setup = json.load(args.setup)
    outdir = os.path.normpath(args.outdir)
    if (os.path.isdir(outdir)):
        print('Warning: outdir "{}" already exisits.'.format(outdir))
    meshdir = os.path.join(outdir, "meshes")
    function =  setup["general"]["function"]

    partitions = set(map(int, setup["general"]["ranks"].values()))
    partitions.discard(1)

    for name, file in set(itertools.chain(setup["general"]["meshes"]["A"].items(), setup["general"]["meshes"]["B"].items())):
        prepareMainMesh(meshdir, name, file, function, args.force)
        for p in partitions:
            preparePartMesh(meshdir, name, p, args.force)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
