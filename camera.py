import queue
import threading
import logging
import os
import sys

import cv2 as cv2
from PIL import Image

logger = logging.getLogger('camera')

class CameraWrapper():
  def __init__(self):
    logger.debug('Killing Cheese if open')
    os.system('killall cheese')

    logging.info('Setting webcam values')
    # Must disable auto focus before setting focus
    if os.system('v4l2-ctl -c zoom_absolute=381,focus_automatic_continuous=0') is not 0:
      logger.critical('Setting zoom and disabling auto focus failed')
      return
    if os.system('v4l2-ctl -c focus_absolute=90') is not 0:
      logger.critical('Disabling focus failed')
      return

    # Disable Backlight Comp, auto white balance, auto exposure, dynamic framerate
    if os.system('v4l2-ctl -c backlight_compensation=0,white_balance_automatic=0,auto_exposure=1,exposure_dynamic_framerate=0') is not 0:
      logger.critical('Disabling backlight compensation/auto white balance/auto exposure failed')
      return
    if os.system('v4l2-ctl -c exposure_time_absolute=2047') is not 0:
      logger.critical('Setting exposure time failed')
      return

    # Set gain
    if os.system('v4l2-ctl -c gain=16') is not 0:
      logger.critical('Setting gain failed')
      return

    # Set saturation
    if os.system('v4l2-ctl -c saturation=102') is not 0:
      logger.critical('Setting saturation failed')
      return

    # No LED
    if os.system('python3 ~/cameractrls/cameractrls.py -c logitech_led1_mode=off') is not 0:
      logger.critical('Disabling LED failed')
      return

    self.cap = cv2.VideoCapture(0)
    if not self.cap or not self.cap.isOpened():
        logger.critical('Cannot open camera!')
        sys.exit(1)

    self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 4096)
    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)
    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    self.queue = queue.Queue()
    self.thread = threading.Thread(target=self.run_reader)
    self.thread.daemon = True

    self.run = True
    self.thread.start()

  def run_reader(self):
    while self.run:
      ret, frame = self.cap.read()
      if not ret:
        logger.critical('Failed to capture image!')
        break
      if not self.queue.empty():
        try:
          self.queue.get_nowait() # discard previous (unprocessed) frame
        except queue.Empty:
          pass
      self.queue.put(frame)
  
  def get_image(self):
    segment = self.queue.get()
    logger.debug('Image captured')

    segment = cv2.rotate(segment, cv2.ROTATE_180)

    logger.debug('Image converted and rotated')
    return segment

  def close(self):
    logger.info('Closing...')
    self.run = False
    self.thread.join()
    self.cap.release()
