from __future__ import annotations

import os
import shutil
import sys
import traceback
from typing import List, Optional

if os.path.basename(sys.executable) == "mayapy.exe":
    import maya.standalone

    maya.standalone.initialize()
    import maya.cmds as cmds
else:
    cmds = None

import bs4

from type_tables import args_to_typehints, undo_query_edit_to_bools

# Environment variables for modifying the various behaviors of this utility.

# Source and Target variables control where the utility should look for the
# offline html docs (source), and where to write the generated stubs (target)
source_dir = os.getenv("CMDS_STUBS_SOURCE_DIR", "")
target_dir = os.getenv("CMDS_STUBS_TARGET_DIR", "")

# Some users and studios prefer sticking to one type of arguments.
# The variables below allow the generated stubs to conform to either,
# or even both short and long at the same time.
long_args = (os.getenv("CMDS_STUBS_LONG_ARGS", "").lower() in ["true", "1"])
short_args = (os.getenv("CMDS_STUBS_SHORT_ARGS", "").lower() in ["true", "1"])

# When generating the stubs, the results will be written to a folder titled
# cmds, after the main maya python cmds module.  The utility will check if
# this directory exists, and if it is empty, and halt if the directory already has contents.
# This flag will inform the tool to forcibly clear the output directory automatically.
force_overwrite = (os.getenv("CMDS_STUBS_FORCE_OVERWRITE", "").lower() in ["true", "1"])

if not any([short_args, long_args]):
    raise RuntimeError("Must specify at least one type of argument style, aborting.")

# If env variables are not used, use the current active directory.
if not source_dir:
    source_dir = os.path.join(os.getcwd(), "source")

if not target_dir:
    target_dir = os.path.join(os.getcwd(), "target")


def scrape_maya_commands(offline_docs_path: str) -> List[MayaCommand]:
    """

    Args:
        offline_docs_path: File path to a downloaded copy of the Maya python commands doc pages.

    Returns:

    """

    if not os.path.exists(offline_docs_path):
        raise IOError("Offline documents could not be found, aborting.")

    command_docs = [f for f in os.listdir(offline_docs_path) if os.path.splitext(f)[1] == ".html"]
    argument_types = []
    maya_commands_list = []

    for doc in command_docs:
        soup: Optional[bs4.BeautifulSoup] = None

        try:
            with open(os.path.join(offline_docs_path, doc), "r") as f:

                soup = bs4.BeautifulSoup(f.read(), "html.parser")

                if not hasattr(soup, "head") or soup.head is None:
                    # Excludes nested pages such as the Letter_A.html pages,
                    # which are alphabetical table-of-contents lists of commands,
                    # and do not have a header section.
                    continue

                if not soup.head.title or soup.head.title.text in ("blank", "Maya commands"):
                    # "blank" : There is a blank.html page in the api docs
                    # "Maya commands" : found in the index.html page
                    continue

                header_metas = soup.head.find_all("meta")
                if "NOINDEX" in [meta.attrs.get("content") for meta in header_metas]:
                    # This will catch the nested sub-pages which re-list commands in
                    # alphabetical order, by category, etc.
                    # Web spiders would double up command indexes so Autodesk appears to
                    # explicitly exclude them, which is handy for us.
                    continue

                banner = soup.find(id="banner")

                if "(Obsolete)" in banner.h1.text:
                    # Skip any deprecated commands that still have doc pages
                    # as these pages contain no documentation at all.
                    continue

        except Exception as e:
            print(f"\nFailed to parse: {doc} with Exception: {e}")
            traceback.print_exc()
            continue

        if soup:
            print(f"Parsing {doc}...", end="")

            maya_command = MayaCommand()
            maya_commands_list.append(maya_command)

            categories_block = banner.table.contents[1]
            categories_hrefs = categories_block.find_all("a", href=True)
            maya_command.categories = [href.text for href in categories_hrefs]

            maya_command.function = soup.body.find(id="synopsis").find("code").text.split("(")[0]

            # Find the text section pertaining to the allowed command flags,
            # found just after the main function and arguments block.
            # eg: ..... is undoable, queryable, and editable.
            undo_query_edit_section = None
            for idx, section in enumerate(soup.body.contents):
                # The three states (undoable, queryable, editable) are always explicitly mentioned
                # look for all three to ensure that we don't accidentally enter a different sort of text block
                # that happens to use just one fo these three words
                if all(x in section.text for x in ("undoable", "queryable", "editable")):
                    undo_query_edit_section = idx
                    maya_command.undoable, maya_command.queryable, maya_command.editable = undo_query_edit_to_bools(
                        section.text)

            for idx, section in enumerate(soup.body.contents[undo_query_edit_section:]):
                if not isinstance(section, bs4.NavigableString) or section == "\n":
                    continue

                maya_command.description = section.text.strip()
                break

            arguments_table: Optional[bs4.element.Tag] = None

            for table in soup.body.find_all("table"):
                if table.find(string="Long name (short name)"):
                    arguments_table = table
                    break

            if not arguments_table:
                # This doc page contains no keyword arguments to parse
                print(f"done")
                continue

            tr_groups = arguments_table.find_all("tr", recursive=False)

            # Walk through the tables until we hit the argument pairs.
            for idx, table in enumerate(tr_groups):
                if table.attrs and table.attrs.get("bgcolor") == "#EEEEEE":
                    header = table
                    command = tr_groups[idx + 1]

                    argument = Argument()

                    names_section, type_section = header.find_all("code")
                    long_name, short_name = names_section.find_all("b")
                    properties_section = header.find_all("img")
                    argument.properties = Properties([p.get("title") for p in properties_section])

                    argument.long_name = long_name.text
                    argument.short_name = short_name.text

                    argument.type = type_section.text.strip()
                    argument.description = command.text.strip()

                    if argument.type not in argument_types:
                        argument_types.append(argument.type)
                    maya_command.arguments.append(argument)

            print("done")

    return maya_commands_list


