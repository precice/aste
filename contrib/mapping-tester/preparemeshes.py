import json
import os
import argparse
import subprocess
import itertools

def parseArguments(args):
    parser = argparse.ArgumentParser(description="Prepares meshes for a test suite")
    parser.add_argument('-o', '--outdir', default="cases", help='Directory to generate the test suite in.')
    parser.add_argument('-s', '--setup', type=argparse.FileType('r'), default="setup.json", help='The test setup file to use.')
    return parser.parse_args(args)


def prepareMainMesh(meshdir, name, file, function):
    mainDir = os.path.join(meshdir, name, "1")
    mainMesh = os.path.join(mainDir, name+".txt")
    print("Preparing Mesh {} in {}".format(name, mainDir))

    os.makedirs(mainDir, exist_ok=True)
    subprocess.run(["eval_mesh.py", file, "-o", mainMesh, function])


def preparePartMesh(meshdir, name, p):
    assert(p > 1)
    mainMesh = os.path.join(meshdir, name, "1", name+".txt")
    partDir = os.path.join(meshdir, name, str(p))
    partMesh = os.path.join(partDir, name+".txt")
    print("Preparing Mesh {} with {} paritions in {}".format(name, p, partDir))

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

    for name, file in itertools.chain(setup["meshes"]["A"].items(), setup["meshes"]["B"].items()):
        prepareMainMesh(meshdir, name, file, function)
        for p in partitions:
            preparePartMesh(meshdir, name, p)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
