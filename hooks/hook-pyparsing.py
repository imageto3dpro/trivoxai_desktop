# PyInstaller runtime hook for pyparsing
# This ensures pyparsing is available for pkg_resources._vendor.pyparsing

import sys
import pyparsing

# Make pyparsing available as pkg_resources._vendor.pyparsing expects
sys.modules['pyparsing'] = pyparsing
