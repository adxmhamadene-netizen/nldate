import sys

from nldate.parser import parse

__all__ = ["parse"]


def main() -> None:
    print(parse(" ".join(sys.argv[1:])))
