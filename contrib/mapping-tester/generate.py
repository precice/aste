#! python3 

import json
import os
import argparse
from jinja2 import Template

def generateConfig(template, setup):
    template = Template(template)
    return template.render(setup)

def as_iter(something):
    try:
        iter(something)
        return something
    except TypeError:
        return [something]


def generateCases(setup):
    meshes = setup["general"]["meshes"]

    cases = []
    for group in setup["groups"]:
        for name, mapping in group["mapping"]["cases"].items():
            for constraint in group["mapping"]["constraints"]:
                for inname in group["meshes"]["A"]:
                    infile = meshes["A"][inname]
                    for outname in group["meshes"]["B"]:
                        outfile = meshes["B"][outname]
                        for ranksA, ranksB in zip(
                                as_iter(setup["general"]["ranks"].get("A", 1)),
                                as_iter(setup["general"]["ranks"].get("B", 1))):
                            cases.append({
                                "function": setup["general"]["function"],
                                "mapping": {
                                    "name": name,
                                    "kind": mapping["kind"],
                                    "constraint": constraint,
                                    "options": mapping.get("options", "")
                                },
                                "A" : {
                                    "ranks": ranksA,
                                    "mesh": {
                                        "name": inname,
                                        "file": infile,
                                    }
                                },
                                "B" : {
                                    "ranks": ranksB,
                                    "mesh": {
                                        "name": outname,
                                        "file": outfile,
                                    }
                                }
                            })

    return cases


def getCaseFolders(case):
    return [case["mapping"]["name"],
            case["mapping"]["constraint"],
            "{}-{}".format(
                case["A"]["mesh"]["name"],
                case["B"]["mesh"]["name"]
            ),
            "{}-{}".format(
                case["A"]["ranks"],
                case["B"]["ranks"]
            )]


def caseToSortable(case):
    parts = case.split(os.path.sep)
    kind = parts[0]
    mesha, meshb = map(float, parts[-2].split("-"))

    kindCost = 0
    if kind.startswith("gaussian"):
        kindCost = 1
    elif kind.startswith("tps"):
        kindCost = 2

    return (kindCost, -mesha, -meshb)


def createMasterRunScripts(casemap, dir):
    common = ["#!/bin/bash",
               "",
               'cd "$( dirname "${BASH_SOURCE[0]}" )"',
               "RUNNER=/bin/bash",
               ""]

    # Generate master runner script
    content = common + [
                   "${RUNNER} " + os.path.join(case, "runall.sh")
                   for case in casemap.keys()
               ]
    open(os.path.join(dir, "runall.sh"),"w").writelines([ line + "\n" for line in content ])

    # Generate master postprocessing script
    post = common + [
                   "${RUNNER} " + os.path.join(case, "postprocessall.sh")
                   for case in casemap.keys()
               ]
    open(os.path.join(dir, "postprocessall.sh"),"w").writelines([ line + "\n" for line in post ])

    for case, instances in casemap.items():
        # Generate master runner script
        content = common + [
                       "${RUNNER} " + os.path.join(*instance, "run-wrapper.sh")
                       for instance in instances
                   ]
        open(os.path.join(dir, case, "runall.sh"),"w").writelines([ line + "\n" for line in content ])

        # Generate master postprocessing script
        post = common + [
                       "${RUNNER} " + os.path.join(*instance, "post.sh")
                       for instance in instances
                   ]
        open(os.path.join(dir, case, "postprocessall.sh"),"w").writelines([ line + "\n" for line in post ])



