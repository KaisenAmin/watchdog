import os
import psycopg2
import sys
import csv
import subprocess
import json
import time
import logging
import threading
from Scripts import minmizeWindow
from Scripts.threadManager import * # my minimize lib for minimize process after run
from Scripts.logger import *
import win32gui
import win32con
import shutil
from Scripts.speechRec import *
from Scripts import connection
import speech_recognition as sr
from datetime import datetime
from PyQt5.QtWidgets import QColorDialog, QAction, QMessageBox
from PyQt5 import QtWidgets, uic, QtGui, QtCore
from PyQt5.QtWidgets import *
import psutil
from PyQt5.QtCore import pyqtSlot
from subprocess import *
from Scripts.plot import *
import connection
# import win32serviceutil
# import win32service
# import win32event
# import servicemanager
# import socket


# class AppServerSvc (win32serviceutil.ServiceFramework):
#     _svc_name_ = "WatchDog"
#     _svc_display_name_ = "WatchDog"

#     def __init__(self,args):
#         win32serviceutil.ServiceFramework.__init__(self,args)
#         self.hWaitStop = win32event.CreateEvent(None,0,0,None)
#         socket.setdefaulttimeout(60)

#     def SvcStop(self):
#         self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
#         win32event.SetEvent(self.hWaitStop)

#     def SvcDoRun(self):
#         servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
#                               servicemanager.PYS_SERVICE_STARTED,
#                               (self._svc_name_,''))
#         self.main()

#     def main(self):
#         pass


class Main():
    # static field variable
    dialogs = list()
    save_process_for_running = []
    saver_name = []
    def __init__(self):

        self.file_address = os.path.dirname(__file__)
        self.table_values = []
        self.process_dictionary = []
        self.process_name_color_dict = []
        self.process_color_table = []

        self.kill_flag_click = True
        self.main_thread = threading.Thread()
        self.thread_saver = None
        self.check_function_address = []
        
        self.now = QtCore.QDateTime.currentDateTime()

        self.kill_info = {
            'MemoryMin': 0,
            'MemoryMax': 0,
            'CpuMax': 0,
            'CpuMin': 0
        }

        self.counter = 0

    def get_class_index(self, class_name):
        self.index = None
        for index, i in enumerate(Main.dialogs):
            if i.__class__.__name__ == class_name:
                self.index = index
                break
        return self.index

    def get_pid_proccess_name(self, process_name):
        self.pid_saver = []

        if type(process_name) == type(str()):
            for proc in psutil.process_iter():
                try:
                    if process_name == proc.name():
                        return proc.pid
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

        else:
            for name in process_name:
                self.value_process_name = name[::-1]
                self.value_process_name = self.value_process_name[0:self.value_process_name.find('\\')][::-1]

                try:
                    for proc in psutil.process_iter():
                        if self.value_process_name == proc.name():
                            self.pid_saver.append(proc.pid)
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

        return self.pid_saver

    def get_session_name(self, proc_name):
        p_tasklist = subprocess.Popen('tasklist.exe /fo csv',
                              stdout=subprocess.PIPE,
                              universal_newlines=True)

        pythons_tasklist = []
        for p in csv.DictReader(p_tasklist.stdout):
            if p['Image Name'] == proc_name:
                return p['Session Name']

    def kill_process(self, proc_name):
        for pr in psutil.process_iter():
            try:
                if pr.name() == proc_name:
                    pr.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

    def delete_from_grid(self, proc_name):
        for row in range(Main.dialogs[0].ProcessGrid.rowCount()):
            try:
                if Main.dialogs[0].ProcessGrid.item(row, 0).text() == proc_name:
                    Main.dialogs[0].ProcessGrid.takeItem(row, 0)
                    Main.dialogs[0].ProcessGrid.takeItem(row, 1)
                    Main.dialogs[0].ProcessGrid.takeItem(row, 2)
            except AttributeError:
                continue



    def process_thread_management(self):
        self.main_thread = threading.Timer(1.0, self.process_thread_management)
        self.main_thread.start()

        self.index = 0
        for proc in Main.save_process_for_running:
            if not self.check_for_start_kill(proc):
                print('Kill')
                print(Main.saver_name[self.index])
                self.delete_from_grid(Main.saver_name[self.index])
                self.kill_process(Main.saver_name[self.index] + '.exe')
                    
                Main.save_process_for_running.remove(proc)
                Main.saver_name.remove(Main.saver_name[self.index])
                self.index = 0
                    
                if len(Main.save_process_for_running) == 0:
                    print('Len')
                    Main.dialogs[0].mainProcBtn.setEnabled(True)
                    Main.dialogs[0].mainProcBtn.click()
                    
                    self.main_thread.cancel()
                    break

            self.index += 1


    def check_for_start_kill(self, proc):
        if proc['StartTimeHour'] <= self.now.currentDateTime().time().hour() and self.now.currentDateTime().time().hour() <= proc['KillTimeHour'] and \
                proc['StartTimeMinute'] <= self.now.currentDateTime().time().minute() and self.now.currentDateTime().time().minute() <= proc['KillTimeMinute'] and \
                proc['StartTimeYear'] <= self.now.currentDateTime().date().year() and self.now.currentDateTime().date().year() <= proc['KillTimeYear'] and \
                proc['StartTimeMonth'] <= self.now.currentDateTime().date().month() and self.now.currentDateTime().date().month() <= proc['KillTimeMonth'] and \
                proc['StartTimeDay'] <= self.now.currentDateTime().date().day() and self.now.currentDateTime().date().day() <= proc['KillTimeday'] and \
                proc['StartTimeIdentifire'] == self.now.currentDateTime().time().toString('a'):
                    self.counter += 1 
                    return True 

        else:
            return False 


    def get_memory_percent(self, name_process):
        for pr in psutil.process_iter():
            try:
                if name_process == pr.name():
                    return pr.memory_full_info().rss / 1024 ** 2

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

    def get_cpu_percent(self, name_process):
        for pr in psutil.process_iter():
            try:
                if name_process == pr.name():
                    return pr.cpu_percent()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

