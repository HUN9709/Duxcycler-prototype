import sys

from pcr.constants.config import CAM_NAME, CAM_SETTINGS, CHANNELS, FLUORESCENCES
from pcr.logger import log_cam_message, log_cam_init, log_cam_brightness

import subprocess as sub
import threading

import numpy as np
import cv2

import time


# Arducam IMX298 setting values definitions.
FRAME_WIDTH             = CAM_SETTINGS["width"]
FRAME_HEIGHT            = CAM_SETTINGS["height"]
EXPOSURE                = CAM_SETTINGS["exposure"]
FOCUS                   = CAM_SETTINGS["focus"]
GAIN                    = CAM_SETTINGS["gain"]
GAMMA                   = CAM_SETTINGS["gamma"]
WHITEBALACE             = CAM_SETTINGS["whitebalance"]
LOW_LIGHT_COMPENSATION  = CAM_SETTINGS["low_light_compensation"]

# .exe file to set IMX298 using DirectShow.
SETTING_EXE_FNAME       = CAM_SETTINGS["exe_filename"]

# Image analysis constants
CENTERS                 = CAM_SETTINGS["centers"]
RAD                     = CAM_SETTINGS["rad"]


# Image analysis functions
def emulate_shot(loop):
    return cv2.imread(f"./res/emulation_img/{loop}.png")

@log_cam_brightness
def tubes_intensity(fluor, img):
    values = [i for i in range(25)]
    channel = CHANNELS[fluor]
    _img = img[:, :, channel]

    for tube_ind, center in enumerate(CENTERS):
        x, y = center[0], center[1]
        mask = np.zeros(_img.shape)
        cv2.circle(mask,(int(x), int(y)), RAD, 255, -1)
        values[tube_ind] = np.mean(_img[mask == 255])

    return values

def emulate_tubes_intensity(fluor, loop):
    img = emulate_shot(loop)
    return tubes_intensity(fluor, img)


#########################################
#   TODO: List up avaliable USB cameras.
#########################################


# IMX298 camera worker class
class IMX298BufferCleaner(threading.Thread):
    """
        Arducam IMX298 카메라 모듈을 사용하여 가장 최신 프레임을 가져오는 Thread
            - exposure time( = 2^exposure[현재 0.25sec]) 마다 주기적으로 업데이트 되는 것 확인
            - 어떠한 경우에도 최신 frame으로 업데이트 해야 하기 때문에 독립적인 Thread로 구현
            - cv2 에서 IMX298 의 focus, expousre, low-light compensation, white-balance 제어 설정이
            구현되어 있지 않으므로, SETTING_EXE_FNAME 사용하여 이를 설정...
    """
    @log_cam_message('INFO', f"Camera thread Initialize")
    def __init__(self, cam_no=0):
        super().__init__()
        self.daemon = True
        self.cap = cv2.VideoCapture(cam_no, cv2.CAP_DSHOW)
        self._cam_init()

        self.exp_time = np.power(2.0, EXPOSURE)

        self.stop_flag = False
        self.last_frame = None

    @log_cam_message('INFO', f"{SETTING_EXE_FNAME} 실행")
    def set_imx298(self, focus, exposure, lowlight):
        """Setting focus, exposure, low-light compensation, white-balance using excute file."""
        return sub.call([f"./{SETTING_EXE_FNAME}", f'{focus}', f'{exposure}', f'{1 if lowlight else 0 }', f'{WHITEBALACE}'])

    @log_cam_message('INFO', f"Camera initialize with values {CAM_SETTINGS}")
    @log_cam_init
    def _cam_init(self):
        """IMX298 settings"""
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)

        self.set_imx298(FOCUS, EXPOSURE, LOW_LIGHT_COMPENSATION)

        self.cap.set(cv2.CAP_PROP_GAIN, GAIN)
        self.cap.set(cv2.CAP_PROP_GAMMA, GAMMA)

    @log_cam_message('DEBUG', 'Start camera read')
    def run(self):
        while not self.stop_flag:
            ret, self.last_frame = self.cap.read()

    @log_cam_message('DEBUG', 'return last_frame')
    def shot(self):
        return self.last_frame

    @log_cam_message('DEBUG', 'Close camera thread')
    def close(self):
        self.stop_flag = True
        self.cap.release()
        sys.exit(0)