def createRunScript(outdir, path, case):
    amesh = case["A"]["mesh"]["name"]
    aranks = case["A"]["ranks"]
    ameshLocation = os.path.relpath(os.path.join(outdir, "meshes", amesh, str(aranks), amesh), path)

    # Generate runner script
    acmd = "/usr/bin/time -f %M -a -o memory-A.log preciceMap -v -p A --mesh {} &".format(ameshLocation)
    if aranks > 1: acmd = "mpirun -n {} $ASTE_A_MPIARGS {}".format(aranks, acmd)

    bmesh = case["B"]["mesh"]["name"]
    branks = case["B"]["ranks"]
    bmeshLocation = os.path.relpath(os.path.join(outdir, "meshes", bmesh, str(branks), bmesh), path)

    bcmd = "/usr/bin/time -f %M -a -o memory-B.log preciceMap -v -p B --mesh {} --output mapped &".format(bmeshLocation)
    if branks > 1: bcmd = "mpirun -n {} $ASTE_B_MPIARGS {}".format(branks, bcmd)

    content = [
        "#!/bin/bash",
        'cd "$( dirname "${BASH_SOURCE[0]}" )"',
        "echo '=========='",
        "rm -f memory-A.log memory-B.log done running",
        "touch running",
        "echo '= {} ({}) {} - {}'".format(
            case["mapping"]["name"],
            case["mapping"]["constraint"],
            amesh, bmesh
        ),
        "echo '=========='",
        "",
        acmd,
        bcmd,
        "wait",
        "",
        "rm -f running",
        "touch done"
    ]
    open(os.path.join(path, "run.sh"),"w").writelines([ line + "\n" for line in content ])

    # Generate wrapper script for runner
    wrapper = [
        "#!/bin/bash",
        'cd "$( dirname "${BASH_SOURCE[0]}" )"',
        "/bin/bash run.sh 2>&1 | tee run.log"
    ]
    open(os.path.join(path, "run-wrapper.sh"),"w").writelines([ line + "\n" for line in wrapper ])

    # Generate post processing script
    post_content = [
        "#!/bin/bash",
        'cd "$( dirname "${BASH_SOURCE[0]}" )"',
        "echo '= {} ({}) {} - {}'".format(
            case["mapping"]["name"],
            case["mapping"]["constraint"],
            amesh, bmesh
        ),
    ]
    if (branks == 1):
        copycmd = "cp {}.conn.txt mapped.conn.txt".format(bmeshLocation)
        diffcmd = "eval_mesh.py mapped.txt -o error.vtk --diff --stats \"{}\" | tee diff.log".format(case["function"])
        post_content += [copycmd, diffcmd]
    else:
        joincmd = "join_mesh.py mapped -r {} -o result.vtk".format(bmeshLocation)
        diffcmd = "eval_mesh.py result.vtk -o error.vtk --diff --stats \"{}\" | tee diff.log".format(case["function"])
        post_content += [joincmd,diffcmd]
    open(os.path.join(path, "post.sh"),"w").writelines([ line + "\n" for line in post_content ])


def setupCases(outdir, template, cases):
    casemap = {}
    for case in cases:
        folders = getCaseFolders(case)
        casemap.setdefault(folders[0], []).append(folders[1:])
        name = [outdir] + folders
        path=os.path.join(*name)
        config=os.path.join(path, "precice.xml")

        print(f"Generating {path}")
        os.makedirs(path, exist_ok=True)
        with open(config, "w") as config:
            config.write(generateConfig(template, case))
        createRunScript(outdir, path, case)
    print(f"Generated {len(cases)} cases")

    print(f"Generating master scripts")
    createMasterRunScripts(casemap, outdir)


def parseArguments(args):
    parser = argparse.ArgumentParser(description="Generator for a mapping test suite")
    parser.add_argument('-o', '--outdir', default="cases", help='Directory to generate the test suite in.')
    parser.add_argument('-s', '--setup', type=argparse.FileType('r'), default="setup.json", help='The test setup file to use.')
    parser.add_argument('-t', '--template', type=argparse.FileType('r'), default="config-template.xml", help='The precice config template to use.')
    return parser.parse_args(args)


def main(argv):
    args = parseArguments(argv[1:])
    setup = json.load(args.setup)
    template = args.template.read()
    cases = generateCases(setup)
    outdir = os.path.normpath(args.outdir)
    if (os.path.isdir(outdir)):
        print('Warning: outdir "{}" already exisits.'.format(outdir))

    setupCases(outdir, template, cases)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
