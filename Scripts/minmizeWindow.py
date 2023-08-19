import win32con
import win32gui
import time 

toplist = []
winlist = [] 
find_process = [] 


def enum_callback(hwnd, results):
    winlist.append((hwnd, win32gui.GetWindowText(hwnd)))


def window_handler(value = ''):
    time.sleep(2)
    try:
        win32gui.EnumWindows(enum_callback, toplist)

        find_process = [(hwnd, title) for hwnd, title in winlist if value.lower() in title.lower() or title.lower().find(value.lower()) >= 0]
        find_process = find_process[0]

        win32gui.SetForegroundWindow(find_process[0])
        win32gui.ShowWindow(find_process[0], win32con.SW_MINIMIZE)
    except IndexError:
        pass 


