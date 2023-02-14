# generate-maya-cmds-stubs
Nearly everyone's first foray into Python in Maya will involve the maya.cmds commands module.  This is a rather monolithic module and encapsulates every mel command, as well as externally registered commands via plugins.  Autodesk offers generated html docs providing users a place to reference and see how to work with each command in this API.  However, constantly needing to refer to external documentation is quite cumbersome.  Additionally, Python IDEs are unable to scrape these commands as they are programmatically registered at maya startup.

There have been a number of attempts to generate Python IDE friendly stubs of the cmds module.  The longest running form has been the [PyMel](https://pypi.org/project/pymel/) module, optionally available during the Maya installation.  Unfortunately with the switch to Python3, it appears that PyMel is no longer including their cmds module stubs.  Another popular alternative is the [FXTD-OSYSSEY](https://github.com/FXTD-ODYSSEY/vscode-mayapy) vscode-mayapy plugin.  This plugin comes bundled with some generated code-completion docs, similar to the intention of this package.  My reason for trying to tackle this myself is that I noticed that the FXTD completion stubs were generated from Maya 2019.  Those completion stubs also didn't seem to catch the numerous permutations of passed-ins for the default arguments allowed by the cmds module.  Eg: an argument could allow a string, a boolean, or a None be passed in.

So with that, I thought I would give it a go!  I hope this helps speed up my fellow Maya developers, and takes away some guess-work associated with working with the black-box cmds module.

# Examples in Use
## PyCharm
<img src="https://user-images.githubusercontent.com/1255630/218574564-e661a37c-296e-45dc-aa34-86a26f3ff05c.gif"  width="800">

## VSCode
<img src="https://user-images.githubusercontent.com/1255630/218580124-2b40f9eb-b29e-406d-ba41-8355eefee89b.gif"  width="800">

Note: You may want to enable Python > Analysis: Type Checking Mode from its default of *off* to *basic*.  Without this enabled, you will not be warned if you are mis-using an argument by passing in something it isn't expecting.
<img src="https://user-images.githubusercontent.com/1255630/218581126-9c7891bd-917a-4488-83bc-d738c553228b.png"  width="600">

# To-Do
This is the initial release of this module, and there is much house-keeping that should be done.  However, it is generating functional cmds-stubs, and while some of my planned refactoring should speed up performance, I don't anticipate the end-results changing much.

# Dependencies
- Python 3.9
- [beautifulSoup4](https://pypi.org/project/beautifulsoup4/)
- Offline Maya API Docs

## Installing the Dependencies
This utility can be run from a standard copy of Python 3, or via the Mayapy interpreter. Pip installing modules in to python is a very documented and typical thing to do.  Follow the instructions for beautifulSoup4 to add the necessary module to your Python environment. 

Using mayapy.exe to generate the code stubs activates additional behavior as there are a number of plugin-registered commands that are in view of the maya.cmds module, but do not have dedicated .html documentation.  When using mayapy.exe for the generation, these _external_ commands will have stubs generated but will be bare functions without any arguments, flags, or docstrings included. 

## Downloading the necessary Maya Documentation
- https://knowledge.autodesk.com/support/maya/downloads/caas/downloads/content/download-install-maya-product-help.html
- ![download_docs_image](https://user-images.githubusercontent.com/1255630/218574988-3e6f9019-6e2e-435b-9505-987f304dee5f.png)
- If the url changes, simply search for "Maya Documentation" and one of the top results should be the website for downloading offline documentation

# Usage
## Behavior Variables
At the top of tie _main.py_ script is block of logic which reads in a number of environment variables which change certain behaviors of this script.  Each variable and its use are descried below.  These variables are intended as a convenient way to tweak various elements of how this script works, and the results that it provides.

There are a number of ways by which you can set these environment variables.  I'll describe the simplest forms below but configuring a tool environment is beyond on the intent of this writeup.  But perhaps this will help.
- Via the command line, prior to running the script.  
  - Eg: `set VARIABLE=1`
- By adding a section at the top of the _main.py_ file directly, and setting the variables with pure Python
  - `os.environ["VARIABLE"] = 1`

### Variable List
| Variable              | Type    | Default     | Description                                                                                             |
|-----------------------|---------|-------------|---------------------------------------------------------------------------------------------------------|
|CMDS_STUBS_SOURCE_DIR| String  | `./source/` | File path to the directory holding the offline .html code docs.                                         |
|CMDS_STUBS_TARGET_DIR| Boolean | `./target/` | File path to the directory holding the offline .html code docs.                                         |
|CMDS_STUBS_LONG_ARGS| Boolean | True        | Specifies if the code stubs should contain the long-name arguments.  Eg: `maya.cmds.ls(selection=True)` |
|CMDS_STUBS_SHORT_ARGS| Boolean | True        | Specifies if the code stubs should contain the long-name arguments.  Eg: `maya.cmds.ls(sl=True)`        |
|CMDS_STUBS_FORCE_OVERWRITE| Boolean | False       | Overwrite the `./target/cmds/` directory contents, if this folder already exists.                       |

## Runing the Script
- Inside the offline documentation download (see the link above), unzip the contents of the folder _/CommandsPython/_ to a folder titled _/source/_.
  - Eg: `E:\my_git_clone\source`
- Set any environment variables you wish
- Run the script using the command below
  - `C:\python3\python.exe E:\generate-maya-cmds-stubs\main.py`
- The results will be placed into the directory specified by the CMDS_STUBS_TARGET_DIR, or by default, `.\target\cmds`
