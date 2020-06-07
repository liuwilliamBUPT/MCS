# -*- coding: utf-8 -*-

"""
Module implementing Signal.
"""

from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import QDialog

from Ui_signal import Ui_Dialog


class Signal(QDialog, Ui_Dialog):
    """
    Class documentation goes here.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget
        @type QWidget
        """
        super(Signal, self).__init__(parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)
        
        self.freq = 100
    
    @pyqtSlot(bool)
    def on_radioButton_toggled(self, checked):
        """
        设置频率 100 Hz
        
        @param checked DESCRIPTION
        @type self, bool
        """
        if checked:
            self.freq = 100
    
    @pyqtSlot(bool)
    def on_radioButton_2_toggled(self, checked):
        """
        设置频率 500 Hz
        
        @param checked DESCRIPTION
        @type self, bool
        """
        if checked:
            self.freq = 500
    
    @pyqtSlot(bool)
    def on_radioButton_3_toggled(self, checked):
        """
        设置频率 2000 Hz
        
        @param checked DESCRIPTION
        @type self, bool
        """
        if checked:
            self.freq = 2000
