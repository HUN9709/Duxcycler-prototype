import sys
import time
import threading

from pcr.serial_ctrl import FILTER_POSITIONS
from pcr.optic.camera import IMX298BufferCleaner, tubes_intensity, FLUORESCENCES
        

class ShotThread(threading.Thread):
    """
        PCR Task와 비동기적으로 Shot을 하기 위한 Thread class
    """
    ## def __init__(self, serial, file_manager, main_ui):
    def __init__(self, file_manager, main_ui, task):
        super().__init__()
        self.daemon = True

        self.task = task
        print(f"task : {task}")

        # Initialize
        self.main_ui = main_ui
        ## self.serial = serial
        self.file_manager = file_manager
        self.cam_worker = IMX298BufferCleaner()
        self.cam_worker.start()

        # Thread event
        self.shot_event = threading.Event()

        # Shotting flag
        self.shotting = False
        self.shot_end = False

        # Shotting params
        self.cur_loop = None
        self.target_flours = None

    def run(self):
        while True:
            self.shot_event.wait()
            self._shot()
            self.shot_event.clear()

    def _shot(self):
        """
            TODO : shot logic
        """
        imgs=[]
        # Shot each filters
        for flour in self.target_flours:
            pos = FILTER_POSITIONS[flour]

            # TODO : GOTO target position:
            ## self.serial.go_to(pos)
            
            # TODO : LED On
            ## self.serial.set_LEDOn()
            
            time.sleep(self.cam_worker.exp_time * 3)

            # Shot
            img = self.cam_worker.shot()
            imgs.append(img)

            # TODO : LED Off
            ## self.serial.set_LEDOff()

        # TODO : GO HOME
        # GO HOME 까지 순차적으로
        # threading.Thread(target=self.serial.go_to, args=(0,)).start()

        # Save img & analysing
        for flour, img in zip(self.target_flours, imgs):
            # Save img
            try:
                if self.cur_loop == None:
                    self.file_manager.save_test_img(img, flour)
                else:
                    self.file_manager.save_img(img, flour, self.cur_loop)

                    values = tubes_intensity(flour, img)
                    self.file_manager.xlsx.record_values(flour, values, self.cur_loop)
                    # self.main_ui.frame_graph.update_values(flour, values)
                    # self.main_ui.frame_img.display_values(flour, values)
                    self.task.set_update_vals(flour, values)
                    
            
            except Exception as e:
                print(f"{e}")
            
        self.shotting = False
        self.shot_end = True
        print("end shot!!!")

    def shot(self, loop, selected_fluors):
        if not self.shotting:
            self.cur_loop = loop
            self.target_flours = [FLUORESCENCES[ind] for ind, is_sel in enumerate(selected_fluors) if is_sel]
            self.shotting = True
            self.shot_event.set()

    def close(self):
        self.cam_worker.close()
        sys.exit(0)