class DataBaseUi(QtWidgets.QMainWindow, Main):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        uic.loadUi(self.file_address + "\\Ui\\db.ui", self)

        
        self.setFixedSize(490, 550)
        self.setWindowTitle("DB Operation")

        self.closeBtn.clicked.connect(self.close)
        self.browseBtn.clicked.connect(self.db_file_operation)
        self.showTableBtn.clicked.connect(self.show_database_value)
        self.consoleOpBtn.setShortcut('Ctrl+R')
        self.consoleOpBtn.clicked.connect(self.console_command_operation)

        self.dbPlainText.setStyleSheet("font-size:10px; font-weight: 500; font-family:arial")


    def console_command_operation(self):
        self.text_command = self.dbPlainText.toPlainText()
        if self.DbNameLineEdit.text() == "":
            QMessageBox.information(self, "DB Warn", "Please Insert TABLE NAME...")
        else:
            self.add_command = ""
            self.list_row_command = []
            self.counter = 1
            for ch in self.text_command:
                if ch == ';':
                    self.new_value = connection.sql_command_operation(self.add_command.strip(), self.dbLineEdit.text(), self.DbNameLineEdit.text())
                    self.show_database_value(flag=True, table_value=self.new_value)
                    self.add_command = ""
                else:
                    self.add_command += ch

    def show_database_value(self, flag = False, table_value = None):
        if flag == True:
            self.dbListWidgetTable.clear()
            self.counter = 1
            for row in table_value:
                self.text = f"[{self.counter}] -- "
                for col in row:
                    self.text += str(col) + " | "
                self.dbListWidgetTable.addItem(self.text)
                self.counter += 1

        else:
            self.run_notepad = lambda : os.system("notepad.exe " + self.dbLineEdit.text())
            self.thread_run_notepad = threading.Thread(target = self.run_notepad)
            self.thread_run_notepad.start()

            if self.dbLineEdit.text() == "":
                QMessageBox.information(self, "DB Warn", "Please Insert DataBase File...")
            else:
                self.rows_sql = connection.reader_sql(self.dbLineEdit.text())
                self.len_column_sql = len(self.rows_sql[0])
                self.table_counter = 0
                self.counter = 0

                print(self.rows_sql)
                for row in self.rows_sql:
                    self.dbListWidgetTable.addItem(row[len(row) - 1] + "\n " + str(20 * '-'))
                    self.row_value = row[0]
                    self.text = f"[{self.counter}] -- "
                    for index_i in self.row_value:
                        self.text += str(index_i) + " | "
                    self.dbListWidgetTable.addItem(self.text)
                    self.counter += 1
                        

    def db_file_operation(self):
        self.dbLineEdit.setText('')

        self.filter = "db(*.db, *.sql)"
        self.open_file_database = QFileDialog.getOpenFileName(self, caption="Select DataBase", directory=str(QtCore.QDir.homePath), filter=self.filter)
        
        self.dbLineEdit.setText(self.open_file_database[0])
        

class ParameterCheck(Main):
    def __init__(self):
            self.check_function_address = [
            self.check_start_time,
            self.check_kill_time,
            self.check_memory_min,
            self.check_memory_max,
            self.check_cpu_min,
            self.check_cpu_max
        ]
        
    def return_function_address(self, id):
        return self.check_function_address[id]

    def check_memory_min(self, id, process_name, name,row_index, col_index):
        print('Memory value' + str(id))

    def check_memory_max(self, process_name, id, name, row_index, col_index):
        pass 

    def check_cpu_min(self, id, process_name, name, row_index, col_index):
        pass 

    def check_cpu_max(self, id, process_name, name, row_index, col_index):
        pass 

    def check_start_time(self, id, process_name, name, row_index, col_index):
        pass 


    def check_kill_time(self, id, process_name, name, row_index, col_index):
        pass 



class KillTimeHandler(QtWidgets.QMainWindow, Main):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        uic.loadUi(self.file_address + "\\Ui\\kill_start_time_handler.ui", self)
        self.setWindowTitle("Handler_Operation")
        self.setFixedSize(280, 230)

        self.now = QtCore.QDateTime.currentDateTime()

        self.startTimeDate.setDateTime(self.now)
        self.killTimeDate.setDateTime(self.now)

        self.setBtn.setShortcut('Return')
        self.closeBtn.clicked.connect(self.close)
        self.setBtn.clicked.connect(self.set_handler_operation)

    def check_start_time(self):
        
        if self.startTimeDate.date().year() < self.now.date().year() or\
            self.startTimeDate.date().month() < self.now.date().month() or\
            self.startTimeDate.date().day() < self.now.date().day() or\
            self.startTimeDate.time().hour() < self.now.time().hour() or\
            self.startTimeDate.time().minute() < self.now.time().minute() or\
            self.startTimeDate.time().second() < self.now.time().second() or\
            self.startTimeDate.time().toString('a') != self.now.time().toString('a'):
                return False 
        else:
            return True
        
    def check_kill_time(self):
        if self.killTimeDate.date().year() < self.now.date().year() or\
            self.killTimeDate.date().month() < self.now.date().month() or\
            self.killTimeDate.date().day() < self.now.date().day() or\
            self.killTimeDate.time().hour() < self.now.time().hour() or\
            self.killTimeDate.time().minute() < self.now.time().minute() or\
            self.killTimeDate.time().second() < self.now.time().second() or\
            self.killTimeDate.time().toString('a') != self.now.time().toString('a'):
                return False 
        else:
            return True

    def set_handler_operation(self):
        try:
            if not self.check_start_time():
                raise Exception('Set Start Time True')

            if not self.check_kill_time():
                raise Exception('Set Kill Time True')

            self.kill_class_index = self.get_class_index('SetTimeHandlerUi')
            if self.kill_flag_click:
                
                Main.save_process_for_running.append(
                    {
                        'ProcessDirName': Main.dialogs[self.kill_class_index].proListWidget.item(Main.dialogs[self.kill_class_index].proListWidget.currentRow()).text(),
                        'StartTimeHour': self.startTimeDate.time().hour(),
                        'StartTimeMinute': self.startTimeDate.time().minute(),
                        'StartTimeSecond': self.startTimeDate.time().second(),
                        'StartTimeYear': self.startTimeDate.date().year(),
                        'StartTimeMonth': self.startTimeDate.date().month(),
                        'StartTimeDay': self.startTimeDate.date().day(),
                        'StartTimeIdentifire': self.startTimeDate.time().toString('a'),
                        'KillTimeHour': self.killTimeDate.time().hour(),
                        'KillTimeMinute': self.killTimeDate.time().minute(),
                        'KillTimeSecond': self.killTimeDate.time().second(),
                        'KillTimeYear': self.killTimeDate.date().year(),
                        'KillTimeMonth': self.killTimeDate.date().month(),
                        'KillTimeday': self.killTimeDate.date().day(),
                        'KillTimeIdentifire': self.killTimeDate.time().toString('a'),
                        'MemoryMin': self.MemoryMinSpin.value(),
                        'MemoryMax': self.MemoryMaxSpin.value(),
                        'CpuMin': self.cpuMinSpin.value(),
                        'CpuMax': self.cpuMaxSpin.value(),
                        'KILL_CLICK_FLAG': self.kill_flag_click
                    }
                )
                self.kill_flag_click = False
                

        except Exception as error:
            QMessageBox.information(self, 'Time Exception', str(error))

        else:
            self.close()