def external_commands(parsed_commands: List[MayaCommand]):
    external_maya_commands = []
    parsed_command_names = [c.function for c in parsed_commands]

    for command in [c for c in dir(cmds) if not c.startswith("_")]:
        if command not in parsed_command_names:
            new_command = ExternalCommand()
            external_maya_commands.append(new_command)
            new_command.function = command

    return external_maya_commands


def write_command_stubs(target_file_path: str,
                        command_objects: List[MayaCommand],
                        external_commands: List[ExternalCommand],
                        force: bool = False) -> None:
    """Writes the provided command objects to the target path."""
    if not os.path.exists(target_file_path):
        raise IOError(f"Target file path does not exits, aborting.\nTarget Path: {target_file_path}")

    output_directory = os.path.join(target_file_path, "cmds")
    if os.path.exists(output_directory):
        if not force:
            raise IOError("The target directory already contains a sub-folder named cmds\n"
                          "Rename, move, or delete this folder to continue.\n"
                          "Use the boolean flag Force to overwrite this directory automatically.")
        else:
            shutil.rmtree(output_directory)

    os.mkdir(output_directory)

    base_categories = []

    for command in command_objects:
        if not hasattr(command, "categories"):
            print(f"Command without categories encountered: {command}")

        base_category = command.categories[0]
        if base_category not in base_categories:
            base_categories.append(base_category)

    print("Writing doc stubs...")

    with open(os.path.join(output_directory, "__init__.py"), "w") as f:
        for category in base_categories:
            f.write(f"from maya.cmds.{category} import *\n")
        if external_commands:
            f.write(f"from maya.cmds.External import *\n")

    for category in base_categories:
        with open(os.path.join(output_directory, f"{category}.py"), "w") as f:
            f.write("from typing import Union, Optional, List, Tuple\n\n")

    for command in command_objects:
        base_category = command.categories[0]
        with open(os.path.join(output_directory, f"{base_category}.py"), "a") as f:
            f.write(f"{command.as_stub()}\n")

    if external_commands:
        with open(os.path.join(output_directory, f"External.py"), "w") as f:
            ...

        with open(os.path.join(output_directory, f"External.py"), "a") as f:
            for external_command in external_commands:
                f.write(f"{external_command.as_stub()}")

    print("Done!")


