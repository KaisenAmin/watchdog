from PyQt5 import QtWidgets, QtCore, uic, Qt
from PyQt5.QtWidgets import QMessageBox, QListWidgetItem
from PyQt5.QtGui import QColor
from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg
import sys  # We need sys so that we can pass argv to QApplication
import os
import psutil
import threading
from Scripts.logger import Logger
from random import randint

class GraphWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.file_address = os.path.dirname(__file__) # get dir addreess of my file
        Logger.log("***Plot UI Start***", file_name="PlotLogger.txt")
        self.process_item = [] # all the process and pid that we put in process list Widget 
        self.x_memory_percent_hour = list(range(10))
        self.y_memory_percent = []
        self.x_cpu_percent_hour = list(range(10))
        self.y_cpu_percent = []

        self.memory_thread = threading.Thread() # thread for update memory
        self.cpu_thread = threading.Thread() # thread for update cpu 

        self.file_address = self.file_address[::-1]
        self.file_address = self.file_address[self.file_address.find('\\')+1:]
        self.file_address = self.file_address[::-1]

        uic.loadUi(self.file_address + "\\Ui\\graphPlot.ui", self) # Load graph plot ui for use
        self.set_process_list() # iterate over all process for fill ListProcess Widget 

        self.setFixedSize(755, 645) # setSize of Graph window
        self.memoryWidget.setStyleSheet("border : 2px solid black") # set border for memory Graph widget
        self.cpuWidget.setStyleSheet("border : 2px solid black") # set border for cpu Graph Widget
        self.processListWidget.setStyleSheet("font-size : 13px")

        self.memoryWidget.setBackground('w') # set Background of memory graph widget to white
        self.cpuWidget.setBackground('w') # set Background of cpu graph widget to white

        self.refreshBtn.clicked.connect(self.set_process_list)
        self.closeBtn.clicked.connect(self.close) # signal for close button 
        self.findProcessBtn.setShortcut('Return') # set Shortcut for find button 'Return'
        self.findProcessBtn.clicked.connect(self.find_process) # signal&slot event for find_process button
        self.processListWidget.itemDoubleClicked.connect(self.update_process_graph) #signal&slot for item in processList when doubleClicked

        self.x = list(range(100))  # 100 time points
        self.y = [randint(0,100) for _ in range(100)]  # 100 data points

        self.pen = pg.mkPen(color=(255, 0, 0)) # color of my line for drawing in widget

        self.memory_data_line = self.memoryWidget.plot(self.x, self.y, pen = self.pen)
        self.cpu_data_line = self.cpuWidget.plot(self.x, self.y, pen = self.pen)

        self.memoryWidget.setXRange(0, 10) # x line of memory widget has 10 part
        self.cpuWidget.setXRange(0, 10) # x line of cpu widget has 10 part

        self.memoryWidget.setYRange(0, 1000) # y line of memory widget max is 1000 (megaByte)
        self.cpuWidget.setYRange(0, 100) # y line of cpu widget 100 (megabyte)

        self.memoryWidget.clear() # clear all data or line from mem plot 
        self.cpuWidget.clear() # clear all data or line from cpu plot 

    def closeEvent(self, event):
        # if program close without button cancel thread 
        if self.memory_thread.isAlive():
            self.memory_thread.cancel()
            self.cpu_thread.cancel()
            Logger.log("Close Window Plot", file_name="PlotLogger.txt")


    def refresh_colorize_process_list(self):
        self.processListWidget.clear() # clear processList for setItem again with color 
        flag = False

        for index, proc in enumerate(self.process_item):
            self.text_value = QListWidgetItem(proc) # get item text
            if self.find_value in proc: # if find my text in lineEdit in processList item 
                flag = True 
                self.text_value.setBackground(QColor('#48dbfb')) # change the background color of item 
                    
            self.processListWidget.addItem(self.text_value) # set item
        if not flag:
            Logger.log(f"Can not find Any Process with name {self.find_value}", file_name="PlotLogger.txt")
            self.statusBar().showMessage(f"Can not Find process {self.find_value}")

    def find_process(self): # method ofr find process in processListWidget
        self.find_value = str(self.findProcessLine.text()) # get text from find lineEdit

        try:
            if self.find_value == "": # check linedit is empty or not
                self.message_box = QMessageBox.question(self, "FindWarning", "Please Enter ProcessName...\n Do You Want to Continue???", QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Cancel) # ask me question button
                if self.message_box == QMessageBox.No: # if click no in messagebox close the Graph window
                    Logger.log("Program Closed --- select no bytton in QMessageBox", file_name="PlotLogger.txt")
                    self.close() # close window
            else:
                self.refresh_colorize_process_list() # call function for referesh and set BackGround Color in processListWidget
                Logger.log("After Colorize the process List", file_name="PlotLogger.txt")
     
        except Exception as err:
            Logger.log("We Have exception in find Process {}".format(self.find_value), file_name="PlotLogger.txt")
            pass 

    def get_memory_percent(self, proc_pid): # function for get memory percent in mg by pid of process 
        try:
            self.process = psutil.Process(proc_pid)
            Logger.log(f"Get Memory Percent Pid-- {proc_pid}", file_name="PlotLogger.txt")
            return self.process.memory_full_info().rss / 1024 ** 2 # return memory percent as MG

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess): # handle exception if access is denied
            Logger.log("We have Exception in Get Memory Percent function", file_name="PlotLogger.txt")
            pass 

    def get_cpu_percent(self, proc_pid): # method for get cpu percent by pid of process 
        try:
            self.process = psutil.Process(proc_pid) # get process by pid
            Logger.log(f'Get Cpu Percent Pid {proc_pid}', file_name="PlotLogger.txt")
            return self.process.cpu_percent() # return  cpu percent 

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            Logger.log("We have Exception in Get Cpu Percent function", file_name="PlotLogger.txt")
            pass

    def update_process_graph(self, item):
        self.memoryWidget.plot([], []) # set now data in memory plot 
        self.cpuWidget.plot([], [])

        if self.memory_thread.isAlive(): # check is my thread is live cancel them because thread should run at least 1 time 
            self.memory_thread.cancel() # cancel mem thread for run new selected process
            self.cpu_thread.cancel() # cancel cpu thread for run new selected process 

            self.memoryWidget.clear() # clear all data or line from mem plot 
            self.cpuWidget.clear() # clear all data or line from cpu plot 
            # Clear all data for append new data for new selected process 
            self.x_memory_percent_hour.clear()
            self.x_cpu_percent_hour.clear()
            self.y_cpu_percent.clear()
            self.y_memory_percent.clear()

            self.x_memory_percent_hour = list(range(10))
            self.x_cpu_percent_hour = list(range(10))

        self.process_name = str(item.text())[0:str(item.text()).find(" <<")] # parse the name process.exe from item in processList 
        self.process_pid = int(str(item.text())[str(item.text()).find(">> ") + 3:]) # parse the pid of process from item in processList when doubleClick event handle

        for y in range(10):
            self.y_memory_percent.append(self.get_memory_percent(self.process_pid)) # get the memory percent of my selected process
            self.y_cpu_percent.append(self.get_cpu_percent(self.process_pid)) # get the cpu percent of selected process 

        self.memory_data_line = self.memoryWidget.plot(self.x_memory_percent_hour, self.y_memory_percent, pen = self.pen)
        self.cpu_data_line = self.cpuWidget.plot(self.x_memory_percent_hour, self.y_memory_percent, pen = self.pen)


        self.update_memory_plot(self.process_pid) # run function for show memory data 
        self.update_cpu_plot(self.process_pid)

    def update_cpu_plot(self, process_pid):
        self.cpu_thread = threading.Timer(1.0, lambda : self.update_cpu_plot(process_pid)) # thread for update cpu process in plot async 
        self.cpu_thread.start() # each 1 second 

        self.x_cpu_percent_hour = self.x_cpu_percent_hour[1:] # for update the plot each second delete first element of x_mem_hour 
        self.x_cpu_percent_hour.append(self.x_cpu_percent_hour[-1] + 1) # now add a new element at the end 

        self.y_cpu_percent = self.y_cpu_percent[1:] # update the cpu list percent with new value because of this del first element for add new element
        self.y_cpu_percent.append(self.get_cpu_percent(process_pid))

        self.cpu_data_line.setData(self.x_cpu_percent_hour, self.y_cpu_percent) # set data in plot 


    def update_memory_plot(self, process_pid):
        self.memory_thread = threading.Timer(1.0, lambda : self.update_memory_plot(process_pid)) # create thread for ptimze asyn the memory value of a selected process
        self.memory_thread.start() # start thread each second run this function

        self.x_memory_percent_hour = self.x_memory_percent_hour[1:]  # Remove the first y element.
        self.x_memory_percent_hour.append(self.x_memory_percent_hour[-1] + 1)  # Add a new value 1 higher than the last.

        self.y_memory_percent = self.y_memory_percent[1:]  # Remove the first 
        self.y_memory_percent.append(self.get_memory_percent(process_pid))  # Add a new random value.

        self.memory_data_line.setData(self.x_memory_percent_hour, self.y_memory_percent)  # Update the data.
    

    def set_process_list(self):
        Logger.log("Get Process Runing List", file_name="PlotLogger.txt")
        self.processListWidget.clear()
        self.process_item.clear()

        for proc in psutil.process_iter(): # process over all the process
            try:
                self.processListWidget.addItem(f"{proc.name()} <<-->> {proc.pid}")
                self.process_item.append(f"{proc.name()} <<-->> {proc.pid}")
                 # fill the Process List widget with name and pid of process 
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess): # if we have accessDenied Exception just continue the loop not crash
                continue