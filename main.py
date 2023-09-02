from __future__ import annotations

import asyncio
import os
import shutil
import sys
import traceback
from typing import List, Optional, Any
import time

import bs4

from type_tables import args_to_typehints, undo_query_edit_to_bools

# Source and Target variables control where the utility should look for the
# offline html docs (source), and where to write the generated stubs (target)
source_folder_path = os.getenv("CMDS_STUBS_SOURCE_DIR", os.path.join(os.getcwd(), "source"))
target_folder_path = os.getenv("CMDS_STUBS_TARGET_DIR", os.path.join(os.getcwd(), "target"))

# Some users and studios prefer sticking to one type of arguments.
# The variables below allow the generated stubs to conform to either,
# or even both short and long at the same time.
long_args = os.getenv("CMDS_STUBS_LONG_ARGS", "true").lower() in ["true", "1"]
short_args = os.getenv("CMDS_STUBS_SHORT_ARGS", "true").lower() in ["true", "1"]

# When generating the stubs, the results will be written to a folder titled
# cmds, after the main maya python cmds module.  The utility will check if
# this directory exists, and if it is empty, and halt if the directory already has contents.
# This flag will inform the tool to forcibly clear the output directory automatically.
force_overwrite = os.getenv("CMDS_STUBS_FORCE_OVERWRITE", "").lower() in ["true", "1"]


async def parse_command(file_path: str) -> Optional[MayaCommand]:
    soup: Optional[bs4.BeautifulSoup] = None

    try:
        with open(os.path.join(file_path), "r") as f:
            soup = bs4.BeautifulSoup(f.read(), "html.parser")
            if not hasattr(soup, "head") or soup.head is None:
                # Excludes nested pages such as the Letter_A.html pages,
                # which are alphabetical table-of-contents lists of commands,
                # and do not have a header section.
                return None

            if not soup.head.title or soup.head.title.text in (
                "blank",
                "Maya commands",
            ):
                # "blank" : There is a blank.html page in the api docs
                # "Maya commands" : found in the index.html page
                return None

            header_metas = soup.head.find_all("meta")
            if "NOINDEX" in [meta.attrs.get("content") for meta in header_metas]:
                # This will catch the nested sub-pages which re-list commands in
                # alphabetical order, by category, etc.
                # Web spiders would double up command indexes so Autodesk appears to
                # explicitly exclude them, which is handy for us.
                return None

            banner: Any = soup.find(id="banner")

            if "(Obsolete)" in banner.h1.text:
                # Skip any deprecated commands that still have doc pages
                # as these pages contain no documentation at all.
                return None

    except Exception as e:
        print(f"\nFailed to parse: {os.path.basename(file_path)} with Exception: {e}")
        traceback.print_exc()
        return None

    if not soup or not banner:
        return None

    maya_command = MayaCommand()
    argument_types = []

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
        # that happens to use just one of these three words
        if all(x in section.text for x in ("undoable", "queryable", "editable")):
            undo_query_edit_section = idx
            undoable_queryable_editable = undo_query_edit_to_bools(section.text)
            if undoable_queryable_editable is None:
                raise ValueError(f"Failed to parse undoable, queryable, editable block: {section.text}")
            (
                maya_command.undoable,
                maya_command.queryable,
                maya_command.editable,
            ) = undoable_queryable_editable
    
    if not undo_query_edit_section:
        raise ValueError(f"Failed to find undoable, queryable, editable block: {maya_command.function}")

    for idx, section in enumerate(soup.body.contents[undo_query_edit_section + 1 :]):
        if "Return value" in section.text:
            maya_command.description += section.text.split("Return value")[0]
            break

        maya_command.description += section.text

    arguments_table: Optional[bs4.element.Tag] = None

    for table in soup.body.find_all("table"):
        if table.find(string="Long name (short name)"):
            arguments_table = table
            break

    if not arguments_table:
        # This doc page contains no keyword arguments to parse
        return maya_command

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

    return maya_command


