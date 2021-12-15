# -*- coding: utf-8 -*-
"""
Created on Sat Jul 25 10:22:26 2020

SYNOPSIS
========

::
    python3 wormy.py

DESCRIPTION
===========

    Provides various utility functions for mathematical calculations for the
    system. There are multiple functions that will provide several functions
    The system is designed primarily for the ms windows

MODULE CONTENTS
===============

::
    class LASTINPUTINFO(ctypes.Structure)
    def wait_until_idle(idle_time=60)
    def wait_until_active(tol=5)
    def timeRemaining(starttime, limit_secs)
    def getProcessList()

..  note::Note Windows System processes

    Some the functions use the windows system calls that may need to
    access the system internal memory

..  parsed-literal::

    try:
        function
    catch:

EXAMPLES
========

    Here is an example::

        python3 SysUtility.getProcessList()

SEE ALSO
========

    None

@author: Amit Gowda
"""
import ctypes
import ctypes.wintypes
from ctypes.wintypes import BOOL, HWND, RECT
from ctypes import windll
from ctypes import POINTER, WINFUNCTYPE
import time
import psutil
from collections import defaultdict
import pyttsx3 as speech
from threading import Thread


class TextSpeak(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.engine = speech.init()
        self.engine.setProperty('rate', 125)

    def speak(self, text):
        assert len(text)>0

        self.engine.say(text)
        self.engine.runAndWait()

    def getSpeakerEngine():
        return self.engine

    def run(self):
        while True:
            time.sleep(1)

    def __del__(self):
        self.engine.stop()


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ('cbSize', ctypes.wintypes.UINT),
        ('dwTime', ctypes.wintypes.DWORD)
        ]

NOSIZE = 1
NOMOVE = 2
TOPMOST = -1
NOT_TOPMOST = -2

prototype = WINFUNCTYPE(BOOL, HWND, POINTER(RECT))
paramflags = (1, 'hwnd'), (2, 'lprect')
GetWindowRect = prototype(('GetWindowRect', windll.user32), paramflags)
SetWindowPos = windll.user32.SetWindowPos

PLASTINPUTINFO = ctypes.POINTER(LASTINPUTINFO)
user32 = ctypes.windll.user32
GetLastInputInfo = user32.GetLastInputInfo
GetLastInputInfo.restype = ctypes.wintypes.BOOL
GetLastInputInfo.argtypes = [PLASTINPUTINFO]

kernel32 = ctypes.windll.kernel32
GetTickCount = kernel32.GetTickCount
Sleep = kernel32.Sleep


def wait_until_idle(idle_time=60):
    """
    Wait for the inactivity that waits for set time before initiating
    action set forth such as Shutdown or Sleep

    Parameters
    ----------
    idle_time : TYPE, optional
        DESCRIPTION. The default is 60.

    Returns
    -------
    None.

    """
    idle_time_ms = int(idle_time * 1000)
    liinfo = LASTINPUTINFO()
    liinfo.cbSize = ctypes.sizeof(liinfo)
    while True:
        GetLastInputInfo(ctypes.byref(liinfo))
        elapsed = GetTickCount() - liinfo.dwTime
        if elapsed >= idle_time_ms:
            break
        Sleep(idle_time_ms - elapsed or 1)


def wait_until_active(tol=5):
    """
    When the system is in inactive mode, this process signals the
    beginning od the user activity

    Parameters
    ----------
    tol : TYPE, optional
        DESCRIPTION. The default is 5.

    Returns
    -------
    None.

    """
    liinfo = LASTINPUTINFO()
    liinfo.cbSize = ctypes.sizeof(liinfo)
    lasttime = None
    delay = 1
    maxdelay = int(tol * 1000)
    while True:
        GetLastInputInfo(ctypes.byref(liinfo))
        if lasttime is None:
            lasttime = liinfo.dwTime
        if lasttime != liinfo.dwTime:
            break
        delay = min(2 * delay, maxdelay)
        Sleep(delay)


def test():
    print('Waiting for 10 seconds of no user input...')
    wait_until_idle(10)
    user32.MessageBeep(0)
    print('Ok, now do something')
    wait_until_active(1)
    user32.MessageBeep(0)
    print('Done')


def getProcessList():
    """
    gets the the top 7 windows process list for display

    Returns
    -------
    TYPE
        DESCRIPTION.

    """
    procs = defaultdict(int)
    for process in psutil.process_iter(['pid', 'name']):
        procs[process.info['name']] += 1
    # sort the dict to list the large first
    x = sorted(procs.items(), key=lambda x: x[1], reverse=True)
    # return the top 7 proceses with high instances
    return x[:7]


def timeRemaining(seconds: int):
    """
    Parameters
    ----------
    seconds : TYPE
        DESCRIPTION.

    Returns
    -------
    None.

    >>> timeRemaining(1000)
     (0, 16, 40)

    """
    mins, seconds = divmod(seconds, 60)
    hours, mins = divmod(mins, 60)
    return (hours, mins, seconds)


if __name__ == '__main__':
    speak = TextSpeak()
    speak.speak('Press a button to continue')

