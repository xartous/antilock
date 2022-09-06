# Screen anti-locker
# Runs the idle check and if idle,
# runs the VolUp-VolDown commands to keep the activity going
# It goes to the tray bar by default
# By Mariusz Misiek
# Written for personal use :)

from tkinter import messagebox

from ctypes import Structure, windll, c_uint, c_int, sizeof, byref

import pyautogui

from tkinter import *
from pystray import MenuItem as item
import pystray
from PIL import Image

from threading import Thread
from threading import Event
from time import sleep

counter: int = 0
paused: bool = False


# Reads the counter of how many times the antilock prevented lock-in :)
def readCounter():
    global counter
    # open and read the file after the appending:
    try:
        f = open("antilock.cfg", "r")
        counter = int(f.read())
    except FileNotFoundError:
        f = open("antilock.cfg", "w")
        f.close()


# Updates the antilock prevention counter in the file
def updateCounter():
    global counter
    counter = counter + 1
    try:
        f = open("antilock.cfg", "w")
        f.write(str(counter))
        f.close()
    except FileNotFoundError:
        print("File not found!")


# The Windows structure to handle the last activity time in Windows
class LASTINPUTINFO(Structure):
    _fields_ = [
        ('cbSize', c_uint),
        ('dwTime', c_int),
    ]


# Reads the activity type in Windows (from Windows Kernel32 services)
# returns the number of seconds
def get_idle_duration():
    lastInputInfo = LASTINPUTINFO()
    lastInputInfo.cbSize = sizeof(lastInputInfo)
    if windll.user32.GetLastInputInfo(byref(lastInputInfo)):
        millis = windll.kernel32.GetTickCount() - lastInputInfo.dwTime
        return millis / 1000.0
    else:
        return 0


# Prevents lock-in if idle for more than 10 seconds
# updates the counter in the file
# reacts on the quit event
def idleantilock(event, pauseEvent):
    global paused
    while True:
        duration = str(get_idle_duration())
        print('User idle for seconds.' + duration)
        if float(duration) > 10:
            pyautogui.press('volumedown')
            sleep(1)
            pyautogui.press('volumeup')
            sleep(5)
            updateCounter()
        sleep(1)
        if pauseEvent.is_set():
            while paused:
                sleep(1)
            else:
                sleep(0)

        if event.is_set():
            break


globalIcon = None

# Create an instance of tkinter frame or window
win = Tk()

# Quit/stop event
stopEvent = Event()
pauseEvent = Event()

antilockerThread = Thread(target=idleantilock, args=(stopEvent, pauseEvent))


# Quit info message, stops the window and the thread
def byebye():
    messagebox.showinfo("Quitting", "AntiLock says bye bye!")
    win.destroy()
    stopEvent.set()


# Quit info message, stops the window and the thread
def pause():
    global paused
    pauseEvent.set()
    if not paused:
        pauseButton.config(text="Resume")
        paused = True
    else:
        pauseButton.config(text="Pause for 5 minutes")
        paused = False


win.title("AntiLock!")
try:
    win.iconbitmap("favicon.ico")
except Exception:
    pass

# Quit button on the small UX
quitButton = Button(win, text="Quit", command=byebye)
# Pause button on the small UX
pauseButton = Button(win, text="Pause for 5 minutes", command=pause)

# Label on the small UX to indicate the number of antilocks :)
infoLabel = Label(win, text="AntiLock helped you: " + str(counter) + " time(s)!")

# Set the size of the window, just a tiny one
win.geometry("280x90+500+500")


# Define a function for quit the window
def quit_window(icon, item):
    icon.stop()
    win.destroy()
    stopEvent.set()


# Define a function to show the window again
def show_window(icon, item):
    icon.stop()
    win.after(0, win.deiconify())


# Hide the window and show on the system taskbar
def hide_window():
    win.withdraw()
    try:
        image = Image.open("favicon.ico")
    except Exception:
        pass
    menu = (item('Quit', quit_window), item('Show', show_window))
    icon = pystray.Icon("name", image, "AntiLock!", menu)
    icon.run()


# Start the antilock thread
antilockerThread.start()
readCounter()
infoLabel.config(text="AntiLock helped you: " + str(counter) + " time(s)!")
quitButton.pack()
pauseButton.pack()
infoLabel.pack()

# Hide by default
win.protocol('WM_DELETE_WINDOW', hide_window)
hide_window()
win.mainloop()
