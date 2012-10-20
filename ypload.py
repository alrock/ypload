#!/usr/bin/python
import sys; sys.path.append('requests.egg')
import os
import ydisk
import mimetypes
import webbrowser

YD_APP_ID = 'cb76e6135dc34947bcf7620e1ab62e54'
YD_APP_SECRET = 'e4dba0141d734e1d89a5333c26a44f46'
KEY_FILE = os.path.expanduser('~/.ypload-key')
key = ydisk.getKey(YD_APP_ID, YD_APP_SECRET, KEY_FILE)
api = ydisk.DiskAPI(key)
api.mkdir('/JustShared')
api.mkdir('/JustShared/screenshots')


from Foundation import NSObject, NSLog
from AppKit import NSApplication, NSApp, NSWorkspace
from Cocoa import (NSEvent,
                   NSKeyDown, NSKeyDownMask, NSKeyUp, NSKeyUpMask,
                   NSLeftMouseUp, NSLeftMouseDown, NSLeftMouseUpMask, NSLeftMouseDownMask,
                   NSRightMouseUp, NSRightMouseDown, NSRightMouseUpMask, NSRightMouseDownMask,
                   NSMouseMoved, NSMouseMovedMask,
                   NSScrollWheel, NSScrollWheelMask,
                   NSAlternateKeyMask, NSCommandKeyMask, NSControlKeyMask)
from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
from PyObjCTools import AppHelper

def screenshot():
    global api
    import tempfile, datetime
    handle, fname = tempfile.mkstemp(suffix='.png', prefix=datetime.datetime.now().isoformat())
    os.close(handle)
    os.system('screencapture -d -i ' + fname + '>/dev/null 2>&1')

    if os.path.isfile(fname) and os.path.getsize(fname) > 15:
        newname = '/JustShared/screenshots/' + os.path.basename(fname)
        try:
            tp, enc = mimetypes.guess_type(fname)
            if not tp:
                tp = 'application/facepalm'
            api.put(newname, open(fname, 'r').read(), tp=tp)
            durl = api.publish(newname)
            os.system('echo ' + durl + '| pbcopy')
            webbrowser.open(durl)
        except Exception, e:
            sys.stderr.write('Something wrong with %s\n%s\n' % (fname, e))
    else:
        sys.stderr.write('No such file %s\n' % fname)
    os.unlink(fname)

class SniffCocoa:
    def __init__(self):
        pass

    def createAppDelegate (self) :
        sc = self
        class AppDelegate(NSObject):
            def applicationDidFinishLaunching_(self, notification):
                mask = (NSKeyDownMask
                        | NSKeyUpMask)
                NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(mask, sc.handler)
        return AppDelegate

    def run(self):
        NSApplication.sharedApplication()
        delegate = self.createAppDelegate().alloc().init()
        NSApp().setDelegate_(delegate)
        self.workspace = NSWorkspace.sharedWorkspace()
        AppHelper.runEventLoop()

    def cancel(self):
        AppHelper.stopEventLoop()

    def handler(self, event):
        try:
            if event.type() == NSKeyDown:
                flags = event.modifierFlags()
                if (flags & NSCommandKeyMask) and \
                   event.keyCode() == 23 and \
                   event.charactersIgnoringModifiers() == u'%':
                   screenshot()
        except (Exception, KeyboardInterrupt) as e:
            print e
            AppHelper.stopEventLoop()

if __name__ == '__main__':
    sc = SniffCocoa()
    sc.run()
