from __future__ import annotations

import bs4
import os
import scandir
import shutil
import traceback
from typing import List, Optional

from type_tables import args_to_typehints, undo_query_edit_to_bools

OUTPUT_DIRECTORY = r"E:\maya\stubs"
DOCS_SOURCE_DIRECTORY = r"E:\maya\CommandsPython"


def scrape_maya_commands(offline_docs_path: str) -> List[MayaCommand]:
    """

    Args:
        offline_docs_path: File path to a downloaded copy of the Maya python commands doc pages.

    Returns:

    """

    if not os.path.exists(offline_docs_path):
        raise IOError("Offline documents could not be found, aborting.")

    command_docs = [f for f in scandir.listdir(offline_docs_path) if os.path.splitext(f)[1] == ".html"]
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

            undo_query_edit_section = None
            for idx, section in enumerate(soup.body.contents):
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
                    argument.long_name = long_name.text
                    argument.short_name = short_name.text

                    argument.type = type_section.text.strip()
                    argument.description = command.text.strip()

                    if argument.type not in argument_types:
                        argument_types.append(argument.type)
                    maya_command.arguments.append(argument)

            print("done")


    return maya_commands_list


def write_command_stubs(target_file_path: str, command_objects: List[MayaCommand], force: bool = False) -> None:
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

    for category in base_categories:
        with open(os.path.join(output_directory, f"{category}.py"), "w") as f:
            f.write("from typing import Union, Optional, List, Tuple\n\n")

    for command in command_objects:
        base_category = command.categories[0]
        with open(os.path.join(output_directory, f"{base_category}.py"), "a") as f:
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
            try:
                arg_typehint, arg_default = args_to_typehints(argument.type)
            except ValueError:
                raise ValueError(f"Failed at {self.function} with argument format: {argument.type}")
            fn_string += f" {argument.long_name}: {arg_typehint} = {arg_default},"

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
            description = argument.description.splitlines()
            description = " ".join(description)
            fn_string += f"        {argument.long_name}: {description}\n"

        fn_string += "    \"\"\"\n"
        fn_string += "    pass\n"

        return fn_string


class Argument:
    def __init__(self):
        self.long_name: str = ""
        self.short_name: str = ""
        self.type: str = ""
        self.properties: list = []
        self.description: str = ""


if __name__ == "__main__":
    maya_commands = scrape_maya_commands(offline_docs_path=DOCS_SOURCE_DIRECTORY)
    write_command_stubs(target_file_path=OUTPUT_DIRECTORY,
                        command_objects=maya_commands, force=True)
