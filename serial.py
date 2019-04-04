# by pts@fazekas.hu at Thu Apr  4 15:20:36 CEST 2019
from serialutil import *
__version__ = '3.4'
VERSION = __version__
if __import__('os').name == 'nt':  # sys.platform == 'win32'.
  from serialwin32 import Serial
else:
  from serialposix import Serial, PosixPollSerial, VTIMESerial
# Not supported: serialcli (.NET), serialjava, serial_for_url.
