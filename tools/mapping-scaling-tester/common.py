import os

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


def getCaseFolders(case):
    return [
        case["mapping"]["name"],
        case["mapping"]["constraint"],
        "{}-{}".format(case["A"]["mesh"]["name"], case["B"]["mesh"]["name"]),
        "{}-{}".format(case["A"]["ranks"], case["B"]["ranks"]),
    ]


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
    common = [
        "#!/bin/bash",
        "",
        'cd "$( dirname "${BASH_SOURCE[0]}" )"',
        "RUNNER=/bin/bash",
        "",
    ]

    # Generate master runner script
    content = common + [
        "${RUNNER} " + os.path.join(case, "runall.sh") for case in casemap.keys()
    ]
    open(os.path.join(dir, "runall.sh"), "w").writelines(
        [line + "\n" for line in content]
    )

    # Generate master postprocessing script
    post = common + [
        "${RUNNER} " + os.path.join(case, "postprocessall.sh")
        for case in casemap.keys()
    ]
    open(os.path.join(dir, "postprocessall.sh"), "w").writelines(
        [line + "\n" for line in post]
    )

    for case, instances in casemap.items():
        # Generate master runner script
        content = common + [
            "${RUNNER} " + os.path.join(*instance, "run-wrapper.sh")
            for instance in instances
        ]
        open(os.path.join(dir, case, "runall.sh"), "w").writelines(
            [line + "\n" for line in content]
        )

        # Generate master postprocessing script
        post = common + [
            "${RUNNER} " + os.path.join(*instance, "post.sh") for instance in instances
        ]
        open(os.path.join(dir, case, "postprocessall.sh"), "w").writelines(
            [line + "\n" for line in post]
        )


def createRunScript(outdir, path, case):
    amesh = case["A"]["mesh"]["name"]
    aranks = case["A"]["ranks"]
    ameshLocation = os.path.relpath(
        os.path.join(outdir, "meshes", amesh, str(aranks), amesh), path
    )

    # Generate runner script
    acmd = '/usr/bin/time -f %M -a -o memory-A.log precice-aste-run -v -p A --data "{}" --mesh {} || kill 0 &'.format(
        case["function"], ameshLocation
    )
    if aranks > 1:
        acmd = "mpirun -n {} $ASTE_A_MPIARGS {}".format(aranks, acmd)

    bmesh = case["B"]["mesh"]["name"]
    branks = case["B"]["ranks"]
    bmeshLocation = os.path.relpath(
        os.path.join(outdir, "meshes", bmesh, str(branks), bmesh), path
    )
    mapped_data_name = case["function"] + "(mapped)"
    bcmd = '/usr/bin/time -f %M -a -o memory-B.log precice-aste-run -v -p B --data "{}" --mesh {} --output mapped || kill 0 &'.format(
        mapped_data_name, bmeshLocation
    )
    if branks > 1:
        bcmd = "mpirun -n {} $ASTE_B_MPIARGS {}".format(branks, bcmd)

    content = [
        "#!/bin/bash",
        "set -e -u",
        'cd "$( dirname "${BASH_SOURCE[0]}" )"',
        "echo '=========='",
        "rm -f memory-A.log memory-B.log done running failed",
        "rm -fr mapped && mkdir mapped",
        "touch running",
        "echo '= {} ({}) {} - {}'".format(
            case["mapping"]["name"], case["mapping"]["constraint"], amesh, bmesh
        ),
        "echo '=========='",
        "",
        "set -m",
        "(",
        acmd,
        bcmd,
        "wait",
        ")",
        'if [[ "$?" -eq 0 ]]; then',
        "touch done",
        "else",
        "touch failed",
        "fi",
        "rm -f running",
    ]
    open(os.path.join(path, "run.sh"), "w").writelines(
        [line + "\n" for line in content]
    )

    # Generate wrapper script for runner
    wrapper = [
        "#!/bin/bash",
        'cd "$( dirname "${BASH_SOURCE[0]}" )"',
        "/bin/bash run.sh 2>&1 | tee run.log",
    ]
    open(os.path.join(path, "run-wrapper.sh"), "w").writelines(
        [line + "\n" for line in wrapper]
    )

    # Generate post processing script
    post_content = [
        "#!/bin/bash",
        "set -e -u",
        'cd "$( dirname "${BASH_SOURCE[0]}" )"',
        "echo '= {} ({}) {} - {}'".format(
            case["mapping"]["name"], case["mapping"]["constraint"], amesh, bmesh
        ),
    ]
    if branks == 1:
        joincmd = "[ ! -f mapped.vtu ] || mv --update mapped.vtu mapped.vtk"
        diffcmd = 'precice-aste-evaluate --data error --diffdata "{1}" --diff --stats --mesh mapped.vtk --function "{0}" | tee diff.log'.format(
            case["function"], mapped_data_name
        )
        post_content += [joincmd, diffcmd]
    else:
        [recoveryFileLocation, tmpPrefix] = os.path.split(
            os.path.normpath(bmeshLocation)
        )
        tmprecoveryFile = recoveryFileLocation + "/{}_recovery.json".format(bmesh)
        joincmd = "precice-aste-join --mesh mapped -r {} -o result.vtk".format(
            tmprecoveryFile
        )
        diffcmd = 'precice-aste-evaluate --data error --diffdata "{1}" --diff --stats --mesh result.vtk --function "{0}" | tee diff.log'.format(
            case["function"], mapped_data_name
        )
        post_content += [joincmd, diffcmd]
    open(os.path.join(path, "post.sh"), "w").writelines(
        [line + "\n" for line in post_content]
    )


def setupCases(outdir, template, cases):
    casemap = {}
    for case in cases:
        folders = getCaseFolders(case)
        casemap.setdefault(folders[0], []).append(folders[1:])
        name = [outdir] + folders
        path = os.path.join(*name)
        config = os.path.join(path, "precice-config.xml")

        print(f"Generating {path}")
        os.makedirs(path, exist_ok=True)
        with open(config, "w") as config:
            config.write(generateConfig(template, case))
        createRunScript(outdir, path, case)
    print(f"Generated {len(cases)} cases")

    print(f"Generating master scripts")
    createMasterRunScripts(casemap, outdir)
