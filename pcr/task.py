import os
import time
import datetime
import threading
import logging


import cv2

import PyQt5
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox


from pcr.constants.constant import Command, State, StateOper
from pcr import protocol as Protocol

import pcr.hid.tx_action as TxAction
import pcr.hid.rx_action as RxAction

from pcr.optic.optic import PCROptic
from pcr.file_manager import PCRFileManager
from pcr.optic.camera import FLUORESCENCES

from pcr import logger


class PCRTask:
    """PCR task class"""
    
    __instance = None

    @classmethod
    def _getInstance(cls):
        return cls.__instance

    @classmethod
    def instance(cls, *args, **kargs):
        cls.__instance = cls(*args, **kargs)
        cls.instance = cls._getInstance
        return cls.__instance

    @logger.log_pcr_message("INFO", f"PCR Task Initialized")
    def __init__(self, mainIU):
        super().__init__()

        # mainUI instance
        self.mainUI = mainIU

        self.mainUI.set_progress_value(10, "Setting flags...")
        # State & command paramters
        self.state = State.READY
        self.command = Command.NOP
        self.shot_finished = False
        
        self.rx_buffer = None
        self.cur_loop = 0
        self.pre_label = 0
        self.cur_label = 0
        self.chamber_temp = 0
        self.heater_temp = 0

        # PCR flags
        self.running = False
        self.finishPCR = False

        # PCR parameters 
        self.preheat = 104
        self.action_num = 0
        self.taskEnded = False

        # Temporary variable
        self.expt_name = None
        self.update_vals = []

        self.mainUI.set_progress_value(10, "Load Protocols...")
        # Load default protocol
        self.protocol = Protocol.default_protocol
        self.get_device_protocol()

        self.mainUI.set_progress_value(80, "Setting FileManager...")
        # FileManager
        self.file_manager = PCRFileManager()


        # PCR Optic(arduino_serial, camera)
        self.optic = PCROptic(self.file_manager, self.mainUI, self)

        self.mainUI.set_progress_value(100, "Setting FileManager...")
        self.mainUI.close_loading_bar()
        self.mainUI.show()
        
    
    '''
        PCR START & STOP event functions
    '''
    @logger.log_pcr_message("INFO", f"PCR Start")
    def pcr_start(self):
        """MainUI ?????? Start ?????? ????????? ???????????? ??????"""

        # Set Flags
        self.running = True
        self.finishPCR = False
        self.command = Command.TASK_WRITE
        
        # Get expt name
        self.expt_name = PCRFileManager.gen_expt_name()

        # Get selected fluor & create path and *.xlsx
        sel_fluors = [FLUORESCENCES[ind] for ind, is_sel in enumerate(self.mainUI.frame_ctrl.selected_fluor) if is_sel]
        self.file_manager.start_task(self.expt_name, sel_fluors, self.protocol.shot_labels)

        # mainUI's mainUI
        self.mainUI.running_event()

    @logger.log_pcr_message("INFO", f"PCR Stop")
    def pcr_stop(self):
        """MainUI ?????? Stop ?????? ????????? ???????????? ??????
            
            ????????? ??????
        """
        if self.state == State.RUN:
            self.command = Command.STOP

    '''
        UI ????????????
    '''
    def set_preheat(self, preheat):
        self.preheat = preheat


    '''
        Protocol ?????? ?????????
    '''
    def load_protocol(self, protocol_name):
        try:
            self.protocol = Protocol.load_protocol(protocol_name)
            Protocol.saveRecentProtocolName(protocol_name)
            self.cycle_num =  next((item for item in self.protocol if item['Label'] == 'GOTO'))['Time']

            self.mainUI.frame_ctrl.label_protocol.setText(protocol_name)
        except ValueError as err:
            QMessageBox.about(self.mainUI, "Invalid_protocol", "???????????? ?????? ???????????? ?????????.")
    
    def get_device_protocol(self):
        '''
        TODO : initialize ???????????? ??????
            220322 : self.deviceCheck flag ????????????,
                        get_device_protocol call??? timer -> PCR_Task.__init__() ?????? ??????
        '''
        protocol_name = Protocol.loadRecentProtocolName()
        if protocol_name:
            try:
                self.load_protocol(protocol_name)
            except FileNotFoundError as err:
                QMessageBox.about(self.mainUI, "protocol_not_found", "?????? ???????????? ?????? ???????????? ??????!")
        else:
            pass
    
    '''
        PCR Task ?????? ?????????
    '''
    def check_action(self):
        """
            self.check_status() ??????
            TASK_WRITE ??? ???????????? ????????? ?????? ???
            rx_buffer ??? check ?????? ??????
        """
        action = self.protocol[self.action_num].copy()
        action['Label'] = 250 if action['Label'] == "GOTO" else action['Label']
        
        # python dictionary subset compare
        return action.items() <= RxAction.rx_buffer.items()

    @logger.log_pcr_command
    def check_status(self):
        """????????? rx_buffer??? Status??? ???????????? flag?????? ????????? ?????? ??????

            State(Constant.State) ???????????? ??????????????????,
            logic error ??? code ???????????? ?????? "?????? ?????????" ???????????? ???????????????.
        """

        if self.command == Command.NOP:
            # TODO : UI Update
            state_oper = RxAction.rx_buffer["Current_Operation"]
            
            if state_oper != StateOper.INIT:
                if self.running and not self.finishPCR:
                    # TODO : reset parameters 
                    if state_oper == StateOper.COMPLETE:
                        # TODO : PCR Complate logic 
                        QMessageBox.about(self.mainUI, "PCR END", "PCR COMPLITE!")

                        self.mainUI.frame_ctrl.btn_start.toggle()

                    elif state_oper == StateOper.INCOMPLETE:
                        # TODO : PCR Incomplate logic
                        QMessageBox.about(self.mainUI, "PCR END", "PCR INCOMPLATE")

                    self.mainUI.not_running_event()

                    self.running = False
                    self.finishPCR = True
                    self.action_num = 0

                    # self.expt_name = None
                    # self.file_manager.end_task()

            else:
                pass

            if self.optic.shot_thread.shot_end:
                """
                    optic.shot_thread ?????? shot ??? ???????????? Command.RESUME ??????
                """
                self.command = Command.RESUME

        elif self.command == Command.RESUME:
            """
                ?????? command ??? RESUME ?????? 
            """
            self.command = Command.NOP
            self.optic.shot_thread.shot_end = False
            self.shot_finished = True
                

        elif self.command == Command.TASK_WRITE:
            '''
                ????????? rx_buffer ??? ????????? ???,  
                ?????? ?????? action ??? ????????? action_num ??? 1???????????????, 
                ?????? ?????? action ??? ????????? command??? TASK_END ??? ????????????. 
            '''
            if self.check_action() :
                if  self.action_num != (len(self.protocol) - 1):
                    self.action_num += 1
                else:
                    self.command = Command.TASK_END

        elif self.command == Command.TASK_END:
            self.command = Command.GO
            
        elif self.command == Command.GO:
            if self.state == State.RUN:
                """
                Running button ????????? start button ??? disable ????????? ?????????,
                TASKWRITE -> TASKEND -> GO ???????????? ?????? ??? State??? Run ???????????? ????????? ??????.
                """
                self.mainUI.frame_ctrl.btn_start.setDisabled(False)
                self.command = Command.NOP
        
        elif self.command == Command.STOP:
            if self.state == State.READY or self.state == State.STOP:
                self.command = Command.NOP
    
    def calc_temp(self):
        """
            Chamber??? LID heater ?????? ?????? ??? MainUI??? Display ????????? ??????
        """
        self.chamber_temp = RxAction.rx_buffer['Chamber_TempH'] + RxAction.rx_buffer['Chamber_TempL'] * 0.1
        self.heater_temp = RxAction.rx_buffer['Cover_TempH'] + RxAction.rx_buffer['Cover_TempL'] * 0.1

        self.mainUI.frame_ctrl.temp(self.chamber_temp)

    def line_task(self):
        if self.state == State.RUN:
            loop, _, left_time = RxAction.rx_buffer["Current_Loop"], RxAction.rx_buffer["Current_Action"], RxAction.rx_buffer["Sec_TimeLeft"]
            self.mainUI.frame_ctrl.loop((0 if loop == 255 else self.cycle_num-loop))

            if len(self.update_vals) > 0:
                update_val = self.update_vals.pop(0)
                self.mainUI.frame_graph.update_values(update_val[0], update_val[1])
                self.mainUI.frame_img.display_values(update_val[0], update_val[1])

    def calc_time(self):
        pass

    def check_shot(self):
        """
            shot ??? ???????????? ?????? ?????? ??????
        """
        if self.shot_finished:
            if self.cur_label != self.pre_label:
                self.shot_finished = False
        
        if (self.running
            and not self.shot_finished
            and not self.optic.shot_thread.shot_end):

            if self.cur_label in self.protocol.shot_labels: # If current label is shot label
                self.cur_action = self.protocol.get_label_action(self.cur_label)
                target_temp = self.cur_action["Temp"]
                
                if (self.cur_action["Time"] == 0
                    and not self.optic.shot_thread.shotting
                    and target_temp-0.3 <= self.chamber_temp <= target_temp+0.3):
                    fluor = self.mainUI.frame_ctrl.selected_fluor
                    self.optic.shot(self.cur_loop, self.cur_label, fluor)

    def set_update_vals(self, label, fluor, values):
        self.update_vals.append((fluor, values))

    '''
        Arduino & Camera ?????? ?????????
    '''
    def chamber_take_out(self, state):
        self.mainUI.chamber_take_out_event(state)

        if state:
            print("?????????")
            #self.arduino_serial.lid_backward()
            #self.arduino_serial.chamber_forward()
            time.sleep(5)
        else:
            #self.arduino_serial.chamber_backward()
            #self.arduino_serial.lid_forward()
            time.sleep(5)

        self.mainUI.frame_ctrl.btn_take_out.setDisabled(False)