import json
import os
import argparse
from jinja2 import Template

def generateConfig(template, setup):
    template = Template(template)
    return template.render(setup)


def generateCases(setup):
    cases = []

    for name, mapping in setup["mapping"]["cases"].items():
        for constraint in setup["mapping"]["constraints"]:
            for inname, infile in setup["meshes"].items():
                for outname, outfile in setup["meshes"].items():
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

    return cases, setup["meshes"]


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
                   "/bin/bash {}".format(os.path.join(reldir, "run.sh"))
                   for reldir in reldirs
               ]
    open(os.path.join(dir, "runall.sh"),"w").writelines([ line + "\n" for line in content ])


def createRunScript(outdir, path, case):
    amesh = case["A"]["mesh"]["name"]
    aranks = case["A"]["ranks"]
    ameshLocation = os.path.relpath(os.path.join(outdir, "meshes", amesh, str(aranks), amesh), path)
    acmd = "preciceMap -p A --mesh {} &".format(ameshLocation)

    bmesh = case["B"]["mesh"]["name"]
    branks = case["B"]["ranks"]
    bmeshLocation = os.path.relpath(os.path.join(outdir, "meshes", bmesh, str(branks), bmesh), path)
    bmeshOrigLocation = os.path.relpath(os.path.join(outdir, "meshes", bmesh, "1", bmesh), path)
    bcmd = "preciceMap -p B --mesh {} --output mapped &".format(bmeshLocation)
    joincmd = "join_mesh.py mapped -i {} -o result.vtk".format(bmeshOrigLocation)
    diffcmd = "eval_mesh.py result.vtk -o error.vtk --diff \"{}\"".format(case["function"])

    content = [
        "#!/bin/bash",
        'cd "$( dirname "${BASH_SOURCE[0]}" )"',
        "",
        acmd,
        bcmd,
        "",
        joincmd,
        diffcmd,
    ]
    open(os.path.join(path, "run.sh"),"w").writelines([ line + "\n" for line in content ])



def setupCases(outdir, template, cases):
    casedirs = []
    for case in cases:
        name = [outdir] + getCaseFolders(case)
        path=os.path.join(*name)
        casedirs.append(path)
        config=os.path.join(path, "config.xml")

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
    cases, meshes = generateCases(setup)
    outdir = os.path.normpath(args.outdir)
    if (os.path.isdir(outdir)):
        print('Warning: outdir "{}" already exisits.'.format(outdir))

    setupCases(outdir, template, cases)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
