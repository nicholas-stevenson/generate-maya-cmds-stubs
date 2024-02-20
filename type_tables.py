from __future__ import annotations

from typing import Tuple, Optional, Union, List, Any, Callable, Literal, Set


def args_to_typehints(argument) -> Optional[str]:
    """This function holds all unique argument occurrences found throughout
    the autodesk documentation.  If any new styles are found in the future,
    updating the table below should account for the new additions.

    The Key side of the dictionary holds the help docs form of the argument's accepted type
    Eg: aimVector=[float, float, float]

    The Value side of the dictionary holds a 2 item list.
    1 : The type-hinted form of this argument
    2 : The Python formatted raw data type form of this argument.

    Example:
        cmds.aimConstraint(aimVector=[float, float, float])

    To generate a docstring for this style of arguments, the results would be:
        Type-hint : Tuple[float, float, float]
        Python    : (float, float, float)
    """
    lookup_table = {
        "boolean": bool,
        "string": str,
        "int": int,
        "float": float,
        "uint": int,
        "[float, float, float]": Tuple[float, float, float],
        "name": str,
        "linear": float,
        "[linear, linear, linear]": Tuple[float, float, float],
        "angle": float,
        "[angle, angle, angle]": Tuple[float, float, float],
        "script": str,
        "time": Union[float, Tuple[float, float]],
        "[float, float]": Tuple[float, float],
        "[float, float, float, float]": Tuple[float, float, float, float],
        "[name, string]": Tuple[str, str],
        "[int, string]": Tuple[int, str],
        "[string, string]": Tuple[str, str],
        "[string, string, string]": Tuple[str, str, str],
        "[string, string, string, string]": Tuple[str, str, str, str],
        "[string, string, string, string, string]": Tuple[str, str, str, str, str],
        "[string, string, string, string, string, string]": Tuple[
            str, str, str, str, str, str
        ],
        "[int, string, int]": Tuple[int, str, int],
        "[int, int]": Tuple[int, int],
        "[int, int, int]": Tuple[int, int, int],
        "[int, int, int, int]": Tuple[int, int, int, int],
        "[int, int, int, int, int]": Tuple[int, int, int, int, int],
        "[int, int, int, int, int, int]": Tuple[int, int, int, int, int, int],
        "[uint, uint]": Tuple[int, int],
        "timerange": Tuple[float, float],
        "string[]": List[str],
        "floatrange": Tuple[float, float],
        "[[, boolean, float, ]]": List[Union[bool, float]],
        "[uint, uint, uint]": Tuple[int, int, int],
        "[uint, uint, uint, uint]": Tuple[int, int, int, int],
        "[string, uint, string, float]": Tuple[str, int, str, float],
        "[uint, float]": Tuple[int, float],
        "[float, boolean, int, int]": Tuple[float, bool, int, int],
        "[boolean, int]": Tuple[bool, int],
        "[string, int]": Tuple[str, int],
        "[float, int]": Tuple[float, int],
        "[int, int, string]": Tuple[int, int, str],
        "[timerange, boolean]": Tuple[Tuple[float, float], bool],
        "[string, boolean]": Tuple[str, bool],
        "[string, string[]]": Tuple[str, List[str]],
        "[boolean, boolean]": Tuple[bool, bool],
        "[boolean, boolean, boolean]": Tuple[bool, bool, bool],
        "[boolean, boolean, boolean, boolean]": Tuple[bool, bool, bool, bool],
        "[string, float]": Tuple[str, float],
        "[string, [, string, ], [, string, ]]": Tuple[str, List[str], List[str]],
        "[linear, linear, linear, float]": Tuple[float, float, float, float],
        "[int, int, float, float, float]": Tuple[int, int, float, float, float],
        "[string, script]": Tuple[str, str],
        "[script, script]": Tuple[str, str],
        "[string, string, boolean]": Tuple[str, str, bool],
        "[script, string]": Tuple[str, str],
        "[string, string, int, string]": Tuple[str, str, int, str],
        "[string, string, int]": Tuple[str, str, int],
        "[string, string, int, int]": Tuple[str, str, int, int],
        "[uint, boolean]": Tuple[int, bool],
        "[int, int, float]": Tuple[int, int, float],
        "[string, float, float]": Tuple[str, float, float],
        "[int, float, float, float]": Tuple[int, float, float, float],
        "[angle, angle]": Tuple[float, float],
        "[time, time, float]": Tuple[float, float, float],
        "[string, uint]": Tuple[str, int],
        "[boolean, string, int]": Tuple[bool, str, int],
        "[int, [, string, ]]": Tuple[int, List[str]],
        "[string, [, string, ]]": Tuple[str, List[str]],
        "[int, [, int, ]]": Tuple[int, List[int]],
        "[string, int, float]": Tuple[str, int, float],
        "[string, string, script]": Tuple[str, str, str],
        "[string, float, float, float]": Tuple[str, float, float, float],
        "[string, float, float, float, float]": Tuple[str, float, float, float, float],
        "[string, int, int]": Tuple[str, int, int],
        "[string, int, int, int]": Tuple[str, int, int, int],
        "[string, int, int, int, int]": Tuple[str, int, int, int, int],
        "[boolean, string, string, string, string]": Tuple[bool, str, str, str, str],
        "[int, boolean]": Tuple[int, bool],
        "[int, boolean, string, string, string, string]": Tuple[
            int, bool, str, str, str, str
        ],
        "[[, float, float, float, ]]": List[Union[float, List[float]]],
        "int64": int,
        "[linear, linear]": Tuple[float, float],
        "[int, float]": Tuple[int, float],
        "[int, float, [, float, float, ]]": Tuple[int, float, List[float]],
        "[string, uint, uint, uint, uint]": Tuple[str, int, int, int, int],
        "[string, uint, boolean]": Tuple[str, int, bool],
        "[string, string, uint]": Tuple[str, str, int],
        "[boolean, boolean, boolean, boolean, boolean]": Tuple[
            bool, bool, bool, bool, bool
        ],
        "[boolean, boolean, boolean, boolean, boolean, boolean, boolean]": Tuple[
            bool, bool, bool, bool, bool, bool, bool
        ],
        "[int, name]": Tuple[int, str],
        "int[]": List[int],
        "[uint, uint, uint, float, float]": Tuple[int, int, int, float, float],
        "[linear, linear, linear, linear]": Tuple[float, float, float, float],
        "[time, time, time, time]": Tuple[float, float, float, float],
        "[string, int, string]": Tuple[str, int, str],
        "[string, int, float, float, float]": Tuple[str, int, float, float, float],
        "[string, int, boolean]": Tuple[str, int, bool],
        "[int, script]": Tuple[int, str],
        "[uint, linear]": Tuple[int, float],
        "[uint, string]": Tuple[int, str],
        "[linear, linear, linear, linear, linear]": Tuple[
            float, float, float, float, float
        ],
        "[float, float, float, float, float, float, float, float, float, float, float, float, float, float, float, float]": Tuple[
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
            float,
        ],
        "[name, boolean]": Tuple[str, bool],
        "[name, int]": Tuple[str, int],
    }

    return lookup_table.get(argument)


