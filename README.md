# generate-maya-cmds-stubs
Nearly everyone's first foray into Python in Maya will involve the maya.cmds commands module.  This is a rather monolithic module and encapsulates every mel command, as well as externally registered commands via plugins.  Autodesk offers generated html docs providing users a place to reference and see how to work with each command in this API.  However, constantly needing to refer to external documentation is quite cumbersome.  Additionally, Python IDEs are unable to scrape these commands as they are programmatically registered at maya startup.

There have been a number of attempts to generate Python IDE friendly stubs of the cmds module.  The longest running form has been the [PyMel](https://pypi.org/project/pymel/) module, optionally available during the Maya installation.  Unfortunately with the switch to Python3, it appears that PyMel is no longer including their cmds module stubs.  Another popular alternative is the [FXTD-OSYSSEY](https://github.com/FXTD-ODYSSEY/vscode-mayapy) vscode-mayapy plugin.  This plugin comes bundled with some generated code-completion docs, similar to the intention of this package.  My reason for trying to tackle this myself is that I noticed that the FXTD completion stubs were generated from Maya 2019.  Those completion stubs also didn't seem to catch the numerous permutations of passed-ins for the default arguments allowed by the cmds module.  Eg: an argument could allow a string, a boolean, or a None be passed in.

So with that, I thought I would give it a go!  I hope this helps speed up my fellow Maya developers, and takes away some guess-work associated with working with the black-box cmds module.

# Example in Use
## PyCharm
https://user-images.githubusercontent.com/1255630/218573922-b6d1a3ed-e529-4b09-9465-558d66137c17.mp4

## VSCode


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
- ![maya_offline_docs_download](https://user-images.githubusercontent.com/1255630/218573895-1bb07f5c-3aee-44ac-86e2-371b8c5051d6.png)
- If the url changes, simply search for "Maya Documentation" and one of the top results should be the website for downloading offline documentation

# Usage
...