class MayaCommand:
    def __init__(self):
        self.function: str = ""
        self.description: str = ""
        self.categories: List[str] = []
        self.arguments: List[Argument] = []
        self.undoable: bool = False
        self.queryable: bool = False
        self.editable: bool = False

    def as_stub(self):
        fn_string = ""
        fn_string += f"def {self.function}("
        fn_string += "*args,"

        for idx, argument in enumerate(self.arguments):
            try:
                arg_typehint, arg_default = args_to_typehints(argument.type)
            except ValueError:
                raise ValueError(f"Failed at {self.function} with argument format: {argument.type}")

            if argument.properties.create or argument.properties.query:
                if arg_typehint != "bool":
                    arg_typehint = f"Optional[Union[{arg_typehint}, bool]]"

            if long_args:
                fn_string += f" {argument.long_name}: {arg_typehint} = {arg_default},"

            if short_args:
                fn_string += f" {argument.short_name}: {arg_typehint} = {arg_default},"

        if self.editable:
            fn_string += " edit: bool = bool,"
        if self.queryable:
            fn_string += " query: bool = bool,"

        if fn_string.endswith(","):
            fn_string = fn_string[:-1]

        fn_string += "):"
        fn_string += "\n"

        fn_string += "    \"\"\"\n"

        desc = [i.strip() for i in self.description.splitlines() if i.strip()]

        fn_string += "    {d}\n".format(d=" ".join(desc))

        fn_string += "\n"

        fn_string += "    Args:\n"

        for argument in self.arguments:
            argument_name = ""
            if long_args and short_args:
                argument_name = " | ".join([argument.long_name, argument.short_name])
            elif long_args:
                argument_name = argument.long_name
            elif short_args:
                argument_name = argument.short_name

            description = argument.description.splitlines()
            description = " ".join(description)
            fn_string += f"        {argument_name}: ({str(argument.properties)}) - {description}\n"

        fn_string += "    \"\"\"\n"
        fn_string += "    pass\n\n"

        return fn_string


class ExternalCommand:
    def __init__(self):
        self.function: str = ""

    def as_stub(self):
        fn_string = ""
        fn_string += f"def {self.function}("
        fn_string += "*args, **kwargs"
        fn_string += "): pass\n"

        return fn_string


class Argument:
    def __init__(self):
        self.long_name: str = ""
        self.short_name: str = ""
        self.type: str = ""
        self.properties: Optional[Properties] = None
        self.description: str = ""


class Properties:
    def __init__(self, init_values: List[str]):
        self.edit = False
        self.create = False
        self.query = False
        self.multiuse = False

        for value in init_values:
            if value not in self._arguments:
                raise ValueError("This command contains an unrecognized property\n"
                                 f"Allowed properties    : {', '.join(self._arguments)}\n"
                                 f"unrecognized property : {value}")

        for field in self._arguments:
            if str(field) in init_values:
                setattr(self, field, True)

    @property
    def _arguments(self) -> List[str]:
        """Returns a string list of the boolean flags set during initialization,
        eg: create, edit, query, multiuse, etc..."""
        return [i for i in dir(self) if not i.startswith("_")]

    def __repr__(self):
        return ", ".join([i for i in self._arguments if getattr(self, i) is True])


if __name__ == "__main__":
    for asset_path in [target_dir, source_dir]:
        if not os.path.exists(asset_path):
            os.mkdir(asset_path)

    maya_commands = scrape_maya_commands(offline_docs_path=source_dir)

    if cmds is not None:
        external_commands = external_commands(maya_commands)
    else:
        external_commands = []

    write_command_stubs(target_file_path=target_dir,
                        command_objects=maya_commands,
                        external_commands=external_commands,
                        force=force_overwrite)