class SetTimeHandlerUi(QtWidgets.QMainWindow, Main):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        uic.loadUi(self.file_address + "\\Ui\\timeHandler.ui", self)

        self.setWindowTitle("TimeHandler")
        self.setFixedSize(368, 405)

        self.processAddressLine.setEnabled(False)
        self.processNameLine.setEnabled(False)
        self.browseBtn.setEnabled(False)
        


        self.startTimeEdit.dateTimeChanged.connect(self.datetime_changed)
        self.proListWidget.installEventFilter(self)
        self.startChBox.stateChanged.connect(self.checkBoxChangedAction)
        self.closeBtn.clicked.connect(self.close)
        self.browseBtn.clicked.connect(self.open_file_dialog)
        self.setBtn.clicked.connect(self.set_process_time_handle)
        self.setBtn.setShortcut('Return')

        

        self.startTimeEdit.setDateTime(self.now)


    @QtCore.pyqtSlot()
    def actionClicked(self):
        action = self.sender()
        if action.text() == 'KillTimeHandler':
            self.kill_flag_click = True
            kill_start_time = KillTimeHandler()
            self.dialogs.append(kill_start_time)
            kill_start_time.show()


    def base_info_process(self, index, flag):
        self.value_base_process = {
            'ProcessDirName': self.proListWidget.item(0).text(),
            'StartTimeHour': self.now.time().hour(),
            'StartTimeMinute': self.now.time().minute(),
            'StartTimeSecond': self.now.time().second(),
            'StartTimeYear': self.now.date().year(),
            'StartTimeMonth': self.now.date().month(),
            'StartTimeDay': self.now.date().day(),
            'StartTimeIdentifire': self.now.time().toString('a'),
            'KillTimeHour': 0,
            'KillTimeMinute': 0,
            'KillTimeSecond': 0,
            'KillTimeYear': 0,
            'KillTimeMonth': 0,
            'KillTimeday': 0,
            'KillTimeIdentifire': 0,
            'MemoryMin': 0,
            'MemoryMax': 0,
            'CpuMin': 0,
            'CpuMax': 0,
            'KILL_CLICK_FLAG': self.kill_flag_click
        }

        if flag:
            self.value_base_process['ProcessDirName'] = self.proListWidget.item(index).text()

        return self.value_base_process


    def set_process_time_handle(self):
        if self.processNameLine.text() == '' and self.processNameLine.isEnabled and self.startChBox.isChecked():
            QMessageBox.information(self, "Info Message", "Fill The Process Line")
        else:
            # if not self.kill_flag_click:
            for self.iterator in range(0, self.proListWidget.count()):
                self.value = self.proListWidget.item(self.iterator).text()

                if len(Main.save_process_for_running) == 0:
                    for self.iterator in range(0, self.proListWidget.count()):
                        Main.save_process_for_running.append(self.base_info_process(self.iterator, flag = True))
                    break
                else:
                    print(len(Main.save_process_for_running))
                    for index, proc in enumerate(Main.save_process_for_running):
                        self.value = self.proListWidget.item(index).text()
                        if proc['ProcessDirName'] == self.value:
                            print('Equal')
                            continue 
                        else:
                            Main.save_process_for_running.append(self.base_info_process(index, flag = True)) 
                    else:
                        break 
            
            for i in Main.save_process_for_running:
                print(i)
            # Main.saver_name = []
            self.kill_info = [{
                'MemoryMin': 0,
                'MemoryMax': 0,
                'CpuMax': 0,
                'CpuMin': 0
            } for i in range(len(Main.save_process_for_running))]

            for proc_list in Main.save_process_for_running:
                if self.check_for_start_kill(proc_list):
                    subprocess.Popen(proc_list['ProcessDirName'], shell = False)
                    
                    value = proc_list['ProcessDirName'][::-1]
                    value = value[:value.find('/')]
                    value = value[::-1]
                    value = value[:value.find('.')]
                    print(value)
                    Main.saver_name.append(value)
                    minmizeWindow.window_handler(value)


        self.row = 1
        self.col = 0
        # self.insert_class_index = self.get_class_index('InsertModeUi')
        Main.dialogs[0].ProcessGrid.setRowCount(len(Main.save_process_for_running) + 1)
        Main.dialogs[0].t1.cancel()
        Main.dialogs[0].ProcessGrid.clear()
        Main.dialogs[0].ProcessGrid.setItem(0, 0, QTableWidgetItem('ProcessName'))
        Main.dialogs[0].ProcessGrid.setItem(0, 1, QTableWidgetItem('PID'))
        Main.dialogs[0].ProcessGrid.setItem(0, 2, QTableWidgetItem('SessionName'))

        Main.dialogs[0].set_disable_flag()

        
        for index, proc in enumerate(Main.save_process_for_running):
            try:
                print(Main.saver_name[index] + ".exe")
                self.pid = self.get_pid_proccess_name(Main.saver_name[index] + ".exe")
                self.session_name = self.get_session_name(Main.saver_name[index] + ".exe")

                self.value = [Main.saver_name[index], self.pid, self.session_name]
                
                for v in self.value:
                    self.text_value = QTableWidgetItem(str(v))
                    self.text_value.setFlags(QtCore.Qt.ItemIsEnabled)
                    Main.dialogs[0].ProcessGrid.setItem(self.row, self.col, self.text_value)
                    self.col += 1
                self.row += 1
                self.col = 0
            except IndexError:
                continue 

        # self.thread_saver = [[0 for i in range(6)] for j in range(len(Main.save_process_for_running))]
        # self.thread_object_class = [[ParameterCheck() for i in range(6)] for j in range(len(Main.save_process_for_running))]


        # self.whatchdog_thread_name = ['StartTime', 'KillTime', 'MemoryMin', 'MemoryMax', 'CpuMin', 'CpuMax']
        # self.thread_id = 1


        # for index, proc in enumerate(Main.save_process_for_running):
        #     for j in range(0, 6):
        #         self.thread_saver[index][j] = threading.Thread()
        #         self.thread_saver[index][j] = threading.Timer(interval = 1.0, args = (self.thread_id, Main.saver_name[index], Main.saver_name[index] + '_' + self.whatchdog_thread_name[j], index, j), \
        #             function = self.thread_object_class[index][j].return_function_address(j))
        #         self.thread_saver[index][j].start()
        #         self.thread_id += 1

        # Main.dialogs[0].mainProcBtn.setEnabled(True) 
        self.process_thread_management()

        self.close()


    def datetime_changed(self):
        pass 

    def checkBoxChangedAction(self, state):
        if (QtCore.Qt.Checked == state):
            self.processAddressLine.setEnabled(True)
            self.processNameLine.setEnabled(True)
            self.browseBtn.setEnabled(True)
        else:
            self.processAddressLine.setEnabled(False)
            self.processNameLine.setEnabled(False)
            self.browseBtn.setEnabled(False)

        
    def open_file_dialog(self):
        self.processAddressLine.setText('')
        self.processNameLine.setText('')

        self.filter = "exe(*.exe)"
        self.open_file_process = QFileDialog.getOpenFileName(self, caption="Select Process", directory=str(QtCore.QDir.homePath), filter=self.filter)
        self.file_name = self.open_file_process[0][::-1]
        self.file_name = self.file_name[0:self.file_name.find('/')]

        self.processAddressLine.setText(self.open_file_process[0])
        self.processNameLine.setText(self.file_name[::-1])

        self.proListWidget.addItem(QListWidgetItem(self.processAddressLine.text()))

    def eventFilter(self, obj, event):
        if (event.type() == QtCore.QEvent.ContextMenu and obj is self.proListWidget):
            self.menu = QtWidgets.QMenu()
            
            self.menu.addAction('KillTimeHandler', self.actionClicked)
            if self.menu.exec_(event.globalPos()):
                item = obj.itemAt(event.pos())


        return super().eventFilter(obj, event)
