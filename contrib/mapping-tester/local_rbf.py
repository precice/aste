#! python3

import sys
import argparse
import itertools
import math
import json


class ArgumentSanitizationError(BaseException):
    def __init__(self, message):
        super().__init__(message)


def sanitize(element, options):
    if (element not in options):
        raise ArgumentSanitizationError(
            f"Argument {element} is not one of the following valid options: {', '.join(options)}"
        )
    return element


def parseArguments(argv):
    # Setup options
    valid_polynomials = set(["on", "separate", "off"])
    valid_types = set([
        "multiquadrics", "inverse-multiquadrics", "volume-splines", "gaussian",
        "compact-tps-c2", "compact-polynomial-c0", "compact-polynomial-c6"
    ])

    # Setup defaults
    default_polynomials = "on,separate"
    default_types = "gaussian"

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-A", "--a-meshes", dest="a", type=str, required=True)
    parser.add_argument("-B", "--b-meshes", dest="b", type=str, required=True)
    parser.add_argument("-p",
                        "--polynomials",
                        default=default_polynomials,
                        type=str)
    parser.add_argument("-t", "--types", default=default_types, type=str)
    parser.add_argument("-n", "--coverage", default="3,5,10,15", type=str)
    parser.add_argument("-o",
                        "--output",
                        default=sys.stdout,
                        type=argparse.FileType('w'))

    args = parser.parse_args(argv[1:])

    # Sanitize arguments
    args.a = [float(e.strip()) for e in args.a.split(",")]
    args.b = [float(e.strip()) for e in args.b.split(",")]
    args.polynomials = [
        sanitize(e, valid_polynomials) for e in args.polynomials.split(",")
    ]
    args.types = [sanitize(e, valid_types) for e in args.types.split(",")]
    args.coverage = [int(e.strip()) for e in args.coverage.split(",")]

    return args


class NotImplementedError(BaseException):
    def __init__(self, type):
        super().__init__(f"The rbf mapping type {type} is not implemented.")


def getConfigurator(type):
    """
    Provides a configuration function for given types of mappings.
    The returned resulting function takes the edge lenght h and the coverage n
    as arguments and returns an option string for the rbf mapping.
    """
    # The various configuration functions
    def gauss(h, n):
        GAUSSIAN_DECAY = 1e-9
        shape = math.sqrt(-math.log(GAUSSIAN_DECAY)) / (float(h) * int(n))
        return f"shape-parameter=\"{shape}\""

    # This dictionary maps a type to a configuration function defined above
    res = {"gaussian": gauss}.get(type)
    if res is None:
        raise NotImplementedError(type)
    return res


def main(argv):
    args = parseArguments(argv)
    sections = []
    # We group by a meshes as we only produce conservative mappings.
    # For conservative mappings, the shape function depends on the edge lenght
    # of mesh a.
    for a in args.a:
        cases = {}
        for polynomial, coverage, type in itertools.product(
                args.polynomials, args.coverage, args.types):
            name = f"{type}-n{coverage}-{polynomial}"
            assert (name not in cases)
            config = getConfigurator(type)(a, coverage)
            cases[name] = {
                "kind": f"rbf-{type}",
                "options": f"{config} polynomial=\"{polynomial}\""
            }
        section = {
            "mapping": {
                "constraints": ["consistent"],
                "cases": cases
            },
            "meshes": {
                "A": [a],
                "B": args.b
            }
        }
        sections.append(section)

    json.dump(sections, args.output, indent=2)


if __name__ == '__main__':
    try:
        main(sys.argv)
    except Exception as e:
        print(e)
        sys.exit(1)
    sys.exit(0)
