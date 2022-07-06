
from pcr.optic.shot_thread import ShotThread
from pcr.serial_ctrl import LED_PWM, SerialTask, FILTER_POSITIONS, valid_ports


class PCROptic():
    def __init__(self, file_manager, main_ui, task):
        
        # main ui
        self.main_ui = main_ui
        self.task = task

        # Serial Connection
        # self.com_port = valid_ports()[0]
        # self.arduino_serial = SerialTask(serial_port=self.com_port)

        # Get File manager
        self.file_manager = file_manager

        # Shot thread start
        ## self.shot_thread = ShotThread(self.arduino_serial, self.file_manager, self.main_ui)
        self.shot_thread = ShotThread(self.file_manager, self.main_ui, self.task)
        self.shot_thread.start()


    def shot(self, loop, selected_fluors):
        self.shot_thread.shot(loop, selected_fluors)

    def chamber_take_out(self):
        pass

    def go_home(self):
        pass

    def close(self):
        del self.arduino_serial
        del self.file_manager
        self.shot_thread.close()