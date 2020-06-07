# -*- coding: utf-8 -*-

"""
Module implementing MCS.
"""

import sys

import numpy as np

from scipy.fft import fft, fftfreq
from scipy import signal
from PyQt5.QtCore import pyqtSlot, QRegExp
from PyQt5.QtWidgets import (QMainWindow, QApplication, QSizePolicy,
                             QActionGroup, QDialog, QFileDialog, QMessageBox)
from PyQt5.QtGui import QRegExpValidator
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import (NavigationToolbar2QT
                                                as NavigationToolbar)
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
        self.canvas1 = Canvas(self.frame,
                              xlabel="Time(s)", title="Sampled waveform")
        self.canvas1.get_default_filename = lambda: 'Sampled waveform.png'

        self.horizontalLayout_15.addWidget(self.canvas1)

        self.canvas2 = Canvas(self.frame,
                              xlabel="Frequency(Hz)",
                              title="FFT of Sampled waveform")
        self.canvas2.get_default_filename = lambda: ('FFT of Sampled '
                                                     'waveform.png')
        self.horizontalLayout_14.addWidget(self.canvas2)

        # 添加 matplotlib 导航工具栏用于操作图像。
        self.toolbar1 = NavigationToolbar(self.canvas1, self)
        self.toolbar1.hide()
        self.toolbar2 = NavigationToolbar(self.canvas2, self)
        self.toolbar2.hide()

        # 为文本框添加 validator
        regex = QRegExp(r'^100(\.0)?$|^[1-9]?[0-9](\.[0-9])?$')
        self.lineEdit_4.setValidator(QRegExpValidator(regex, self))

        # 一些初始化变量值
        self.scrollbar_value = 1
        self.signal_wave = None
        self.amplitude = 2.5, 2.5
        self.data = None
        self.external_flag = False
        self.sample_freq_value = 0.1

        # 将菜单栏中的 signal 选项改为单选。
        self.menuGroupSingal = QActionGroup(self.menuSignal)
        self.menuGroupSingal.addAction(self.actionSquare)
        self.menuGroupSingal.addAction(self.actionTriangle)
        self.menuGroupSingal.addAction(self.actionSin)
        self.menuGroupSingal.setExclusive(True)

    def zoom(self):
        """缩放图像。"""
        self.toolbar1.zoom()
        self.toolbar2.zoom()

    def pan(self):
        """拖动图像。"""
        self.toolbar1.pan()
        self.toolbar2.pan()

    def save(self):
        """保存图像。"""
        self.toolbar1.save_figure()
        self.toolbar2.save_figure()

    def generate_signal(self, freq, sample_point):
        """根据传入参数及预设，生成对应信号。"""
        # 函数的相位
        phase = 2 * np.pi * freq * sample_point

        # 模拟产生噪音信号
        noise = np.random.randn(*np.shape(sample_point)) / 50
        # noise = 0

        if self.signal_wave == 3:
            # 返回正弦波
            return self.amplitude[0] * np.sin(phase) + noise + self.amplitude[1]
        elif self.signal_wave == 2:
            # 返回三角波
            return (self.amplitude[0] * signal.sawtooth(phase, 0.5) + noise
                    + self.amplitude[1])
        else:
            # 返回方波
            return (self.amplitude[0] * signal.square(phase) + noise +
                    self.amplitude[1])

    def plot(self):
        """绘制图像。"""
        # 采样时间
        T = 1
        if self.external_flag:
            x, y, N, f_s = self.resume_data_from_file()
            self.horizontalScrollBar.setValue(int(N / 10))
            self.external_flag = False
        else:
            # f_s 范围 0.1k~400K 而 scrollbar_value 范围 1~1000
            f_s = int(self.scrollbar_value * 10)

            # 采样点数 N = T * f_s
            N = T * f_s

            # 生成采样点集，范围从 0-T 均分 N个点。
            x = np.linspace(0, T, N, endpoint=False)

            # 设置产生信号的频率
            freq = signal_dlg.freq

            # 采样点
            sample_point = x

            # 生成指定信号
            y = self.generate_signal(freq, sample_point)

            # 生成用于导出的数据
            self.generate_export_data(x, y, N, f_s)

        # FFT 变换
        yf2 = fft(y)
        f = fftfreq(N, 1.0 / f_s)
        mask = np.where(f >= 0)
        xf2 = f[mask]
        yf2 = abs(yf2[mask] / N)

        self.lineEdit.setText(f"{np.max(y) - np.mean(y):.4f}")

        y_ac = y - np.mean(y)
        count = ((y_ac[:-1] * y_ac[1:]) < 0).sum()
        count = count if count % 2 == 0 else count + 1
        self.lineEdit_3.setText(f"{2*T/count:.4f}")
        # self.lineEdit_3.setText(f"{((y_ac[:-1] * y_ac[1:]) < 0).sum():.5f}")
        self.lineEdit_2.setText(f"{count/(2*T):.2f}")
        self.canvas1.plot(x, y, "Time(s)", "Amplitude(V)", "Sampled waveform")
        self.canvas2.plot(xf2, yf2, "Frequency(Hz)", "Amplitude(V)",
                          "FFT of Sampled waveform")

    def generate_export_data(self, x, y, N, f_s):
        """生成用于输出的数据。"""
        self.data = f"{N}\n{f_s}\n" + "\n".join([str(i) for i in zip(x, y)])

    def resume_data_from_file(self):
        """从文件中恢复数据。"""
        data = self.data.split("\n")
        list_data = [eval(i) for i in data[2:]]
        N = int(data[0])
        f_s = int(data[1])
        x, y = map(list, zip(*list_data))
        x = np.array(x)
        y = np.array(y)
        return x, y, N, f_s

    @pyqtSlot()
    def on_pushButton_clicked(self):
        """pushButton 被点击时，绘制图像。"""
        self.plot()

    @pyqtSlot()
    def on_pushButton_2_clicked(self):
        """pushButton2 被点击时，允许缩放图像。"""
        self.zoom()

    @pyqtSlot()
    def on_pushButton_3_clicked(self):
        """pushButton3 被点击时，允许拖动图像。"""
        self.pan()

    @pyqtSlot()
    def on_pushButton_4_clicked(self):
        """
        点击 pushButton_4（还原采样波形） 触发采样波形恢复。
        """
        self.toolbar1.home()

    @pyqtSlot()
    def on_pushButton_5_clicked(self):
        """
        点击 pushButton_5（缩放） 允许缩放波形。
        """
        self.zoom()

    @pyqtSlot()
    def on_pushButton_6_clicked(self):
        """
        点击 pushButton_6（拖动） 允许拖动波形。
        """
        self.pan()

    @pyqtSlot()
    def on_pushButton_7_clicked(self):
        """
        点击 pushButton_7（保存） 依次弹出保存图形窗口。
        """
        self.save()

    @pyqtSlot()
    def on_pushButton_8_clicked(self):
        """
        点击 pushButton_8（还原FFT） 触发FFT波形恢复
        """
        self.toolbar2.home()

    @pyqtSlot()
    def on_pushButton_9_clicked(self):
        """
        点击 pushButton_9（采样数据），从 self.data 中读取数据，并写入弹出对话框中的
        文本框；如果 self.data 为空，则向文本框中写入报错信息。
        """
        if self.data:
            dlg_ui.textEdit.setText(self.data)
        else:
            dlg_ui.textEdit.setText("请先采集数据或导入数据。")
        Dialog.show()

    @pyqtSlot()
    def on_pushButton_10_clicked(self):
        """
        点击 pushButton_10（频率设置） 弹出频率设置对话框。
        """
        signal_dlg.show()

    @pyqtSlot()
    def on_action_Exit_triggered(self):
        """
        点击 File-Exit 退出程序。
        """
        self.close()

    @pyqtSlot(int)
    def on_horizontalScrollBar_valueChanged(self, value):
        """
        将水平滑动控件与 lineEdit_4 绑定，当滑条数值改变时，对应改变文本框中的数值。

        @param value DESCRIPTION
        @type self, int
        """
        # ScrollBar 范围为 1-1000 所以将从其获得的值除以十倍置于 lineEdit_4。
        self.lineEdit_4.setText(str(value / 10))
        self.scrollbar_value = value

    @pyqtSlot()
    def on_lineEdit_4_editingFinished(self):
        """
        当 lineEdit_4 完成编辑，即光标焦点移开或者是敲击 Enter 或 Return 后，
        该方法生效。
        """
        if self.lineEdit_4.text():
            # ScrollBar 范围为 1-1000 所以将从文本框中获得的值乘十设置为滑块值。
            value = int(float(self.lineEdit_4.text()) * 10)
            self.horizontalScrollBar.setValue(value)
        else:
            self.horizontalScrollBar.setValue(0.1)

    @pyqtSlot(bool)
    def on_actionSquare_triggered(self, checked):
        """
        点击 View-Signal-Square 时，将类属性 signal_wave 设置为1，即表示方波。
        
        @param checked DESCRIPTION
        @type self, bool
        """
        self.signal_wave = 1 if checked else None

    @pyqtSlot(bool)
    def on_actionTriangle_triggered(self, checked):
        """
        点击 View-Signal-Triangle 时，将类属性 signal_wave 设置为2，即表示三角波。
        
        @param checked DESCRIPTION
        @type self, bool
        """
        self.signal_wave = 2 if checked else None

    @pyqtSlot(bool)
    def on_actionSin_triggered(self, checked):
        """
        点击 View-Signal-Sine 时，将类属性 signal_wave 设置为3，即表示正弦波。
        
        @param checked DESCRIPTION
        @type self, bool
        """
        self.signal_wave = 3 if checked else None

    # 单选框代码，即选则输入电压。
    @pyqtSlot(bool)
    def on_radioButton_toggled(self, checked):
        """
        选中 radioButton 时，将类属性 amplitude 设置为 (2.5, 2.5)，
        即输入电压为 0~5V。

        @param checked DESCRIPTION
        @type self, bool
        """
        if checked:
            self.amplitude = 2.5, 2.5

    @pyqtSlot(bool)
    def on_radioButton_2_toggled(self, checked):
        """
        选中 radioButton_2 时，将类属性 amplitude 设置为 (5, 5)，
        即输入电压为 0~10V。
        
        @param checked DESCRIPTION
        @type self, bool
        """
        if checked:
            self.amplitude = 5, 5

    @pyqtSlot(bool)
    def on_radioButton_3_toggled(self, checked):
        """
        选中 radioButton_3 时，将类属性 amplitude 设置为 (5, 0)，
        即输入电压为 -5~+5V。

        @param checked DESCRIPTION
        @type self, bool
        """
        if checked:
            self.amplitude = 5, 0

    @pyqtSlot(bool)
    def on_radioButton_4_toggled(self, checked):
        """
        选中 radioButton_4 时，将类属性 amplitude 设置为 (10, 0)，
        即输入电压为 -10~+10V。
        
        @param checked DESCRIPTION
        @type self, bool
        """
        if checked:
            self.amplitude = 10, 0

    @pyqtSlot()
    def on_actionExport_Data_triggered(self):
        """
         点击 File—Export Data，将储存在 self.data中的数据导出到文件。
        """
        # todo: 导出到 json
        if self.data:
            fileName, _ = QFileDialog.getSaveFileName(self, "Export Data")
            if fileName:
                file = open(fileName, 'w')
                text = self.data
                file.write(text)
                file.close()
        else:
            # 如果没有采集数据，则弹出警告。
            reply = QMessageBox.warning(self, "警告", "请先采集数据！",
                                        QMessageBox.Yes | QMessageBox.No,
                                        QMessageBox.Yes)

    @pyqtSlot()
    def on_actionSave_triggered(self):
        """
        Slot documentation goes here.
        """
        self.save()

    @pyqtSlot()
    def on_actionOpen_triggered(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        fileName, _ = QFileDialog.getOpenFileName(self, "Open File")
        if fileName:
            file = open(fileName, "r")
            self.data = file.read()
            # 抛出错误？
            self.external_flag = True
            file.close()


class Canvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100,
                 xlabel="Time(s)", title="Sampled waveform"):
        fig = Figure(figsize=(width, height), dpi=dpi)
        fig.set_tight_layout(True)
        self.axes = fig.add_subplot(111)
        self.axes.set_ylabel("Amplitude(V)")
        self.axes.set_xlabel(xlabel)
        self.axes.set_title(title)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass

    def plot(self, x, y, xlabel, ylabel, title):
        self.axes.clear()
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel(ylabel)
        self.axes.set_title(title)
        self.axes.plot(x, y)
        self.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # 启动主窗口
    mainWindow = MCS()
    mainWindow.show()
    # 加载数据窗口
    Dialog = QDialog()
    dlg_ui = Ui_Dialog()
    dlg_ui.setupUi(Dialog)
    # 加载波形频率窗口
    signal_dlg = Signal()
    sys.exit(app.exec_())