def write_command_stubs(cmds_directory: str, command_objects: List[MayaCommand]) -> None:
    """Writes the provided command objects to the target path."""
    base_categories = []

    for command in command_objects:
        if not hasattr(command, "categories"):
            print(f"Command without categories encountered: {command}")

        base_category = command.categories[0]
        if base_category not in base_categories:
            base_categories.append(base_category)

    print("Writing doc stubs...")

    with open(os.path.join(cmds_directory, "__init__.py"), "w") as f:
        for category in base_categories:
            f.write(f"from {category} import *\n")

    for category in base_categories:
        with open(os.path.join(cmds_directory, f"{category}.py"), "w") as f:
            f.write("from typing import Union, Optional, List, Tuple, Any\n\n")

    for command in command_objects:
        base_category = command.categories[0]
        with open(os.path.join(cmds_directory, f"{base_category}.py"), "a") as f:
            f.write(f"{command.as_stub()}\n")

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
            arg_typehint = args_to_typehints(argument.type)
            if arg_typehint is None:
                raise ValueError(f"Failed at {self.function} with argument format: {argument.type}")

            if argument and argument.properties:
                if argument.properties.create or argument.properties.query:
                    if arg_typehint != "bool":
                        arg_typehint = f"Optional[Union[{arg_typehint}, bool]]"

            # Accounts for arguments that use the same argument name for both short or long styles
            if long_args and short_args and argument.long_name == argument.short_name:
                fn_string += f" {argument.long_name}: {arg_typehint} = ...,"
            else:
                if long_args and argument.long_name:
                    fn_string += f" {argument.long_name}: {arg_typehint} = ...,"

                if short_args and argument.short_name:
                    fn_string += f" {argument.short_name}: {arg_typehint} = ...,"

        if self.editable:
            fn_string += " edit: bool = ...,"
        if self.queryable:
            fn_string += " query: bool = ...,"

        if fn_string.endswith(","):
            fn_string = fn_string[:-1]

        fn_string += ") -> Any:"
        fn_string += "\n"

        fn_string += '    r"""\n'

        desc = self.description.strip().splitlines(keepends=True)

        fn_string += "    {d}\n".format(d="    ".join(desc))

        fn_string += "\n"

        fn_string += "    Args:\n"

        for argument in self.arguments:
            argument_name = ""
            if long_args and short_args:
                argument_name = argument.long_name
                if argument.short_name:
                    argument_name += f" | {argument.short_name}"
            elif long_args:
                argument_name = argument.long_name
            elif short_args:
                argument_name = argument.short_name

            description = argument.description.splitlines()
            description = " ".join(description)
            fn_string += f"        {argument_name}: ({str(argument.properties)}) - {description}\n"

        fn_string += '    """\n'
        fn_string += "    ...\n\n"

        return fn_string


class ExternalCommand:
    def __init__(self):
        self.function: str = ""

    def as_stub(self):
        fn_string = ""
        fn_string += f"def {self.function}("
        fn_string += "*args, **kwargs"
        fn_string += ") -> Any: ...\n"

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
                raise ValueError(
                    "This command contains an unrecognized property\n"
                    f"Allowed properties    : {', '.join(self._arguments)}\n"
                    f"unrecognized property : {value}"
                )

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


async def do_it():
    command_docs = [f for f in os.listdir(source_folder_path) if os.path.splitext(f)[1] == ".html"]
    print("Parsing docs...")

    tasks = [asyncio.create_task(parse_command(os.path.join(source_folder_path, cmd))) for cmd in command_docs]
    maya_commands = await asyncio.gather(*tasks)
    maya_commands = [i for i in maya_commands if i is not None]

    print("Writing stubs...")

    write_command_stubs(
        cmds_directory=cmds_directory,
        command_objects=maya_commands,
    )

if __name__ == "__main__":
    # Create the ./source/ and ./target/ folders if they don't already exist
    for asset_path in [target_folder_path, source_folder_path]:
        if not os.path.exists(asset_path):
            os.makedirs(asset_path)

    if not any([short_args, long_args]):
        raise RuntimeError("Must specify at least one type of argument style, short or long.  Aborting.")

    if not os.path.exists(target_folder_path):
        raise IOError(f"Target file path does not exits, aborting.\nTarget Path: {target_folder_path}")

    # The cmds module must be inside a folder named /maya/, to match Maya's own
    # module structure for the cmds module.  Eg: import maya.cmds is ./maya/cmds/
    maya_directory = os.path.join(target_folder_path, "maya")
    cmds_directory = os.path.join(target_folder_path, "maya", "cmds")

    if os.path.exists(cmds_directory) and os.listdir(cmds_directory):
        if not force_overwrite:
            raise IOError(
                "The target directory already exists, Rename, move, or delete this folder to continue.\n"
                "Optional: Use the boolean flag Force to reset the contents of this directory automatically."
            )
        else:
            shutil.rmtree(cmds_directory)

    if not os.path.exists(cmds_directory):
        os.makedirs(cmds_directory)

    if not os.path.isfile(os.path.join(maya_directory, "__init__.py")):
        with open(os.path.join(maya_directory, "__init__.py"), "w") as f:
            ...
    start = time.perf_counter()

    asyncio.run(do_it())

    end = time.perf_counter()
    print(f"Finished in {end - start:0.4f} seconds")