# this class is for set process by id 
class FinddUi(QtWidgets.QMainWindow, Main):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        uic.loadUi(self.file_address + "\\Ui\\find.ui", self)
        self.setWindowTitle("FindProcess")
        self.closeBtn.clicked.connect(self.close)
        self.findBtn.setShortcut('Return')

        self.findBtn.clicked.connect(lambda : self.find_process(self.proLineEdit.text()))
        self.findChBox.stateChanged.connect(self.checkBoxChangedAction)


    def checkBoxChangedAction(self, state):
        if (QtCore.Qt.Checked == state):
            self.only_int = QtGui.QIntValidator()
            self.proLineEdit.setValidator(self.only_int)
            self.statusBar().showMessage("Just Digit For PID")
        else:
            self.reg_ex = QtCore.QRegExp("^.*$")
            self.input_validator = QtGui.QRegExpValidator(self.reg_ex, self.proLineEdit)
            self.proLineEdit.setValidator(self.input_validator)
            

    # def get_session_name(self, proc_name):
    #     p_tasklist = subprocess.Popen('tasklist.exe /fo csv',
    #                           stdout=subprocess.PIPE,
    #                           universal_newlines=True)

    #     pythons_tasklist = []
    #     for p in csv.DictReader(p_tasklist.stdout):
    #         if p['Image Name'] == proc_name:
    #             return p['Session Name']


    def find_process(self, process_value):
        self.close()
        self.number_row_Process_grid = Main.dialogs[0].ProcessGrid.rowCount()
        self.save_process = list()

        for pr in psutil.process_iter():
            try:
                if pr.name() == process_value + ".exe":
                    self.save_process.append(
                    {
                        'ProcessName': pr.name(),
                        'PID': pr.pid,
                        'SessionName': self.get_session_name(pr.name())
                    }
                )

            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue 

        # for number in range(1, self.number_row_Process_grid):
        #     if Main.dialogs[0].ProcessGrid.item(number, 0).text().strip() == process_value :
                
        Main.dialogs[0].ProcessGrid.clear()
        self.row = 1
        self.col = 0

        if len(self.save_process) > 0:
            Main.dialogs[0].ProcessGrid.setItem(0, 0, QTableWidgetItem('ProcessName'))
            Main.dialogs[0].ProcessGrid.setItem(0, 1, QTableWidgetItem('PID'))
            Main.dialogs[0].ProcessGrid.setItem(0, 2, QTableWidgetItem('SessionName'))

            Main.dialogs[0].set_disable_flag()

            Main.dialogs[0].ProcessGrid.setRowCount(len(self.save_process))
            for row in self.save_process:
                for value in row.items():
                    Main.dialogs[0].ProcessGrid.setItem(self.row, self.col, QTableWidgetItem(str(value[1])))
                    self.col += 1
                self.col = 0
                self.row += 1
            Main.dialogs[0].mainProcBtn.setEnabled(True)
            Main.dialogs[0].t1.cancel()

        else:
            QMessageBox.information(self, "FindMessage", f"Process {process_value} Not Find.")



