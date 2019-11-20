#! /usr/bin/python
#
# stackmat_clock.py: Generate serial signal emitted by the StackMat Timer.
# by pts@fazekas.hu at Thu Apr  4 15:21:17 CEST 2019
#

import os
import select
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
PACKET_RUN1    =  ' 123451P\n\r'  # Running, at 1:23.45.


def get_run_packet3(a, bb, ccc):
  assert 0 <= a <= 9
  assert 0 <= bb <= 99
  assert 0 <= ccc <= 999
  tss = '%d%02d%03d' % (a, bb, ccc)
  o0 = ord('0')
  dsum = sum(ord(c) - o0 for c in tss)
  return ' %s%c\n\r' % (tss, 64 + dsum)


def get_run_packet2(a, bb, cc):
  assert 0 <= a <= 9
  assert 0 <= bb <= 99
  assert 0 <= cc <= 99
  tss = '%d%02d%02d' % (a, bb, cc)
  o0 = ord('0')
  dsum = sum(ord(c) - o0 for c in tss)
  return ' %s%c\n\r' % (tss, 64 + dsum)


def get_run_packet_at(ts):
  """Returns a packet representing run time ts, which is in seconds."""
  if isinstance(ts, (int, long)):
    sec. msec = ts, 0
  elif isinstance(ts, float):
    msec = int(ts * 1000 + .5)
    sec, msec = divmod(msec, 1000)
  else:
    raise TypeError
  assert sec >= 0
  assert 0 <= msec <= 999
  if sec < 10 * 60:
    # Last digit (.??D) D == 0 vs 1 because Python is slow.
    return get_run_packet2(sec // 60, sec % 60, msec // 10)
  elif sec < 10 * 3600:
    return get_run_packet2(sec // 3600, sec // 60 % 60, sec % 60)
  elif sec < 1000 * 3600:
    return get_run_packet2(sec // 360000, sec // 3600 % 100, sec // 60 % 60)
  else:
    return get_run_packet3(9, 99, 9999)


#assert get_run_packet_at(83.451) == PACKET_RUN1


class NullSerial(object):
  """A partial Serial implementation which ignores data written to it."""

  def __init__(self, *args, **kwargs):
    pass
  def write(self, data):
    pass
  def isOpen(self):
    return True

def parse_time(time_str):
  # TODO(pts): Add .msec
  # !! positive only
  items = map(int, time_str.split(':'))
  if len(items) == 3:
    return 3600 * items[0] + 60 * items[1] + items[2]
  elif len(items) == 2:
    return 60 * items[0] + items[1]
  else:
    return items[0]


def main(argv):
  if len(argv) not in (2, 3):
    sys.stderr.write(
        'Usage:   %s <serial-device> [<start-time>]\n'
        'Example: %s /dev/null\n'
        'Example: %s /dev/ttyS0\n' % (argv[0], argv[0], argv[0]))
    sys.exit(1)
  serial_device = argv[1]
  if len(argv) > 2:
    ts = parse_time(argv[2])

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
  t0 = time.time() - ts
  i = 0
  is_running = True
  ts = 0
  try:
    while 1:
      if is_running:
        ts = time.time() - t0
      packet = get_run_packet_at(ts)
      #packet = get_run_packet3(3, 44, 567)
      #packet = get_run_packet2(3, 44, 56)
      #packet = get_run_packet3(9, 99, 999)
      # Leading spaces so that ^C doesn't overrite the hours.
      sys.stdout.write('   %d:%02d:%02d %s  ' % (ts // 3600, ts // 60 % 60, ts // 1 % 60, packet.rstrip('\r\n')) + '\r')
      sys.stdout.flush()
      ser.write(packet)
      ser.flushOutput()
      i += 1
      #time.sleep(.1 - (ts % .1))
      #time.sleep(max(0.06,  i * .1 - ts))
      rfds, _, _ = select.select((0,), (), (), .1 - (ts % .1))
      if rfds:  # <Enter>
        os.read(0, 8192)
        if is_running:
          is_running = False
        else:
          t0 = time.time() - ts
          is_running = True
  finally:
    sys.stdout.write('\n')
    sys.stdout.flush()

if __name__ == '__main__':
  sys.exit(main(sys.argv))
