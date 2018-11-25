# -*- coding: utf-8 -*-
"""
GUI for APPA
@author: Dmitriy Emelin
"""

import os
import sys
from pkgutil import iter_modules


def main():
    
    #Check OS
    sys.platform = 'linux'
    if 'win' in sys.platform:
        print 'This OS does\'t support'
        sys.exit()
    elif 'linux' in sys.platform:
        pass

    # Check version of Qt and import it
    qt_list = []
    for obj, name, iswork in iter_modules():
        if iswork and 'pyqt' in name.lower():
            qt_list.append(name)
    if qt_list:
        last_qt_version = max([ int(qt.lower().split('pyqt')[-1])
                                                           for qt in qt_list ])
        if last_qt_version == 4:
    
            from PyQt4 import Qt, QtGui, QtCore
            app = QtGui.QApplication(sys.argv)

        elif last_qt_version == 5:

            from PyQt5 import Qt, QtGui, QtCore, QtWidgets
            app = QtWidgets.QApplication(sys.argv)
            
        else:
            print 'Version PyQt is old'
            sys.exit()
    else:
        print 'PyQt does\'t install'
        sys.exit()
    
    
    #print last_qt_version
    import gui.main_frame as mf  # GUI

    ex = mf.MainFrame()
    
    #try:
    #    sys.exit(app.exec_())
    #except SystemExit:
    #    import signal
    #    os.kill(os.getpid(), signal.SIGQUIT)
    #    pass


if __name__ == '__main__':
    main()