"""The provided type-hints in the html docs don't always reflect the actual
arguments allowed for certain commands and argumnets. This dictionary allows
a user to register an override by both the command and the argument, and providing
the type-hint that should be used instead of the one found in the html docs.
Typehints can be either a single string, or a list of strings."""
cmd_arg_typehint_override = {
    "curve": {
        "point": Union[List[Tuple[float, float, float]], Tuple[float, float, float]],
        "knot": Union[List[int], int],
    },
    "ls": {"type": Union[str, List[str]]},
    "copySkinWeights": {"influenceAssociation": Union[List[str], str]},
    "scriptJob": {"event": Union[Tuple[str, str], Tuple[str, Callable]]},
    "parentConstraint": {
        "skipTranslate": Set[Literal["x", "y", "z"]],
        "skipRotate": Set[Literal["x", "y", "z"]],
    },
    "pointConstraint": {
        "skip": Set[Literal["x", "y", "z"]],
    },
    "orientConstraint": {
        "skip": Set[Literal["x", "y", "z"]],
    },
    "scaleConstraint": {
        "skip": Set[Literal["x", "y", "z"]],
    },
}


def undo_query_edit_to_bools(syntax: str) -> Optional[Tuple[bool, bool, bool]]:
    """
    This function takes all found permutations of the undo/query/edit block
    and converts the result to a set of booleans pertaining to the undo/query/edit
    ability of the function
    """
    # Remove the name of the command from the passed in syntax
    syntax = " ".join(syntax.lower().split(" ")[1:])

    lookup_table = {
        "is not undoable, not queryable, and not editable.": (False, False, False),
        "is undoable, not queryable, and not editable.": (True, False, False),
        "is undoable, queryable, and editable.": (True, True, True),
        "is not undoable, queryable, and editable.": (False, True, True),
        "is undoable, queryable, and not editable.": (True, True, False),
        "is not undoable, queryable, and not editable.": (False, True, False),
        "is undoable, not queryable, and editable.": (True, False, True),
    }

    return lookup_table.get(syntax)


def typing_and_natives_to_str(typehint: Any):
    """This function will take a python typing typehint declaration and convert it
    to a string that can be used in a docstring."""
    if str(typehint).startswith("typing."):
        return str(typehint).replace("typing.", "")
    else:
        return typehint.__name__
