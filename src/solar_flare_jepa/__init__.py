"""Solar telemetry research and bounded baseline experiment foundation."""
import sys as _sys

from ._executed_source import install as _install_source_capture

_install_source_capture(__name__, __file__, _sys._getframe().f_code)

del _sys, _install_source_capture
