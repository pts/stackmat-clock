#! /usr/bin/python
#
# stackmat_clock.py: Generate serial signal emitted by the StackMat Timer.
# by pts@fazekas.hu at Thu Apr  4 15:21:17 CEST 2019
#

import serial
import sys
import time

# Description of packets:
# https://www.reddit.com/r/Cubers/comments/64czya/wip_stackmat_timer_support_for_twistytimer_app/dg19s4y/
#
# Packet validator code:
# https://github.com/timhabermaas/stackmat.js/blob/c282a247935afb0b2519c644217e278e2c9284c5/src/stackmat.coffee#L72-L85
#
# Audio data decoder:
# https://github.com/timhabermaas/stackmat.js/blob/c282a247935afb0b2519c644217e278e2c9284c5/src/stackmat.coffee#L106-L176
PACKET_LEFT    =  'L00000@\n\r'  # Left and on timer.
PACKET_RIGHT   =  'R00000@\n\r'  # Right hand on timer.
PACKET_BOTH    =  'C00000@\n\r'  # Both hands on timer.
PACKET_READY   =  'A00000@\n\r'  # Ready to start.
PACKET_RESET   =  'I00000@\n\r'
PACKET_STOPPED =  'S00000@\n\r'
PACKET_RUN1    =  ' 12345O\n\r'  # Running, at 1:23.45.


def get_run_packet_at(ts):
  """Returns a packet representing run time ts, which is in seconds."""
  if isinstance(ts, (int, long)):
    ts = int(ts % 600) * 100
  elif isinstance(ts, float):
    ts = int(ts * 100 + .5) % 60000
  else:
    raise TypeError
  assert ts >= 0  # % above ensures it.
  tss = '%d%04d' % (ts / 6000, ts % 6000)
  o0 = ord('0')
  dsum = sum(ord(c) - o0 for c in tss)
  return ' %s%c\n\r' % (tss, 64 + dsum)


assert get_run_packet_at(83.45) == PACKET_RUN1


class NullSerial(object):
  """A partial Serial implementation which ignores data written to it."""

  def __init__(self, *args, **kwargs):
    pass
  def write(self, data):
    pass
  def isOpen(self):
    return True


def main(argv):
  if len(argv) != 2:
    sys.stderr.write(
        'Usage:   %s <serial-device>\n'
        'Example: %s /dev/null\n'
        'Example: %s /dev/ttyS0\n' % (argv[0], argv[0], argv[0]))
    sys.exit(1)
  serial_device = argv[1]

  if serial_device == '/dev/null':
    ser = NullSerial()
  else:
    # Based on https://stackoverflow.com/q/25662489
    #
    # Description of serial port settings:
    # https://www.reddit.com/r/Cubers/comments/64czya/wip_stackmat_timer_support_for_twistytimer_app/dg19s4y/
    ser = serial.Serial()
    # TODO(pts): Pass these as arguments to Serial(...), and omit the call to
    #            ser.open().
    ser.port = serial_device
    ser.baudrate = 1200
    ser.bytesize = serial.EIGHTBITS
    ser.parity = serial.PARITY_NONE
    ser.stopbits = serial.STOPBITS_ONE
    ser.timeout = None
    ser.xonxoff = False
    ser.rtscts = False
    ser.dsrdtr = False
    ser.writeTimeout = 0

    ser.open()

  assert ser.isOpen()
  t0 = time.time()
  i = 0
  while 1:
    ts = time.time() - t0
    packet = get_run_packet_at(ts)
    sys.stdout.write(packet.rstrip('\r\n') + '\n')
    sys.stdout.flush()
    ser.flushOutput()
    ser.write(packet)
    i += 1
    time.sleep(i * .1 - ts)


if __name__ == '__main__':
  sys.exit(main(sys.argv))