class ProcessIdUi(QtWidgets.QMainWindow, Main):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        uic.loadUi(self.file_address + "\\Ui\\processId.ui", self)

        self.setFixedSize(350, 290)
        self.setWindowTitle("SetProcessId")
        self.createButton.setShortcut('Return')

        self.closeButton.clicked.connect(self.close)
        self.okButton.clicked.connect(self.do_change_okbutton)
        self.createButton.clicked.connect(self.set_number_processId)
        self.numberProcessTable.cellDoubleClicked.connect(self.on_click)

    def on_click(self, row, col):
        if col == 2:
            self.color_name = QColorDialog.getColor()
            self.row = row
            self.col = col
            if self.color_name.isValid():
                self.numberProcessTable.setItem(self.row, self.col, QTableWidgetItem(self.color_name.name()))
            self.process_color_table.append((self.row, self.col, self.color_name.name()))

    def do_change_okbutton(self):
        Main.dialogs[0].ProcessGrid.clear()
        Main.dialogs[0].ProcessGrid.setRowCount(int(self.numberProcessLine.text()) + 1)
        Main.dialogs[0].ProcessGrid.setColumnCount(3)

        for row in range(0, int(self.numberProcessLine.text()) + 1):
            if row > 0:
                self.color_value = self.process_color_table[row - 1][2]
            for col in range(3):  
                self.value_item = self.numberProcessTable.item(row, col).text()
                self.item = QTableWidgetItem(self.value_item)

                if col == 2 and self.value_item == '' and row != 0:
                    self.color_value = '#ff0000'
                    
                if row == 0:
                    self.item.setBackground(QtGui.QBrush(QtGui.QColor(255, 255, 255)))
                else:
                    self.value_item = self.color_value.lstrip('#')
                    self.hex_convert_rgb = tuple(int(self.value_item[i:i+2], 16) for i in (0, 2, 4))
                    self.hex_convert_rgb = [int(i) for i in self.hex_convert_rgb]
                    self.item.setBackground(QtGui.QBrush(QtGui.QColor(self.hex_convert_rgb[0], self.hex_convert_rgb[1], self.hex_convert_rgb[2])))

                Main.dialogs[0].ProcessGrid.setItem(row, col, QTableWidgetItem(self.item))

        self.close()
        
    def set_number_processId(self):
        try:
            self.process_number = int(self.numberProcessLine.text())
            if self.process_number > 0:
                self.numberProcessTable.setRowCount(self.process_number + 1)
                self.numberProcessTable.setColumnCount(3)
                self.numberProcessTable.setItem(0, 0, QTableWidgetItem("ProcessId"))
                self.numberProcessTable.setItem(0, 1, QTableWidgetItem("Comment"))
                self.numberProcessTable.setItem(0, 2, QTableWidgetItem("Color"))
            elif self.process_number < 0:
                QMessageBox.information(self, "Negative Number", "Please Inser Positive Number")
                self.numberProcessLine.setText('')
                
        except Exception as error:
            self.message_box = QMessageBox.question(self, "Select", "Please Enter number of ProcessId...\n Do You Want to Continue???", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)
            if self.message_box == QMessageBox.Yes:
                self.close()
                self.show()
            else:
                self.close()
                Main.dialogs[0].statusBar().showMessage("Not Set ProcessId!!!")
                

