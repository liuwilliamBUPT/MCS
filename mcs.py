# -*- coding: utf-8 -*-

"""
Module implementing MCS.
"""

import sys

import numpy as np

from scipy.fft import fft,  fftfreq
from scipy import signal
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QMainWindow, QApplication, QSizePolicy, QActionGroup, QDialog, QFileDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


from Ui_mcs import Ui_MCS
from Ui_data import Ui_Dialog
from signal_dlg import Signal


class MCS(QMainWindow, Ui_MCS):
    """
    Class documentation goes here.
    """
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget
        @type QWidget
        """
        super(MCS, self).__init__(parent)
        self.setupUi(self)

        # 添加 matplotlib 画布组件用于绘图
        self.canvas1 = TestCanvas(self.frame)
        self.horizontalLayout_15.addWidget(self.canvas1)

        self.canvas2 = TestCanvas(self.frame)
        self.horizontalLayout_14.addWidget(self.canvas2)

        # 添加 matplotlib 导航工具栏用于操作图像。
        self.toolbar1 = NavigationToolbar(self.canvas1, self)
        self.toolbar1.hide()
        self.toolbar2 = NavigationToolbar(self.canvas2, self)
        self.toolbar2.hide()

        # 
        self.scrollbar_value = 1000
        self.signal_wave = None
        self.amplitude = 2.5, 2.5
        self.data = None
        self.external_flag = False

        # 将菜单栏中的 signal 选项改为单选。
        self.menuGroupSingal = QActionGroup(self.menuSignal)
        self.menuGroupSingal.addAction(self.actionSquare)
        self.menuGroupSingal.addAction(self.actionTriangle)
        self.menuGroupSingal.addAction(self.actionSin)
        self.menuGroupSingal.setExclusive(True)
        
    def zoom(self):
        """
        缩放图像
        """
        self.toolbar1.zoom()
        self.toolbar2.zoom()

    def pan(self):
        """
        拖动图像
        """
        self.toolbar1.pan()
        self.toolbar2.pan()

    def home(self):
        """
        还原图像
        """
        self.toolbar1.home()
        
    def save(self):
        """
        保持图像
        """
        self.toolbar1.save_figure()
        self.toolbar2.save_figure()
        
    @pyqtSlot()
    def on_pushButton_clicked(self):
        """
        pushButton 被点击时，绘制图像。
        """
        self.plot()
    
    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        """
        pushButton2 被点击时，允许缩放图像。
        """
        self.zoom()
    
    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        """
        pushButton3 被点击时，允许拖动图像。
        """
        self.pan()
    
    def generate_signal(self, freq, sample_freq):
        """
        信号生成
        """
        phase = 2 * np.pi * freq * sample_freq
        nosie = np.random.randn(*np.shape(sample_freq))/10
        if self.signal_wave == 3:
            return self.amplitude[0] * np.sin(phase) + nosie + self.amplitude[1]
        elif self.signal_wave == 2:
            return self.amplitude[0] * signal.sawtooth(phase,  0.5) + nosie + self.amplitude[1]
        else:
            return self.amplitude[0] * signal.square(phase) + nosie + self.amplitude[1]
    
    def plot(self):
        """
        绘制图像
        """
        # a = self.canvas1.update_figure()
        # x=np.linspace(0, 1, 5000)
        # y=7*np.sin(2*np.pi*180*x)
        # yy=fft(y)                     #快速傅里叶变换
        # #yreal = yy.real               # 获取实数部分
        # #yimag = yy.imag               # 获取虚数部分

        # #yf=abs(yy)                # 取绝对值
        # yf1=abs(yy)/len(x)           #归一化处理
        # yf2 = yf1[range(int(len(x)/2))]  #由于对称性，只取一半区间

        # xf = np.arange(len(y))        # 频率
        # #xf1 = xf
        # xf2 = xf[range(int(len(x)/2))]  #取一半区间
        # self.canvas1.draw_(x[0:50], y[0:50])
        # self.canvas2.draw_(xf2,yf2)
        if self.external_flag:
            x, y, N, f_s = self.resume_data_from_file()
            self.horizontalScrollBar.setValue(int(N/100))
            self.external_flag = False
        else:
            N = int(self.scrollbar_value/10)
            f_s = 80
            x=np.linspace(0, 5, N, endpoint=False)
            #k=np.arange(1,99)
            #k=2*k-1
            # y=np.zeros_like(x)
            freq = signal_dlg.freq
            sample_freq = x
            y = self.generate_signal(freq, sample_freq)
            self.generate_export_data(x, y, N, f_s)
            #        y = signal.square(2 * np.pi *5 * x)
            # for i in range(len(x)):
            #     y[i]=(4/np.pi)*np.sum(np.sin(k*x[i])/k)
        xf2 = np.arange(len(y))
        # y = signal.square(2 * np.pi * 5 * t)
        yf2 = fft(y)
        f = fftfreq(N, 1.0/f_s)
        mask = np.where(f >= 0)
        xf2 = f[mask]
        yf2 = abs(yf2[mask]/N)
        
        self.lineEdit.setText(str(np.max(yf2)))
        self.canvas1.draw_(x, y)
        self.canvas2.draw_(xf2,yf2)
        
    def generate_export_data(self,x, y, N, f_s):
        self.data = f"{N}\n{f_s}\n" +"\n".join([ str(i) for i in zip(x, y) ])
        
    def resume_data_from_file(self):
        data = self.data.split("\n")
        list_data = [ eval(i) for i in data[2:] ]
        N =int(data[0])
        f_s = int(data[1])
        x, y =map(list, zip(*list_data))
        x = np.array(x)
        y = np.array(y)
        return x, y, N, f_s
    
    @pyqtSlot()
    def on_pushButton_4_clicked(self):
        """
        Slot documentation goes here.
        """
        self.home()
    
    @pyqtSlot()
    def on_pushButton_5_clicked(self):
        """
        Slot documentation goes here.
        """
        self.zoom()
    
    @pyqtSlot()
    def on_pushButton_6_clicked(self):
        """
        Slot documentation goes here.
        """
        self.pan()
    
    @pyqtSlot()
    def on_pushButton_7_clicked(self):
        """
        Slot documentation goes here.
        """
        self.save()
    
    @pyqtSlot()
    def on_action_Exit_triggered(self):
        """
        Slot documentation goes here.
        """
        self.close()

    @pyqtSlot()
    def on_actionSave_As_triggered(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSlot()
    def on_pushButton_8_clicked(self):
        """
        Slot documentation goes here.
        """
        self.toolbar2.home()
    
    @pyqtSlot(int)
    def on_horizontalScrollBar_valueChanged(self, value):
        """
        Slot documentation goes here.
        
        @param value DESCRIPTION
        @type int
        """
        self.lineEdit_4.setText(str(value/10))
        self.scrollbar_value = value * 1000
    
    @pyqtSlot(str)
    def on_lineEdit_4_textChanged(self, p0):
        """
        Slot documentation goes here.
        
        @param p0 DESCRIPTION
        @type str
        """
        if p0:
            # 错误检查 2.0.多输入的0不允许输入或者怎么处理。
            self.horizontalScrollBar.setValue(int(float(p0)*10))
        else:
            # bug: 初始化时候的1不是1
            self.horizontalScrollBar.setValue(1)
    
    @pyqtSlot(bool)
    def on_actionSquare_triggered(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        self.signal_wave = 1 if checked else None
    
    @pyqtSlot(bool)
    def on_actionTriangle_triggered(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        self.signal_wave = 2 if checked else None
    
    @pyqtSlot(bool)
    def on_actionSin_triggered(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        self.signal_wave = 3 if checked else None
    
    @pyqtSlot(bool)
    def on_radioButton_2_toggled(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        if checked:
            self.amplitude = 5, 5
    
    @pyqtSlot(bool)
    def on_radioButton_4_toggled(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        if checked:
            self.amplitude = 10, 0
    
    @pyqtSlot(bool)
    def on_radioButton_3_toggled(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        if checked:
            self.amplitude = 5, 0 
    
    @pyqtSlot(bool)
    def on_radioButton_toggled(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        if checked:
            self.amplitude = 2.5, 2.5 
    
    @pyqtSlot()
    def on_pushButton_9_clicked(self):
        """
        Slot documentation goes here.
        """
        if self.data:
            dlg_ui.textEdit.setText(self.data)
        else:
            dlg_ui.textEdit.setText("请先采集数据或导入数据。")
        Dialog.show()
    
    @pyqtSlot()
    def on_actionExport_Data_triggered(self):
        """
        Slot documentation goes here.
        """
        fileName, _ = QFileDialog.getSaveFileName(self, "Export Data")
        # todo: z检查是否有数据，没有就弹窗
        if fileName:
            file = open(fileName, 'w')
            text = self.data
            file.write(text)
            file.close()
    
    @pyqtSlot()
    def on_actionExport_Data_As_triggered(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        raise NotImplementedError
    
    @pyqtSlot()
    def on_actionSave_triggered(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        self.save()
    
    @pyqtSlot()
    def on_actionOpen_triggered(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        fileName, _ = QFileDialog.getOpenFileName(self, "Open File")
        if fileName:
            file = open(fileName,  "r")
            self.data = file.read()
            # 抛出错误？
            self.external_flag = True
            file.close()
    
    @pyqtSlot()
    def on_pushButton_10_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        signal_dlg.show()
            
        
class Canvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        
    def compute_initial_figure(self):
        pass      
        
class TestCanvas(Canvas):
    def __init__(self, *args, **kwargs):
        Canvas.__init__(self, *args, **kwargs)
        # timer = QTimer(self)
        # timer.timeout.connect(self.update_figure)
        # timer.start(1000)

    def compute_initial_figure(self):
        self.axes.plot([i for i in range(50)], [i for i in range(50)], 'r')

    def draw_(self, a, b):
        self.compute_initial_figure()
        self.axes.clear()
        self.axes.plot(a, b)
        self.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWindow = MCS()
    mainWindow.show()
    Dialog = QDialog()
    dlg_ui = Ui_Dialog()
    dlg_ui.setupUi(Dialog)
    signal_dlg = Signal()
    sys.exit(app.exec_())