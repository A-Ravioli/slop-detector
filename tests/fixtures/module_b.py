"""Module B - part of circular dependency."""

from . import module_a


def function_b():
    """Function in module B."""
    return module_a.ClassA()


class ClassB:
    """Class in module B."""
    pass

