#! python3 

import json
import os
import argparse
from jinja2 import Template

def generateConfig(template, setup):
    template = Template(template)
    return template.render(setup)


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
                        cases.append({
                            "function": setup["general"]["function"],
                            "mapping": {
                                "name": name,
                                "kind": mapping["kind"],
                                "constraint": constraint,
                                "options": mapping.get("options", "")
                            },
                            "A" : {
                                "ranks": setup["general"]["ranks"].get("A", 1),
                                "mesh": {
                                    "name": inname,
                                    "file": infile,
                                }
                            },
                            "B" : {
                                "ranks": setup["general"]["ranks"].get("B", 1),
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
            )]


def createMasterRunScript(casedirs, dir):
    reldirs = [
        os.path.relpath(casedir, dir)
        for casedir in casedirs
    ]
    content = ["#!/bin/bash",
               "",
               'cd "$( dirname "${BASH_SOURCE[0]}" )"',
               ""] + [
                   "/bin/bash {} 2>&1 | tee {}".format(
                       os.path.join(reldir, "run.sh"),
                       os.path.join(reldir, "run.log")
                   )
                   for reldir in reldirs
               ]
    open(os.path.join(dir, "runall.sh"),"w").writelines([ line + "\n" for line in content ])


def createRunScript(outdir, path, case):
    amesh = case["A"]["mesh"]["name"]
    aranks = case["A"]["ranks"]
    ameshLocation = os.path.relpath(os.path.join(outdir, "meshes", amesh, str(aranks), amesh), path)

    acmd = "preciceMap -v -p A --mesh {} &".format(ameshLocation)
    if aranks > 1: acmd.append("mpirun -n {} ".format(aranks))

    bmesh = case["B"]["mesh"]["name"]
    branks = case["B"]["ranks"]
    bmeshLocation = os.path.relpath(os.path.join(outdir, "meshes", bmesh, str(branks), bmesh), path)

    bcmd = "preciceMap -v -p B --mesh {} --output mapped".format(bmeshLocation)
    if branks > 1: bcmd.append("mpirun -n {} ".format(branks))

    content = [
        "#!/bin/bash",
        'cd "$( dirname "${BASH_SOURCE[0]}" )"',
        "echo '=========='",
        "echo '= {} ({}) {} - {}'".format(
            case["mapping"]["name"],
            case["mapping"]["constraint"],
            amesh, bmesh
        ),
        "echo '=========='",
        "",
        acmd,
        bcmd,
        ""
    ]

    if (branks == 1):
        copycmd = "cp {}.conn.txt mapped.conn.txt".format(bmeshLocation)
        diffcmd = "eval_mesh.py mapped.txt -o error.vtk --diff --stats \"{}\" | tee diff.log".format(case["function"])
        content += [copycmd, diffcmd]
    else:
        joincmd = "join_mesh.py mapped -r {} -o result.vtk".format(bmeshLocation)
        diffcmd = "eval_mesh.py result.vtk -o error.vtk --diff --stats \"{}\" | tee diff.log".format(case["function"])
        content += [joincmd,diffcmd]
    open(os.path.join(path, "run.sh"),"w").writelines([ line + "\n" for line in content ])



def setupCases(outdir, template, cases):
    casedirs = []
    for case in cases:
        name = [outdir] + getCaseFolders(case)
        path=os.path.join(*name)
        casedirs.append(path)
        config=os.path.join(path, "precice.xml")

        os.makedirs(path, exist_ok=True)
        with open(config, "w") as config:
            config.write(generateConfig(template, case))
        createRunScript(outdir, path, case)

    createMasterRunScript(casedirs, outdir)


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
