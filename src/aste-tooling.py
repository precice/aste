#!/usr/bin/env python3
import argparse
from asteEvaluate import Calculator
from astePartition import MeshPartitioner
from asteJoin import MeshJoiner


class asteTools():
    def __init__(self) -> None:
        self.args = argparse.Namespace
        self.parse_args()
        tool = self.args.tool
        if tool == "evaluate":
            Calculator()
        elif tool == "join":
            MeshJoiner()
        else:
            MeshPartitioner()

    def parse_args(self) -> None:
        parser = argparse.ArgumentParser(description="ASTE toolset for manupulating meshes.")
        parser.add_argument("tool", metavar="tool", choices=[
                            "join", "partition", "evaluate"], help="Tool for manupulating mesh.")
        parser.parse_known_args(namespace=self.args)


if __name__ == "__main__":
    asteTools()
