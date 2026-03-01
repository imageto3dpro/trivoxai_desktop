# Runtime hook to fix pyparsing import for pkg_resources._vendor
# This must run before pkg_resources is imported

import sys

# Pre-import pyparsing and make it available
try:
    import pyparsing
    # Make it available for pkg_resources._vendor.pyparsing
    if 'pkg_resources._vendor.pyparsing' not in sys.modules:
        sys.modules['pkg_resources._vendor.pyparsing'] = pyparsing
except ImportError:
    pass