class InsertModeUi(QtWidgets.QMainWindow, Main):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        uic.loadUi(self.file_address + "\\Ui\\inserMode.ui", self)

        self.setFixedSize(380, 350)
        self.setWindowTitle("InsertProcess")
        self.setWindowIcon(QtGui.QIcon(self.file_address + "\\Images\\insertProcess.png"))

        self.closeButton.clicked.connect(self.close)
        self.okButton.clicked.connect(self.do_change_ok_button)
        self.processIdCh.stateChanged.connect(self.checkBoxChangedAction)
        self.processNameCh.stateChanged.connect(self.checkBoxChangedAction)

        self.colorButton.clicked.connect(self.get_color)
        self.browseButton.clicked.connect(self.get_file)

        self.dir_file_list = []
    # def get_pid_proccess_name(self, process_name):
    #     self.pid_saver = []
        
    #     for name in process_name:
    #         self.value_process_name = name[::-1]
    #         self.value_process_name = self.value_process_name[0:self.value_process_name.find('\\')][::-1]
    #         try:
    #             for proc in psutil.process_iter():
    #                 if self.value_process_name == proc.name():
    #                     self.pid_saver.append(proc.pid)
    #                     break 
    #         except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
    #             continue

    #     return self.pid_saver

    def do_change_ok_button(self):
        self.number_of_list_process = self.listWidget.count()
        self.column_name = ['ProcessName', 'PID', 'Color']
        self.name_process_list = list()

        for row in range(int(self.number_of_list_process)):
            self.row_value = self.listWidget.item(row).text().split(' | ')
            self.process_name_color_dict.append(
                {
                    self.column_name[0]:self.row_value[0],
                    self.column_name[1]:self.row_value[1],
                    self.column_name[2]:self.row_value[2]
                }
            )
        
        Main.dialogs[0].ProcessGrid.clear()
        Main.dialogs[0].ProcessGrid.setRowCount(self.listWidget.count() + 1)
        Main.dialogs[0].ProcessGrid.setColumnCount(3)

       
        Main.dialogs[0].ProcessGrid.setItem(0, 0, QTableWidgetItem(self.column_name[0]))
        Main.dialogs[0].ProcessGrid.setItem(0, 1, QTableWidgetItem(self.column_name[1]))
        Main.dialogs[0].ProcessGrid.setItem(0, 2, QTableWidgetItem(self.column_name[2]))
        for index, r in enumerate(self.process_name_color_dict):
            self.name_process_list.append(self.dir_file_list[index] + '\\' + r['ProcessName'])

        for i in self.name_process_list:
            subprocess.Popen(i, shell = False)

        self.pid_list_values = self.get_pid_proccess_name(self.name_process_list)
        # print(self.pid_list_values)
        
        self.r = 1
        self.c = 0
        self.col_counter = 0
        for row in self.process_name_color_dict:
            row['PID'] = self.pid_list_values[self.col_counter]
            # print(row['PID'])
            self.col_counter += 1

            if row['Color'] == '':
                row['Color'] = '#ffffff'

            self.value_item = row['Color'].lstrip('#')
            self.hex_convert_rgb = tuple(int(self.value_item[i:i+2], 16) for i in (0, 2, 4))
            self.hex_convert_rgb = [int(i) for i in self.hex_convert_rgb]

            for col in row.items():
                # print(col)
                self.value_item = str(col[1])
                
                self.item = QTableWidgetItem(self.value_item)

                self.item.setBackground(QtGui.QBrush(QtGui.QColor(self.hex_convert_rgb[0], self.hex_convert_rgb[1], self.hex_convert_rgb[2])))
                Main.dialogs[0].ProcessGrid.setItem(self.r, self.c, QTableWidgetItem(self.item))
                self.c += 1
            
            self.r += 1
            self.c = 0
               
        # Main.dialogs[0].ProcessGrid.cellDoubleClicked.connect(Main.dialogs[0].put_procces_on_listview)
        # Main.dialogs[0].ProcessGrid.cellDoubleClicked.connect(Main.dialogs[0].put_on_line)
                # Main.dialogs[0].ProcessGrid.setItem(row + 1, col, QTableWidgetItem(self.process_name_color_dict[row][self.column_name[col]]))
        self.listWidget.clear()
        self.close()

    def get_color(self):
        self.color_name = QColorDialog.getColor()
        if self.color_name.isValid():
            self.processColorEdit.setText(self.color_name.name())


    def checkBoxChangedAction(self, state):
        if (QtCore.Qt.Checked == state):
            if self.processIdCh.isChecked():
                self.processNameCh.setEnabled(False)
                self.procesFileBrowse.setEnabled(False)
                self.browseButton.setEnabled(False)
                
                processIdWindow = ProcessIdUi(self)
                Main.dialogs.append(processIdWindow)
                processIdWindow.show()
                self.close()

            else:
                self.processIdCh.setEnabled(False)
        else:
            self.processIdCh.setEnabled(True)
            self.processNameCh.setEnabled(True)
            
    def get_file(self):
        self.procesFileBrowse.setText('')
        self.file_name = QFileDialog.getOpenFileName(self, 'Open file', 'c:\\',"Executable File (*.exe)")


        self.program_name = self.file_name[0][-1::-1]
        self.program_name = self.program_name[0:self.program_name.find("/")]
        self.program_name = self.program_name[-1::-1]

        self.dir_file = self.file_name[0][0:self.file_name[0].find(self.program_name) - 1]
        self.procesFileBrowse.setText(self.file_name[0])
        self.color_value = self.processColorEdit.text()
        self.dir_file_list.append(self.dir_file)

        if len(self.color_value) == 0:
            self.color_value = "aqua"

        self.listWidget.addItem(self.program_name + ' | ' + self.dir_file + ' | ' + self.color_value )

        self.statusBar().showMessage(f'Process {self.program_name} add to the Item')


