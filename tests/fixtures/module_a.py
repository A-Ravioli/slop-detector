"""Module A - part of circular dependency."""

from . import module_b


def function_a():
    """Function in module A."""
    return module_b.function_b()


class ClassA:
    """Class in module A."""
    pass