class Ui(QtWidgets.QMainWindow, Main):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.line_counter = 0
        self.main_pid = ''
        self.t1 = threading.Thread()
        # self.file_address = os.path.dirname(__file__)
        uic.loadUi(self.file_address + "\\Ui\\watchDogUI.ui", self)
        self.time_refresh = 5.0
        self.refreshTimeLine.setText(str(self.time_refresh))

        self.setFixedSize(720, 603)
        self.setWindowTitle("WatchDog")
        self.setWindowIcon(QtGui.QIcon(self.file_address + "\\Images\\watchdogicon.png"))
        self.ProcessGrid.horizontalHeader().setStretchLastSection(True)

        self.list_widget_head_item = "USERNAME" + (30 * ' ') + "NAME" + (20 * ' ') + "PID" + (20 * ' ') + "CPU" + (20 * ' ') + "MEMORY" + (20 * ' ') + "STATUS" + (20 * ' ') + "STARTED" + \
            (20 * ' ') + "ADDRESS"
        self.down_header_line_size = len(self.list_widget_head_item) * '_'

        
        self.header_list_item = QListWidgetItem(self.list_widget_head_item)
        self.down_header_line = QListWidgetItem(self.down_header_line_size)
        

        self.processListWidget.addItem(self.header_list_item)
        self.processListWidget.addItem(self.down_header_line)

        self.header_list_item.setFlags(self.header_list_item.flags() & ~QtCore.Qt.ItemIsEnabled)
        self.down_header_line.setFlags(self.down_header_line.flags() & ~QtCore.Qt.ItemIsEnabled)

        # self.save_file = QAction("&SaveAsJson", self)
        self.actionSaveAs.setShortcut('Ctrl+S')
        self.actionExit.setShortcut('Ctrl+Q')
        self.actionFind.setShortcut('Ctrl+F')
        self.actionTimeHandler.setShortcut('Ctrl+T')
        self.actionDB_Work.setShortcut('Ctrl+D')
        self.actionShow_Graph.setShortcut('Ctrl+G')


        # self.save_file.triggered.connect(self.saveProcessJson)
        self.browseProcessBtn.clicked.connect(self.browse_btn)
        self.ProcessGrid.cellDoubleClicked.connect(self.put_procces_on_listview)
        self.ProcessGrid.cellDoubleClicked.connect(self.put_on_line)
        self.InsertButton.clicked.connect(self.print_insert_button)
        self.actionExit.triggered.connect(quit)
        self.actionTimeHandler.triggered.connect(self.set_time_handler)
        self.actionSaveAs.triggered.connect(self.saveProcessJson)
        self.actionShow_Graph.triggered.connect(self.show_graph)
        self.actionFind.triggered.connect(self.find_process)
        self.actionDB_Work.triggered.connect(self.db_operation)
        self.actionSpeechProcess.triggered.connect(self.call_speech_rec)
        self.closeButton.clicked.connect(self.close)
        self.mainProcBtn.clicked.connect(self.process_operation)


        self.mainProcBtn.setEnabled(False)


        self.commandProcessText.insertPlainText(">>> ")
        # self.commandProcessText.textCursor().insertHtml('<p>>>> </p>')
        # self.commandProcessText.triggered.connect(self.keyPressEvent)
        
        self.commandProcessText.installEventFilter(self)
        self.processListWidget.installEventFilter(self)

        self.ProccessOperationCombo.addItem('Kill Process')
        self.ProccessOperationCombo.addItem('StartProcess')
        self.ProccessOperationCombo.addItem('Log Process')
        self.ProccessOperationCombo.addItem('Monitor Process')

        self.process_operation()
    
    def db_operation(self):
        database = DataBaseUi(self)
        self.dialogs.append(database)
        database.show()

    def show_graph(self):
        graph = GraphWindow(self)
        self.dialogs.append(graph)
        graph.show()
        
    def set_time_handler(self):
        time_handler = SetTimeHandlerUi(self)
        self.dialogs.append(time_handler)
        time_handler.show()

    def find_process(self):
        findWindow = FinddUi(self)
        self.dialogs.append(findWindow)
        findWindow.show()

    def put_procces_on_listview(self, row, column):
        try:
            self.show_process = psutil.Process(int(self.ProcessGrid.item(row, 1).text()))
            self.started_time = str(self.show_process.cwd)
            self.started_time = self.started_time[self.started_time.find('started='):self.started_time.find("')")]
            self.started_time = [i for i in self.started_time if i.isdigit() or i == ':']
            self.started_time = ''.join(self.started_time)

            self.process_line = self.show_process.username() +"|"+  (5 * ' ') + '|' + self.show_process.name() +'|' + (10 * ' ') + '|' + str(self.show_process.pid) + \
                '|' + (15 * ' ') + '|' + str(self.show_process.cpu_percent())+ '|' + (20 * ' ') + '|' + str(self.show_process.memory_info().rss / 1024) + '|' + (20 * ' ') + '|'+ self.show_process.as_dict()['status'] + \
                '|' + (20 * ' ') + '|' + self.started_time + '|'+ (20 * ' ') + '|'+ self.show_process.exe()

            self.process_value = QListWidgetItem(self.process_line)
            self.processListWidget.addItem(self.process_value)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            QMessageBox.information(self, "Process Event", "This Process Has AccessDenied Label")


    def browse_btn(self):
        self.filter = "exe(*.exe)"
        self.open_file_process = QFileDialog.getOpenFileName(self, caption="Select Process", directory=str(QtCore.QDir.homePath), filter=self.filter)
        self.file_name = self.open_file_process[0][::-1]
        self.file_name = self.file_name[0:self.file_name.find('/')]

        self.ProccessLineAddress.setText(self.open_file_process[0])
        self.ProccessLineName.setText(self.file_name)
        # print(self.open_file_process)

    def get_process_add(self, pid):
        try:
            self.pid_value = pid
            self.pid_value = psutil.Process(int(self.pid_value))
            return self.pid_value.exe()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return False 

    def put_on_line(self, row, col):
        try:
            self.process_address = str(self.get_process_add(self.ProcessGrid.item(row, 1).text()))

            if self.process_address != 'False':
                self.ProccessLineName.setText(self.ProcessGrid.item(row, 0).text())
                self.ProccessLineAddress.setText(self.process_address)
            else:
                raise Exception("The return Value of Process is not true")

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            QMessageBox.information(self, "Process Event", "This Process Has AccessDenied Label")
        except Exception as error:
            QMessageBox.information(self, "Process", str(error))

    def cell(self,var=""):
        self.item = QTableWidgetItem()
        self.item.setText(var)
        return self.item

    def call_speech_rec(self):
        
        self.th = threading.Thread(target = speech_rec)
        self.th.start()
        # self.statusBar().showMessage("Microphone Save Speech...")
        self.th.join()

    @QtCore.pyqtSlot()
    def actionClicked(self):
        action = self.sender()
        if action.text() == 'Delete':
            self.value = self.processListWidget.item(self.processListWidget.currentRow()).text()
            self.processListWidget.takeItem(self.processListWidget.currentRow())
            self.statusBar().showMessage(f'Process {self.value.split()[1]} is Deleted')
            
        elif action.text() == "Kill":
            self.item_text = self.processListWidget.item(self.processListWidget.currentRow()).text()
            self.pip_counter = 0
            self.pid_value_kill = ''

            for i in self.item_text:
                if i == '|':
                    self.pip_counter += 1
                elif self.pip_counter == 5:
                    break
                elif self.pip_counter >= 4 and i != '|' and i.isdigit():
                    self.pid_value_kill += i

            self.processListWidget.takeItem(self.processListWidget.currentRow())
            # print(self.item_text.split()[1][1:len(self.item_text.split()[1])-1])
            self.pro = psutil.Process(int(self.item_text.split()[2][1:len(self.item_text.split()[2])-1]))
            self.pro.kill()
            self.statusBar().showMessage(f'Process {self.item_text.split()[1]} has been Killed')
            # self.process_operation()

        elif action.text() == 'Log':
            pass 

                

    def eventFilter(self, obj, event):

        if (event.type() == QtCore.QEvent.ContextMenu and obj is self.processListWidget):
            self.menu = QtWidgets.QMenu()
            
            self.menu.addAction('Kill', self.actionClicked)
            self.menu.addAction('Log', self.actionClicked)
            self.menu.addAction('Delete', self.actionClicked)

            if self.menu.exec_(event.globalPos()):
                
                item = obj.itemAt(event.pos())
                try:
                    if item == None:
                        item.setText('')
                        raise Exception('Okkk')

                    self.counter = 0
                    for i in str(item.text()):
                        if i == '|':
                            self.counter += 1
                        if self.counter > 3 and i.isdigit():
                            self.main_pid += i
                        if self.counter > 5:
                            break
                except Exception as err:
                    pass 

        if event.type() == QtCore.QEvent.KeyPress and obj is self.commandProcessText:
            if event.key() == QtCore.Qt.Key_Return and self.commandProcessText.hasFocus() :
                
                self.cursor = self.commandProcessText.textCursor()
                
                self.cursor.insertText("test")
                # self.commandProcessText.setText("test")
                self.cursor.movePosition(QtGui.QTextCursor.EndOfLine, QtGui.QTextCursor.MoveAnchor, 1)
                # self.cursor.insertText("test")
                # print("Minus {0}".format(int(self.cursor.position()) + 5))
                
                # self.commandProcessText.setTextCursor(self.cursor)
                
        return super().eventFilter(obj, event)

    def saveProcessJson(self):
        self.save_file_dialog = QFileDialog.getSaveFileName(self, 'Save Json')
        self.save_file_dialog = list(self.save_file_dialog)
        
        if not self.save_file_dialog[0].find('.json'):
            self.save_file_dialog[0] += ".json"
        try:
            with open(self.save_file_dialog[0], 'w') as file_writer:
                    json.dump(self.process_dictionary, file_writer, sort_keys=True, indent=4)
        except Exception as error:
            self.message = QMessageBox.question(self, 'SetChoice', str(error) + "\nDo You Want to Continue???", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel)
            if self.message == QMessageBox.Yes:
                self.saveProcessJson()
                
    def print_insert_button(self):
            insertWindow = InsertModeUi(self)
            self.dialogs.append(insertWindow)
            insertWindow.show()
            # sys.exit(insertWindow.exec_())

    def process_operation(self):
        self.time_refresh = self.refreshTimeLine.text()
        self.ProcessGrid.clear()
        self.t1 = threading.Timer(float(self.time_refresh), self.process_operation)
        self.t1.start()
        
        

        result = subprocess.run(['tasklist'], stdout=subprocess.PIPE)
        logging.info(result.stdout.decode('utf-8').rstrip('\n'))

        self.chr = ""
        self.flag = False 
        # self.table_values = []
        self.process_dictionary = []
        
        self.process_string_add = ""
        self.process_column = ['processName', 'PID', 'SessionName', 'Session', 'Menu']
        self.process_column_counter = 0
        self.process_line = ""

        for string in result.stdout.decode('utf-8'):
            if string != '\n':
                self.chr += string 
            else:
                if(self.chr.find('=') >= 0 or self.chr.find('pid'.upper()) >= 0):
                    self.chr = ''
                else:
                    self.process_line = self.chr
                    self.value = ""
                    for index in range(0, len(self.process_line) - 1):
                        if self.process_line[index] == ' ' and self.process_line[index + 1] == ' ' and len(self.process_string_add) >= 0:
                            self.table_values.append(self.process_string_add)
                            self.process_string_add = ''
                            continue
                        else:
                            self.process_string_add += self.process_line[index]
                    
                    self.table_values = [i for i in self.table_values if i != '' ]

                    if len(self.table_values) > 0:
                        self.process_session_name = ''.join([i for i in self.table_values[1] if i.isalpha()])
                        self.pid_numbers = [int(pid) for pid in self.table_values[1] if pid.isdigit()]
                        self.pid_numbers = ''.join([str(i) for i in self.pid_numbers])
                        self.process_name = self.table_values[0]
                    
                        self.process_dictionary.append(
                            {
                                "ProcessName":self.process_name,
                                "PID":self.pid_numbers,
                                "processSession":self.process_session_name
                            }
                        )

                    self.table_values.clear()
                    self.chr = ''
                    self.process_string_add = ''
        self.set_data_tableProcess(self.process_dictionary)

    def set_data_tableProcess(self, process_di):
        self.ProcessGrid.setRowCount(len(process_di))
        self.ProcessGrid.setColumnCount(3)
        self.ProcessGrid.resize

        self.ProcessGrid.setItem(0, 0, QTableWidgetItem("ProcessName"))
        self.ProcessGrid.setItem(0, 1, QTableWidgetItem("PID"))
        self.ProcessGrid.setItem(0, 2, QTableWidgetItem("SessionName"))

        self.set_disable_flag()
        self.row_counter = 1
        self.col_counter = 0
        for row in process_di:
            for col in row.values():
                self.text_value = self.cell(col)
                self.text_value.setFlags(QtCore.Qt.ItemIsEnabled)
                self.ProcessGrid.setItem(self.row_counter, self.col_counter, self.text_value)
                self.col_counter += 1
            self.row_counter += 1
            self.col_counter = 0

        self.mainProcBtn.setEnabled(False)

    def set_disable_flag(self):
        self.ProcessGrid.item(0, 0).setFlags(QtCore.Qt.ItemIsEditable)
        self.ProcessGrid.item(0, 1).setFlags(QtCore.Qt.ItemIsEditable)
        self.ProcessGrid.item(0, 2).setFlags(QtCore.Qt.ItemIsEditable)


def check_log_file_size():
    file_address = os.path.dirname(__file__)

    log_thread = threading.Timer(30, check_log_file_size)
    log_thread.start()

    if os.path.getsize(file_address + "\\Logger.txt") > 10 ** 5:
        import datetime
        source = file_address + "\\Logger.txt"
        target = file_address + "\\LoggerArchive"

        if os.path.isdir(target):
            shutil.copyfile(source, target + "\\Logger" + str(datetime.datetime.now().date()) + ".txt")
        else:
            os.mkdir(target)
            shutil.copyfile(source, target + "\\Logger" + str(datetime.datetime.now().date()) + ".txt")
        
        os.remove(source)
        Logger.create_log_file()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    Logger.create_log_file()

    os.system('cls')
    Logger.log("The Program Start")
    Logger.log("After Start Program")
    check_log_file_size()

    MainWindow = Ui()
    Main.dialogs.append(MainWindow)
    MainWindow.show()
    
    # win32serviceutil.HandleCommandLine(AppServerSvc)
    
    
    sys.exit(app.exec_())


