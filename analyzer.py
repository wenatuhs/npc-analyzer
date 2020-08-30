# !/usr/bin/python
# -*- coding: utf-8 -*-

"""
NPC Reflectivity Measurement Data Analysis Program

In this code, we built a simple image analysis gui program.

author: Zhe Zhang
email: wenatuhs@gmail.com
last edited: August 2014
"""

import os
import sys
import traceback
import warnings
import csv
from PyQt4 import QtGui, QtCore
from skimage import io, filter, transform
import numpy as np
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.ticker import AutoMinorLocator


__version__ = '1.4'
_formats = [".bmp", ".jpg", ".png"]
_cal_format = ".csv"
# _filter = {0: [0], 1: [0], 2: [1, 2], 3: [1, 2]}
_filter = {0: [0], 45: [1], 90: [2], 135: [3]}
_home = QtCore.QDir.currentPath() # "/Users/wena/"
_size = QtCore.QSize(640, 480)+QtCore.QSize(4, 4)
_minsize = QtCore.QSize(640, 480)+QtCore.QSize(4, 4)
_zoom_level = [1/5.0, 1/4.0, 1/3.0, 1/2.0, 2/3.0, 4/5.0, 1.0, \
        5/4.0, 3/2.0, 2.0, 3.0, 4.0, 5.0]


class Main(QtGui.QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
    
    def initUI(self):
        # Set transparent background
        p = self.palette()
        color = p.color(QtGui.QPalette.Background)
        p.setColor(self.backgroundRole(), \
                   QtGui.QColor(color.red(), color.green(), color.blue(), 0xff))
        self.setPalette(p)
        # Set main widget
        self.image_display = ImageDisplay(self)
        self.setCentralWidget(self.image_display)
        # Set menus
        self.create_actions()
        self.create_menus()
        # Set other stuff
        self.printer = QtGui.QPrinter()
        
        self.setWindowTitle('NPC Analyzer '+__version__)
        self.show()
        self.center()
    
    def closeEvent(self, e):
        self.image_display.plot.setVisible(False)
        super().closeEvent(e)
    
    def center(self):
        qr = self.frameGeometry()
        qr.moveCenter(QtGui.QDesktopWidget().availableGeometry().center())
        self.move(qr.topLeft())
    
    def print_(self):
        dialog = QtGui.QPrintDialog(self.printer, self)
        if dialog.exec_():
            painter = QtGui.QPainter(self.printer)
            image = self.image_display.lbl
            # self.printer.setPaperSize(QtCore.QSizeF(image.size()),
            #         QtGui.QPrinter.DevicePixel)
            rect = painter.window()
            rect_size = rect.size()
            rect_size.scale(image.size(), QtCore.Qt.KeepAspectRatioByExpanding)
            rect.setSize(rect_size)
            painter.setWindow(rect)
            image.render(painter)
            painter.end()
    
    def about(self):
        QtGui.QMessageBox.about(self, "About Image Viewer",
                "<p>The <b>Image Viewer</b> example shows how to combine "
                "QLabel and QScrollArea to display an image. QLabel is "
                "typically used for displaying text, but it can also display "
                "an image. QScrollArea provides a scrolling view around "
                "another widget. If the child widget exceeds the size of the "
                "frame, QScrollArea automatically provides scroll bars.</p>"
                "<p>The example demonstrates how QLabel's ability to scale "
                "its contents (QLabel.scaledContents), and QScrollArea's "
                "ability to automatically resize its contents "
                "(QScrollArea.widgetResizable), can be used to implement "
                "zooming and scaling features.</p>"
                "<p>In addition the example shows how to use QPainter to "
                "print an image.</p>")
    
    def create_actions(self):
        self.open_act = QtGui.QAction("&Open...", self,
                shortcut="Ctrl+O",
                triggered=self.image_display.open_file,
                shortcutContext=QtCore.Qt.ApplicationShortcut)
        
        self.choose_dir_act = QtGui.QAction("Choose &Directory...", self,
                shortcut="Ctrl+Shift+O",
                triggered=self.image_display.choose_dir,
                shortcutContext=QtCore.Qt.ApplicationShortcut)
        
        self.print_act = QtGui.QAction("&Print...", self,
                shortcut="Ctrl+P",
                enabled=False, triggered=self.print_,
                shortcutContext=QtCore.Qt.ApplicationShortcut)
        
        self.exit_act = QtGui.QAction("Q&uit NPC Analyzer", self,
                shortcut="Ctrl+Q",
                triggered=self.close,
                shortcutContext=QtCore.Qt.ApplicationShortcut)
        
        self.analyze_act = QtGui.QAction("&Run Analyze", self,
                shortcut="Ctrl+R",
                triggered=self.image_display.do_analyze_act,
                shortcutContext=QtCore.Qt.ApplicationShortcut)
        
        self.sigma_up_act = QtGui.QAction("Edge Sigma &Up (+0.1)", self,
                shortcut="Ctrl+Right",
                enabled=True, triggered=self.image_display.sigma_up,
                shortcutContext=QtCore.Qt.ApplicationShortcut)
        
        self.sigma_down_act = QtGui.QAction("Edge Sigma &Down (-0.1)", self,
                shortcut="Ctrl+Left",
                enabled=False, triggered=self.image_display.sigma_down,
                shortcutContext=QtCore.Qt.ApplicationShortcut)
        
        self.sigma_line_up_act = QtGui.QAction("Line Sigma &Up (+0.1)", self,
                shortcut="Ctrl+Up",
                enabled=True, triggered=self.image_display.sigma_line_up,
                shortcutContext=QtCore.Qt.ApplicationShortcut)
        
        self.sigma_line_down_act = QtGui.QAction("Line Sigma &Down (-0.1)", self,
                shortcut="Ctrl+Down",
                enabled=False, triggered=self.image_display.sigma_line_down,
                shortcutContext=QtCore.Qt.ApplicationShortcut)
        
        self.add_act = QtGui.QAction("&Add Data Point", self,
                shortcut="Ctrl+A",
                enabled=False, triggered=self.image_display.add_act,
                shortcutContext=QtCore.Qt.ApplicationShortcut)
        
        self.restore_act = QtGui.QAction("&Restore Selected Data Point", self,
                shortcut="Ctrl+L",
                enabled=False, triggered=self.image_display.restore_act,
                shortcutContext=QtCore.Qt.ApplicationShortcut)
        
        self.replace_act = QtGui.QAction("Replac&e Selected Data Point", self,
                shortcut="Ctrl+X",
                enabled=False, triggered=self.image_display.replace_act,
                shortcutContext=QtCore.Qt.ApplicationShortcut)
        
        self.del_act = QtGui.QAction("&Delete Selected Data Point(s)", self,
                shortcut="Ctrl+D",
                enabled=False, triggered=self.image_display.del_act,
                shortcutContext=QtCore.Qt.ApplicationShortcut)
        
        self.export_act = QtGui.QAction("&Export All Data Points", self,
                shortcut="Ctrl+E",
                enabled=False, triggered=self.image_display.export_act,
                shortcutContext=QtCore.Qt.ApplicationShortcut)
        
        self.preview_act = QtGui.QAction("&Show Preview", self,
                shortcut="Ctrl+S",
                triggered=self.image_display.preview_act,
                shortcutContext=QtCore.Qt.ApplicationShortcut)
        
        self.preview_always_on_top_act = QtGui.QAction("&Preview Always on Top", self,
                shortcut="Ctrl+Shift+P",
                checkable=True,
                triggered=self.image_display.preview_always_on_top,
                shortcutContext=QtCore.Qt.ApplicationShortcut)
        self.preview_always_on_top_act.setChecked(True)
        
        self.fit_to_image_act = QtGui.QAction("&Fit to Image", self,
                shortcut="Ctrl+F",
                enabled=False, triggered=self.image_display.fit_to_image,
                shortcutContext=QtCore.Qt.ApplicationShortcut)
        
        self.auto_fit_act = QtGui.QAction("&Auto Fit", self,
                shortcut="Ctrl+Shift+F",
                checkable=True,
                shortcutContext=QtCore.Qt.ApplicationShortcut)
        self.auto_fit_act.setChecked(False)
        
        self.zoomin_act = QtGui.QAction("Zoom &In (25%)", self,
                shortcut="Ctrl+=",
                enabled=False, triggered=self.image_display.zoomin,
                shortcutContext=QtCore.Qt.ApplicationShortcut)
        
        self.zoomout_act = QtGui.QAction("Zoom &Out (25%)", self,
                shortcut="Ctrl+-",
                enabled=False, triggered=self.image_display.zoomout,
                shortcutContext=QtCore.Qt.ApplicationShortcut)
        
        self.normalsize_act = QtGui.QAction("&Normal Size", self,
                shortcut="Ctrl+0",
                enabled=False, triggered=self.image_display.normalsize,
                shortcutContext=QtCore.Qt.ApplicationShortcut)
        
        self.show_edges_act = QtGui.QAction("Show &Edges", self,
                checkable=True, triggered=self.image_display.show_paints)
        self.show_edges_act.setChecked(True)
        
        self.show_lines_act = QtGui.QAction("Show &Lines", self,
                checkable=True, triggered=self.image_display.show_paints)
        self.show_lines_act.setChecked(True)
        
        self.show_squares_act = QtGui.QAction("Show &Squares", self,
                checkable=True, triggered=self.image_display.show_paints)
        self.show_squares_act.setChecked(True)
        
        self.show_stat_act = QtGui.QAction("Show S&tat", self,
                checkable=True, triggered=self.image_display.show_others)
        self.show_stat_act.setChecked(True)
        
        self.show_info_act = QtGui.QAction("Show &Info", self,
                checkable=True, triggered=self.image_display.show_others)
        self.show_info_act.setChecked(True)
        
        self.tool_tip_act = QtGui.QAction("Show Tool &Tips", self,
                shortcut="Ctrl+Shift+T",
                checkable=True,
                triggered=self.image_display.show_tool_tips,
                shortcutContext=QtCore.Qt.ApplicationShortcut)
        self.tool_tip_act.setChecked(False)
        
        self.keep_drawing_act = QtGui.QAction(
                "&Keep Analysis Result while Dragging", self,
                shortcut="Ctrl+Shift+K",
                checkable=True,
                shortcutContext=QtCore.Qt.ApplicationShortcut)
        self.keep_drawing_act.setChecked(True)
        
        self.about_act = QtGui.QAction("&About", self,
                triggered=self.about)
    
    def create_menus(self):
        self.file_menu = QtGui.QMenu("&File", self)
        self.file_menu.addAction(self.open_act)
        self.file_menu.addAction(self.choose_dir_act)
        self.file_menu.addAction(self.print_act)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_act)
        
        self.view_menu = QtGui.QMenu("&View", self)
        self.view_menu.addAction(self.fit_to_image_act)
        self.view_menu.addAction(self.auto_fit_act)
        self.view_menu.addSeparator()
        self.view_menu.addAction(self.zoomin_act)
        self.view_menu.addAction(self.zoomout_act)
        self.view_menu.addAction(self.normalsize_act)
        self.view_menu.addSeparator()
        self.view_menu.addAction(self.show_lines_act)
        self.view_menu.addAction(self.show_edges_act)
        self.view_menu.addAction(self.show_squares_act)
        self.view_menu.addAction(self.show_stat_act)
        self.view_menu.addAction(self.show_info_act)
        self.view_menu.addSeparator()
        self.view_menu.addAction(self.tool_tip_act)
        self.view_menu.addAction(self.keep_drawing_act)
        
        self.analyze_menu = QtGui.QMenu("&Analyze", self)
        self.analyze_menu.addAction(self.analyze_act)
        self.analyze_menu.addSeparator()
        self.analyze_menu.addAction(self.sigma_up_act)
        self.analyze_menu.addAction(self.sigma_down_act)
        self.analyze_menu.addAction(self.sigma_line_up_act)
        self.analyze_menu.addAction(self.sigma_line_down_act)
        
        self.data_menu = QtGui.QMenu("&Data", self)
        self.data_menu.addAction(self.add_act)
        self.data_menu.addAction(self.restore_act)
        self.data_menu.addAction(self.replace_act)
        self.data_menu.addAction(self.del_act)
        self.data_menu.addSeparator()
        self.data_menu.addAction(self.preview_act)
        self.data_menu.addAction(self.export_act)
        self.data_menu.addSeparator()
        self.data_menu.addAction(self.preview_always_on_top_act)
        
        self.help_menu = QtGui.QMenu("&Help", self)
        self.help_menu.addAction(self.about_act)
        
        self.menuBar().addMenu(self.file_menu)
        self.menuBar().addMenu(self.view_menu)
        self.menuBar().addMenu(self.analyze_menu)
        self.menuBar().addMenu(self.data_menu)
        self.menuBar().addMenu(self.help_menu)
    
    def update_actions(self):
        state = bool(self.image_display.image)
        self.print_act.setEnabled(state)
        self.fit_to_image_act.setEnabled(state)
        self.zoomin_act.setEnabled(state)
        self.zoomout_act.setEnabled(state)
        self.normalsize_act.setEnabled(state)


class MyTableWidgetItem(QtGui.QTableWidgetItem):
    def __init__(self, text='', id=-1):
        super().__init__(text)
        self.id = id


class MyDataTable(QtGui.QTableWidget):
    def __init__(self, parent):
        super().__init__(0, 4, parent)
        self.display = parent
        self.initUI()
    
    def initUI(self):
        self.set_header()
        self.setAlternatingRowColors(True)
        self.setShowGrid(False)
        self.setSortingEnabled(True)
        self.sortItems(0, QtCore.Qt.AscendingOrder)
        points = 11 if os.name == 'posix' else 9
        font  = QtGui.QFont('Helvetica', points)
        self.setFont(font)
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
    
    def sizeHint(self):
        return QtCore.QSize(200, 100)
    
    def set_header(self):
        hor_header = ['wavelength [nm]', 'reflectivity [%]', 'polarization', 'FWHM [nm]']
        self.setHorizontalHeaderLabels(hor_header)
        # self.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
        # self.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.Stretch)
        # self.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.Stretch)
        # self.horizontalHeader().setResizeMode(3, QtGui.QHeaderView.Stretch)
    
    def selected_rows(self):
        indexes = self.selectedIndexes()
        rows = list(set([idx.row() for idx in indexes]))
        return rows
    
    def add_empty_row(self):
        r = self.rowCount()
        space1 = QtGui.QTableWidgetItem('')
        space1.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        space2 = QtGui.QTableWidgetItem('')
        space2.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        
        self.insertRow(self.rowCount())
        self.setItem(r, 0, space1)
        self.setItem(r, 1, space2)
    
    def add_data(self, data):
        r = self.rowCount()
        self.insertRow(r)
        wave = MyTableWidgetItem(data[0], self.display.count)
        wave.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        refl = QtGui.QTableWidgetItem(data[1])
        refl.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        pola = QtGui.QTableWidgetItem(data[2] if data[2] else 'unknown')
        pola.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        fwhm = QtGui.QTableWidgetItem(data[3] if data[3] else 'unknown')
        fwhm.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        
        self.setSortingEnabled(False)
        self.setItem(r, 0, wave)
        self.setItem(r, 1, refl)
        self.setItem(r, 2, pola)
        self.setItem(r, 3, fwhm)
        self.setSortingEnabled(True)
        
        self.display.record[self.display.count] = [self.display.image,
                self.display.scale_factor,
                self.display.lbl.sel_rect,
                self.display.sigma_value_spin.value(),
                self.display.sigma_line_value_spin.value(),
                self.display.bg_cbox.isChecked(),
                self.display.scroll.horizontalScrollBar().value(),
                self.display.scroll.verticalScrollBar().value()]
        self.display.count += 1
    
    def replace_data(self, wavelength, reflectivity):
        row = self.selected_rows()[0]
        id = self.item(row, 0).id
        wave = MyTableWidgetItem(wavelength, id)
        wave.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        refl = QtGui.QTableWidgetItem(reflectivity)
        refl.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        
        self.setSortingEnabled(False)
        self.setItem(row, 0, wave)
        self.setItem(row, 1, refl)
        self.setSortingEnabled(True)
        
        self.display.record[id] = [self.display.image,
                self.display.scale_factor,
                self.display.lbl.sel_rect,
                self.display.sigma_value_spin.value(),
                self.display.sigma_line_value_spin.value(),
                self.display.bg_cbox.isChecked(),
                self.display.scroll.horizontalScrollBar().value(),
                self.display.scroll.verticalScrollBar().value()]
    
    def del_selected_rows(self):
        rows = self.selected_rows()
        for row in rows[::-1]:
            del self.display.record[self.item(row, 0).id]
            self.removeRow(row)
    
    def get_data(self):
        rows = self.selected_rows()
        sel_data = [[self.item (r, 0).text(), self.item(r, 1).text()] \
                for r in rows]
        sel_data = np.array(sel_data).astype(float)
        
        raw_data = np.array([[self.item(i, 0).text(), self.item(i, 1).text(), \
                self.item(i, 2).text()] for i in range(self.rowCount())])
        data = np.array([])
        data_dict = {}
        try:
            raw_data = raw_data[raw_data[:, 0].astype(float).argsort()]
            data = raw_data[:, :2].astype(float)
            polars = raw_data[:, 2]
            polar_keys = set(polars)
            for key in polar_keys:
                data_dict[key] = data[polars == key]
        except:
            pass
        return data, data_dict, sel_data
    
    def get_data_text(self):
        sep_head = ' '*4
        sep = ' '*4
        data = ['\n'+sep.join([self.item(i, 0).text(), self.item(i, 1).text(), \
                self.item(i, 2).text(), self.item(i, 3).text()]) \
                for i in range(self.rowCount())]
        data = [sep_head.join(['wavelength[nm]', 'reflectivity[%]', \
                'polarization', 'FWHM[nm]'])]+data
        return data


class MyPlotWindow(QtGui.QDialog):
    def __init__(self, parent):
        super().__init__(parent, QtCore.Qt.WindowStaysOnTopHint)
        self.initUI()
    
    def initUI(self):
        self.canvas = canvas = MyMplCanvas(self)
        hbox = QtGui.QHBoxLayout(self)
        hbox.addWidget(canvas)
        hbox.setContentsMargins(0, 0, 0, 0)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowSystemMenuHint | \
                QtCore.Qt.WindowMinMaxButtonsHint)
        self.setLayout(hbox)
        self.setMinimumSize(QtCore.QSize(480, 360))
        self.setWindowTitle('Reflectivity Curve Preview')
    
    def closeEvent(self, e):
        self.parent().image_display.preview_act()


class MyMplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=10, height=8, dpi=80):
        self.fig = fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.fig.set_tight_layout(True)
        self.axes.hold(False)
        self.compute_initial_figure()
        super().__init__(fig)
        self.setParent(parent)
        FigureCanvas.updateGeometry(self)
        self.setMouseTracking(True)
    
    def compute_initial_figure(self):
        self.axes.set(xlabel='wavelength [nm]', ylabel='reflectivity [%]',
                xlim=(0, 1000), ylim=(0, 100))
        self.axes.xaxis.set_minor_locator(AutoMinorLocator())
        self.axes.yaxis.set_minor_locator(AutoMinorLocator())
        self.axes.grid(True)
    
    def update_figure(self):
        data, data_dict, sel_data = self.parent().parent().image_display.table.get_data()
        if len(data_dict):
            w_m, w_M = np.min(data[:, 0]), np.max(data[:, 0])
            x_m, x_M = np.floor(w_m/10)*10, np.ceil(w_M/10)*10
            
            self.axes.clear()
            self.axes.hold(True)
            for key in data_dict.keys():
                data = data_dict[key]
                if key:
                    try:
                        angle = float(key)
                        label = 'polarization: {0:.1f} deg'.format(angle)
                    except:
                        label = 'polarization: {0}'.format(key)
                else:
                    label = 'polarization: unknown'
                self.axes.plot(data[:, 0], data[:, 1], 'o-', label=label)
            if sel_data.size:
                self.axes.plot(sel_data[:, 0], sel_data[:, 1], 'ro')
            self.axes.hold(False)
            
            self.axes.set(xlabel='wavelength [nm]', ylabel='reflectivity [%]',
                    xlim=(x_m, x_M), ylim=(0, 100))
            self.axes.xaxis.set_minor_locator(AutoMinorLocator())
            self.axes.yaxis.set_minor_locator(AutoMinorLocator())
            self.axes.legend(loc=0, prop={'size':12})
            self.axes.grid(True)
        else:
            self.axes.plot() # clear the axes
            self.compute_initial_figure()
        self.draw()
    
    def save_image(self):
        path = QtCore.QDir.tempPath()
        filename = 'reflectivity'
        preview_name = os.path.join(path, filename+'.png')
        self.pdf_name = pdf_name = os.path.join(path, filename+'.pdf')
        
        self.fig.savefig(preview_name, dpi=30)
        self.fig.savefig(pdf_name, dpi=80)
        pixmap = QtGui.QPixmap(preview_name)
        self.pixmap = pixmap.scaledToWidth(64)
    
    def mouseMoveEvent(self, e):
        if e.buttons() != QtCore.Qt.NoButton:
            e.accept()
            
            self.save_image()
            
            data = QtCore.QMimeData()
            data.setUrls([QtCore.QUrl(QtCore.QUrl.fromLocalFile(self.pdf_name))])
            
            pixmap = self.pixmap
            
            drag = QtGui.QDrag(self)
            drag.setMimeData(data)
            drag.setPixmap(pixmap)
            drag.setHotSpot(QtCore.QPoint(pixmap.width()/2, pixmap.height()/2))
            drag.exec_()


class MyScrollArea(QtGui.QScrollArea):
    def __init__(self, parent):
        super().__init__(parent)
        if os.name != 'posix':
            self.horizontalScrollBar().valueChanged.connect(self.parent().lbl.update)
            self.verticalScrollBar().valueChanged.connect(self.parent().lbl.update)
    
    def sizeHint(self):
        if self.parent().image:
            if os.name == 'posix':
                extra_size = QtCore.QSize(2, 2)
            else:
                extra_size = QtCore.QSize(2, 23)
            h, w = self.parent().matrix.shape
            return QtCore.QSize(w+2, h+2)+extra_size
        else:
            return _size
    
    def minimumSizeHint(self):
        return _minsize


class MyImageLabel(QtGui.QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.display = parent
        self.sel_rect = QtCore.QRect()
        # trace the mouse
        self.x = 0
        self.y = 0
        self.flag = 1 # drawing flag
        self.initUI()
    
    def initUI(self):
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtGui.QColor(0xff,0xff,0xff,0x66))
        self.setPalette(p)
    
    def sizeHint(self):
        if self.display.image:
            h, w = self.display.matrix.shape
            return QtCore.QSize(w+2, h+2)
        else:
            return super().sizeHint()
    
    def paintEvent(self, e):
        super().paintEvent(e)
        qp = QtGui.QPainter()
        qp.begin(self)
        self.draw_text(e, qp)
        if self.display.analyze_btn.isChecked() and self.flag:
            self.draw_edge_points(qp)
            self.draw_lines(qp)
            self.draw_inner_rect(qp)
            self.draw_outer_rects(qp)
        self.draw_rect(qp)
        self.draw_stat(e, qp)
        self.draw_info(e, qp)
        qp.end()
    
    def draw_text(self, e, qp):
        if not self.display.image:
            qp.setPen(QtGui.QColor(230, 230, 230))
            qp.setFont(QtGui.QFont('Helvetica', 40))
            qp.drawText(e.rect(), QtCore.Qt.AlignCenter, "Drop Image Here")
    
    def draw_stat(self, e, qp):
        if self.display.parent().show_stat_act.isChecked():
            qp.setPen(QtCore.Qt.red)
            points = 12 if os.name == 'posix' else 9
            qp.setFont(QtGui.QFont('Courier', points, QtGui.QFont.Light))
            qp.drawText(e.rect().translated(16, 10), QtCore.Qt.AlignLeft,
                    self.display.stat_text())
    
    def draw_info(self, e, qp):
        if self.display.parent().show_info_act.isChecked():
            height = 105 if os.name == 'posix' else 120
            rect = QtCore.QRect(0, 0, 210, height)
            rect.moveBottomRight(e.rect().bottomRight())
            qp.setPen(QtCore.Qt.black)
            qp.setBrush(QtCore.Qt.black)
            qp.drawRect(rect)
            qp.setPen(QtCore.Qt.white)
            points = 12 if os.name == 'posix' else 8
            qp.setFont(QtGui.QFont('Courier', points, QtGui.QFont.Light))
            qp.drawText(rect.translated(16, 10), QtCore.Qt.AlignLeft,
                    self.display.info_text())
    
    def draw_rect(self, qp):
        qp.setPen(QtCore.Qt.red)
        if not self.sel_rect.isNull():
            qp.drawRect(self.sel_rect.normalized())
    
    def draw_lines(self, qp):
        if self.display.parent().show_lines_act.isChecked():
            lines = [line.translated(1, 1) for line in self.display.lines]
            qp.setPen(QtCore.Qt.magenta)
            qp.drawLines(lines)
    
    def draw_inner_rect(self, qp):
        if self.display.parent().show_squares_act.isChecked():
            qp.setPen(QtCore.Qt.green)
            if not self.display.inner_rect.isEmpty():
                qp.drawRect(self.display.inner_rect.translated(1, 1))
    
    def draw_outer_rects(self, qp):
        if self.display.parent().show_squares_act.isChecked():
            qp.setPen(QtCore.Qt.blue)
            for rect in self.display.outer_rects:
                if not rect.isEmpty():
                    qp.drawRect(rect.translated(1, 1))
    
    def draw_edge_points(self, qp):
        if self.display.parent().show_edges_act.isChecked():
            qp.setPen(QtCore.Qt.darkBlue)
            qp.drawPoints(self.display.edge_points.translated(1, 1))
    
    def show_pos_tip(self):
        if (self.x == 0) or (self.y == 0):
            brightness = '/'
        else:
            try:
                brightness = self.display.matrix[self.y-1, self.x-1]
            except:
                brightness = '/'
        flag = self.display.tooltips and self.frameRect().contains(
                self.mapFromGlobal(self.cursor().pos()))
        tips = ['', 'P({0}, {1}), B({2})'.format(self.x, self.y, brightness)][flag]
        QtGui.QToolTip.showText(self.cursor().pos(), tips, self)
    
    def show_size_tip(self):
        rect = self.sel_rect.normalized()
        tips = ['', 'S({0}, {1})'.format(rect.width(),
                rect.height())][self.display.tooltips]
        QtGui.QToolTip.showText(self.cursor().pos(), tips, self)
    
    def show_rect_tip(self):
        rect = self.sel_rect.normalized()
        tips = ['', 'P({0}, {1}), S({2}, {3})'.format(rect.x(), rect.y(),
                rect.width(), rect.height())][self.display.tooltips]
        QtGui.QToolTip.showText(self.cursor().pos(), tips, self)
    
    def mousePressEvent(self, e):
        self.x = e.x()
        self.y = e.y()
        if e.button() == QtCore.Qt.MidButton:
            self.setCursor(QtGui.QCursor(QtCore.Qt.ClosedHandCursor))
        else:
            if not self.display.parent().keep_drawing_act.isChecked():
                self.flag = 0
            self.sel_rect = QtCore.QRect(e.x(), e.y(), 0, 0)
            self.update()
            self.show_rect_tip()
    
    def mouseMoveEvent(self, e):
        if self.display.isActiveWindow():
            if e.buttons() == QtCore.Qt.NoButton:
                self.x = e.x()
                self.y = e.y()
                self.show_pos_tip()
            elif e.buttons() == QtCore.Qt.MidButton:
                x, y = e.x(), e.y()
                dx = x-self.x
                dy = y-self.y
                scrollbar_h = self.display.scroll.horizontalScrollBar()
                scrollbar_v = self.display.scroll.verticalScrollBar()
                scrollbar_h.setValue(scrollbar_h.value()-dx)
                scrollbar_v.setValue(scrollbar_v.value()-dy)
            else:
                self.x = e.x()
                self.y = e.y()
                self.sel_rect.setRight(e.x()-1)
                self.sel_rect.setBottom(e.y()-1)
                self.update()
                self.show_rect_tip()
    
    def mouseReleaseEvent(self, e):
        if e.button() == QtCore.Qt.MidButton:
            self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
        else:
            if not self.display.parent().keep_drawing_act.isChecked():
                self.flag = 1
            self.sel_rect.setRight(e.x()-1)
            self.sel_rect.setBottom(e.y()-1)
            if self.sel_rect.normalized().isEmpty(): # to get rid of the empty but null rect
                self.sel_rect = QtCore.QRect()
            if self.display.image:
                self.display.update_total('rect')
        self.update()
        self.x = e.x()
        self.y = e.y()
        self.show_pos_tip()
    
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            url = e.mimeData().urls()[0] # only consider the first file
            fullname = url.toLocalFile()
            if os.path.splitext(fullname)[1] in _formats:
                e.accept()
            else:
                e.ignore()
        else:
              e.ignore()
    
    def dragMoveEvent(self, e):
        # seems useless
        super().dragMoveEvent(e)
    
    def dropEvent(self, e):
        url = e.mimeData().urls()[0] # only consider the first file
        fullname = url.toLocalFile()
        self.display.check_fullname(fullname)
        e.accept()


class ImageDisplay(QtGui.QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.image = '' # image fullname
        self.matrix = None # image ndarray
        self.background = '' # background image fullname
        self.cal = '' # calibration file fullname
        self.cal_data = [] # calibration data
        self.scale_factor = 1 # image scale factor
        self.hold = 0 # the flag indicates if keep current window size
        self.tooltips = 0 # switch tooltips on/off
        self.inner_rect = QtCore.QRect() # pattern area
        self.outer_rects = [] # bg areas list
        self.edge_points = QtGui.QPolygon() # image canny edge points
        self.lines = [] # lines given by hough transform
        self.record = {} # record settings for each data point
        self.count = 0 # number of all data points taken from start
        self.stat = {'maximum':'',
                     'minimum':'',
                     'mean':'',
                     'std':''} # statistic on the selected area
        self.info = {'wavelength':'',
                     'reflectivity':'',
                     'FWHM':'',
                     'exposure':'',
                     'brightness':'',
                     'gain':'',
                     'polarization':''} # info dict: {wavelength, reflectivity, FWHM, exposure, brightness, gain, polarization}
        self.initUI()
    
    def initUI(self):
        # Path & File Settings
        path_label = QtGui.QLabel('Path')
        self.path_list = path_list = QtGui.QComboBox(self)
        path_list.currentIndexChanged.connect(self.set_lists)
        
        imag_label = QtGui.QLabel('Image')
        self.imag_list = imag_list = QtGui.QComboBox(self)
        imag_list.currentIndexChanged.connect(self.check_lists)
        
        self.format_list = format_list = QtGui.QComboBox(self)
        format_list.setFixedWidth(70)
        format_list.addItems(_formats)
        format_list.currentIndexChanged.connect(self.set_imaglist)
        
        space = ' ' if os.name == 'posix' else ''
        self.cal_cbox = cal_cbox = QtGui.QCheckBox('Calibr'+space, self, checked=True)
        cal_cbox.stateChanged[int].connect(self.enable_cal)
        
        self.cal_list = cal_list = QtGui.QComboBox(self)
        cal_list.currentIndexChanged.connect(self.check_lists)
        
        self.bg_cbox = bg_cbox = QtGui.QCheckBox('BG'+space, self, checked=True)
        bg_cbox.stateChanged[int].connect(self.enable_bg)
        
        self.bg_list = bg_list = QtGui.QComboBox(self)
        bg_list.currentIndexChanged.connect(self.check_bg)
        
        grid = QtGui.QGridLayout()
        grid.setSpacing(10)
        # grid.setColumnStretch(1, 1)
        grid.addWidget(path_label, 1, 0, QtCore.Qt.AlignRight)
        grid.addWidget(path_list, 1, 1, 1, 4)
        grid.addWidget(imag_label, 2, 0, QtCore.Qt.AlignRight)
        grid.addWidget(imag_list, 2, 1, 1, 3)
        grid.addWidget(format_list, 2, 4)
        grid.addWidget(cal_cbox, 3, 0, QtCore.Qt.AlignRight)
        grid.addWidget(cal_list, 3, 1, 1, 4)
        grid.addWidget(bg_cbox, 4, 0, QtCore.Qt.AlignRight)
        grid.addWidget(bg_list, 4, 1, 1, 4)
        
        # Analysis settings
        sigma_label = QtGui.QLabel('Edge')
        self.sigma_value_spin = sigma_value_spin = QtGui.QDoubleSpinBox()
        sigma_value_spin.setRange(0.0, 10.0)
        sigma_value_spin.setSingleStep(0.01)
        sigma_value_spin.setValue(0.0)
        sigma_value_spin.setFixedWidth(62)
        sigma_value_spin.setAlignment(QtCore.Qt.AlignRight)
        sigma_value_spin.valueChanged[float].connect(self.set_sigma)
        
        self.sigma_sld = sigma_sld = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        sigma_sld.setMinimum(0)
        sigma_sld.setMaximum(100)
        sigma_sld.setTickPosition(QtGui.QSlider.TicksBelow)
        sigma_sld.valueChanged.connect(self.change_sigma)
        
        sigma_line_label = QtGui.QLabel('Line')
        self.sigma_line_value_spin = sigma_line_value_spin = QtGui.QDoubleSpinBox()
        sigma_line_value_spin.setRange(0.0, 10.0)
        sigma_line_value_spin.setSingleStep(0.01)
        sigma_line_value_spin.setValue(0.0)
        sigma_line_value_spin.setFixedWidth(62)
        sigma_line_value_spin.setAlignment(QtCore.Qt.AlignRight)
        sigma_line_value_spin.valueChanged[float].connect(self.set_sigma_line)
        
        self.sigma_line_sld = sigma_line_sld = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        sigma_line_sld.setMinimum(0)
        sigma_line_sld.setMaximum(100)
        sigma_line_sld.setTickPosition(QtGui.QSlider.TicksBelow)
        sigma_line_sld.valueChanged.connect(self.change_sigma_line)
        
        zoom_label = QtGui.QLabel('Zoom')
        self.zoom_value_label = zoom_value_label = QtGui.QLabel('100%')
        zoom_value_label.setFixedWidth(40)
        zoom_value_label.setAlignment(QtCore.Qt.AlignRight)
        
        self.zoom_sld = zoom_sld = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        zoom_sld.setMinimum(1)
        zoom_sld.setMaximum(13)
        zoom_sld.setTickInterval(1)
        zoom_sld.setTickPosition(QtGui.QSlider.TicksBelow)
        zoom_sld.setValue(7)
        zoom_sld.setEnabled(False)
        zoom_sld.valueChanged.connect(self.change_zoom)
        zoom_sld.sliderPressed.connect(self.set_hold)
        zoom_sld.actionTriggered.connect(self.set_hold)
        zoom_sld.sliderReleased.connect(self.unset_hold)
        
        hline = QtGui.QFrame()
        hline.setFrameStyle(QtGui.QFrame.HLine)
        hline.setFrameShadow(QtGui.QFrame.Sunken)
        hline.setLineWidth(1)
        
        grid.addWidget(hline, 5, 0, 1, 5)
        grid.addWidget(sigma_label, 6, 0, QtCore.Qt.AlignRight)
        grid.addWidget(sigma_sld, 6, 1, 1, 3)
        grid.addWidget(sigma_value_spin, 6, 4)
        grid.addWidget(sigma_line_label, 7, 0, QtCore.Qt.AlignRight)
        grid.addWidget(sigma_line_sld, 7, 1, 1, 3)
        grid.addWidget(sigma_line_value_spin, 7, 4)
        grid.addWidget(zoom_label, 8, 0, QtCore.Qt.AlignRight)
        grid.addWidget(zoom_sld, 8, 1, 1, 3)
        grid.addWidget(zoom_value_label, 8, 4)
        
        # Table view settings
        self.table = table = MyDataTable(self)
        table.itemSelectionChanged.connect(self.update_button)
        
        self.add_btn = add_btn = QtGui.QPushButton('+')
        add_btn.setEnabled(False)
        add_btn.setToolTip('Add current data point')
        add_btn.clicked.connect(self.add_point)
        
        self.export_btn = export_btn = QtGui.QPushButton("↑")
        export_btn.setEnabled(False)
        export_btn.setToolTip('Export data')
        export_btn.clicked.connect(self.export_point)
        
        restore_symbol = '⟲' if os.name == 'posix' else '↺'
        self.restore_btn = restore_btn = QtGui.QPushButton(restore_symbol)
        restore_btn.setEnabled(False)
        restore_btn.setToolTip('Restore to the settings of the selected data point')
        restore_btn.clicked.connect(self.restore_point)
        
        replace_symbol = '⥊' if os.name == 'posix' else '⇔'
        self.replace_btn = replace_btn = QtGui.QPushButton(replace_symbol)
        replace_btn.setEnabled(False)
        replace_btn.setToolTip('Change the selected data point to current data point')
        replace_btn.clicked.connect(self.replace_point)
        
        self.del_btn = del_btn = QtGui.QPushButton("−")
        del_btn.setEnabled(False)
        del_btn.setToolTip('Delete selected data point(s)')
        del_btn.clicked.connect(self.del_point)
        
        self.preview_btn = preview_btn = QtGui.QPushButton("✪")
        preview_btn.setCheckable(True)
        preview_btn.setToolTip('Preview data')
        preview_btn.clicked[bool].connect(self.preview)
        
        hline2 = QtGui.QFrame()
        hline2.setFrameStyle(QtGui.QFrame.HLine)
        hline2.setFrameShadow(QtGui.QFrame.Sunken)
        hline2.setLineWidth(1)
        
        grid.setRowStretch(14, 1)
        grid.addWidget(hline2, 9, 0, 1, 5)
        grid.addWidget(table, 10, 1, 6, 4)
        grid.addWidget(add_btn, 10, 0)
        grid.addWidget(del_btn, 11, 0)
        grid.addWidget(restore_btn, 12, 0)
        grid.addWidget(replace_btn, 13, 0)
        grid.addWidget(preview_btn, 14, 0, QtCore.Qt.AlignBottom)
        grid.addWidget(export_btn, 15, 0)
        
        # Action button settings
        self.analyze_btn = analyze_btn = QtGui.QPushButton("Analyze")
        analyze_btn.setCheckable(True)
        analyze_btn.clicked[bool].connect(self.do_analyze)
        
        hline3 = QtGui.QFrame()
        hline3.setFrameStyle(QtGui.QFrame.HLine)
        hline3.setFrameShadow(QtGui.QFrame.Sunken)
        hline3.setLineWidth(1)
        
        grid.addWidget(hline3, 16, 0, 1, 5)
        grid.addWidget(analyze_btn, 17, 3, 1, 2)
        
        gbox = QtGui.QGroupBox()
        gbox.setFixedWidth(300)
        gbox.setLayout(grid)
        
        # Screen settings
        self.lbl = lbl = MyImageLabel(self)
        lbl.setAlignment(QtCore.Qt.AlignCenter)
        lbl.setStyleSheet('border: 1px solid black; border-radius: 0px;')
        self.scroll = scroll = MyScrollArea(self)
        scroll.setAlignment(QtCore.Qt.AlignCenter)
        scroll.setWidget(lbl)
        scroll.setBackgroundRole(QtGui.QPalette.Dark)
        scroll.setWidgetResizable(True)
        
        # Combine
        hbox = QtGui.QHBoxLayout(self)
        hbox.addWidget(scroll)
        hbox.addWidget(gbox)
        self.setLayout(hbox)
        
        # Plot window settings
        self.plot = MyPlotWindow(self.parent())
        self.plot.setGeometry(QtCore.QRect(100, 100, 400, 300))
        self.plot.setVisible(False)
    
    # path control methods
    def open_file(self):
        filter_string = 'Image Files ('+' '.join(['*'+format for format in _formats])+')'
        fullname = QtGui.QFileDialog.getOpenFileName(self.parent(),
                'Open image', _home, filter_string)
        self.check_fullname(fullname)
    
    def choose_dir(self):
        directory = QtGui.QFileDialog.getExistingDirectory(self,
                "Select directory", _home)
        self.set_dir(directory)
    
    def set_dir(self, directory):
        if directory:
            pe = self.path_list
            dir_list = [pe.itemText(i) for i in range(pe.count())]
            if directory not in dir_list:
                pe.addItem(directory)
                pe.setCurrentIndex(pe.count()-1)
            else:
                idx = dir_list.index(directory)
                if pe.currentIndex() == idx:
                    self.set_lists()
                else:
                    pe.setCurrentIndex(idx)
    
    def set_lists(self, path='', silent=0):
        self.set_imaglist(silent=1)
        self.set_callist(silent=1)
        if not silent:
            self.check_lists()
    
    def set_imaglist(self, idx=0, silent=0):
        """ This method is called when path or image format list changes.
        
        Keyword arguments:
        idx -- the index of the current item in imag_list, no use.
        silent -- if 0, this method will cause an currentIndexChanged event;
            if 1, this method will only change the imag_list content.
        """
        path = self.path_list.currentText()
        if silent:
            self.imag_list.blockSignals(True)
        if os.path.exists(path):
            imags = [f for f in os.listdir(path) \
                     if os.path.splitext(f)[1] == self.format_list.currentText()]
            self.imag_list.clear()
            self.imag_list.addItems(imags)
        else:
            self.imag_list.clear()
        if silent:
            self.imag_list.blockSignals(False)
    
    def set_callist(self, silent=0):
        """ This method is called only when path changes.
        
        Keyword arguments:
        silent -- if 0, this method will cause an currentIndexChanged event;
            if 1, this method will only change the cal_list content.
        """
        path = self.path_list.currentText()
        if silent:
            self.cal_list.blockSignals(True)
        if os.path.exists(path):
            cals = [f for f in os.listdir(path) \
                     if os.path.splitext(f)[1] == _cal_format]
            self.cal_list.clear()
            self.cal_list.addItems(cals)
        else:
            self.cal_list.clear()
        if silent:
            self.cal_list.blockSignals(False)
    
    def check_fullname(self, fullname):
        if fullname and (fullname != self.image):
            path, filename = os.path.split(fullname)
            suffix = os.path.splitext(filename)[1]
            
            self.format_list.blockSignals(True)
            index_f = _formats.index(suffix)
            self.format_list.setCurrentIndex(index_f)
            self.format_list.blockSignals(False)
            
            self.imag_list.blockSignals(True)
            self.cal_list.blockSignals(True)
            self.set_dir(path)
            imags = [f for f in os.listdir(path) \
                     if os.path.splitext(f)[1] == suffix]
            index_i = imags.index(filename)
            self.imag_list.setCurrentIndex(index_i)
            self.imag_list.blockSignals(False)
            self.cal_list.blockSignals(False)
            self.check_lists()
    
    
    def check_lists(self):
        path = self.path_list.currentText()
        image = os.path.join(path, self.imag_list.currentText())
        image = image if os.path.isfile(image) else ''
        cal = os.path.join(path, self.cal_list.currentText())
        cal = cal if os.path.isfile(cal) else ''
        if (image != self.image) or (cal != self.cal):
            self.image = image
            if cal != self.cal:
                self.cal = cal
                self.set_cal_data()
            self.update_total('dir')
    
    def check_bg(self):
        path = self.path_list.currentText()
        filename = self.bg_list.currentText()
        fullname = os.path.join(path, filename)
        fullname = fullname if os.path.isfile(fullname) else ''
        if fullname != self.background:
            self.background = fullname
            self.update_total('background')
    
    def enable_cal(self, enabled):
        self.cal_list.setEnabled(enabled)
        self.bg_cbox.setEnabled(enabled)
        self.bg_list.setEnabled(enabled and self.bg_cbox.isChecked())
        self.update_total('dir')
    
    def enable_bg(self, enabled):
        self.bg_list.setEnabled(enabled)
        self.update_total('background')
    
    # sigma control methods
    def set_sigma_act(self, step):
        value = max(min(self.sigma_value_spin.value()+step, 10.0), 0.0)
        self.sigma_value_spin.setValue(value)
    
    def sigma_up(self):
        self.set_sigma_act(0.10)
    
    def sigma_down(self):
        self.set_sigma_act(-0.10)
    
    def set_sigma(self, value):
        sigma = round(10*value)
        sigma_o = self.sigma_sld.value()
        if sigma_o != sigma:
            self.sigma_sld.setValue(sigma)
        self.update_total('sigma_edge')
    
    def change_sigma(self):
        sigma = self.sigma_sld.value()
        sigma_r = round(self.sigma_value_spin.value()*10)
        if sigma_r != sigma:
            self.sigma_value_spin.setValue(sigma*0.1)
    
    def set_sigma_line(self, value):
        sigma = round(10*value)
        sigma_o = self.sigma_line_sld.value()
        if sigma_o != sigma:
            self.sigma_line_sld.setValue(sigma)
        self.update_total('sigma_line')
    
    def change_sigma_line(self):
        sigma = self.sigma_line_sld.value()
        sigma_r = round(self.sigma_line_value_spin.value()*10)
        if sigma_r != sigma:
            self.sigma_line_value_spin.setValue(sigma*0.1)
    
    def set_sigma_line_act(self, step):
        value = max(min(self.sigma_line_value_spin.value()+step, 10.0), 0.0)
        self.sigma_line_value_spin.setValue(value)
    
    def sigma_line_up(self):
        self.set_sigma_line_act(0.10)
    
    def sigma_line_down(self):
        self.set_sigma_line_act(-0.10)
    
    # image converting methods
    def array2gray(self, array):
        if np.ndim(array) == 3:
            array = np.dot(array[..., :3], [0.2989, 0.5870, 0.1140]) # ignore alpha channel
        gray = np.require(array, np.uint8, 'C')
        return gray
    
    def gray2qimage(self, gray):
        gray = np.require(gray, np.uint32, 'C')
        gray *= 65793 # convert 8-bits to 32-bits while keeping the gray color
        gray += 4278190080 # add alpha channel to solve the issue on windows
        h, w = gray.shape
        imag = QtGui.QImage(gray.data, w, h, QtGui.QImage.Format_ARGB32_Premultiplied)
        return imag
    
    # calibrating and parsing methods
    def modified(self, sample):
        if not sample[1]:
            sample[1] = sample[0]
        return sample
    
    def get_raw_cal_data(self):
        data = []
        
        with open(self.cal) as f:
            reader = csv.reader(f)
            flag = 0
            data.append([])
            for row in reader:
                try:
                    wavelength = float(row[0])
                    data[-1].append(row)
                    if not flag:
                        flag = 1
                except:
                    if flag:
                        flag = 0
                        data.append([])
        return data
    
    def get_cal_data(self):
        data = self.get_raw_cal_data()
        current_value = self.modified(data[0][0])[:]
        for i in range(len(data)):
            for j in range(len(data[i])):
                sample = data[i][j]
                for k in range(len(sample)):
                    sample = self.modified(sample)
                    if sample[k]:
                        current_value[k] = sample[k]
                    else:
                        sample[k] = current_value[k]
        return data
    
    def set_cal_data(self):
        try:
            self.cal_data = self.get_cal_data()
        except:
            self.cal_data = []
    
    def preprocessor(self, part):
        if part:
            return '_'+'_'.join(part.split('/'))
        else:
            return part
    
    def bg_generator(self, prefix, exposure, gain):
        return ''.join([prefix, self.preprocessor(exposure), self.preprocessor(gain)])
    
    def find_nearest(self, array, value):
        idx = (np.abs(array-value)).argmin()
        return array[idx]
    
    def find_nearest_index(self, array, value):
        idx = (np.abs(array-value)).argmin()
        return idx
    
    def name_parser(self, name):
        """ Parse the image name to get more information.
            The information will fill into self.info dictionary.
        
        Keyword arguments:
        name -- the name of image, without suffix.
        """
        for key in self.info.keys():
            self.info[key] = ''
        
        try:
            tokens = name.split('_')
            if len(tokens) < 2:
                peak = tokens[0]
                turn = 0
            else:
                peak, turn = tokens[:2]
            peak = float(peak.split('n')[0])
            try:
                turn = int(turn)
            except:
                turn = 0
            self.info['wavelength'] = '{0:.3f}'.format(peak)
            # calibration
            if self.cal_cbox.isChecked() and self.cal:
                data = np.array(self.cal_data)
                part_data = np.concatenate(data[_filter[turn]])
                peaks = part_data[:, 1].astype(float)
                idx = self.find_nearest_index(peaks, peak)
                self.info['FWHM'] = part_data[idx, 2]
                self.info['exposure'] = part_data[idx, 3]
                self.info['brightness'] = part_data[idx, 4]
                self.info['gain'] = part_data[idx, 5]
                self.info['polarization'] = part_data[idx, 6]
                real_peak = peaks[idx]
                self.info['wavelength'] = '{0:.3f}'.format(real_peak)
        except:
            pass
    
    def info_text(self):
        text = ['  wavelength: '+(self.info['wavelength'] and \
                (self.info['wavelength']+' nm')),
                'reflectivity: '+(self.info['reflectivity'] and \
                (self.info['reflectivity']+'%')),
                '        FWHM: '+(self.info['FWHM'] and \
                (self.info['FWHM']+' nm')),
                '    exposure: '+(self.info['exposure'] and \
                (self.info['exposure']+' s')),
                '  brightness: '+self.info['brightness'],
                '        gain: '+self.info['gain'],
                'polarization: '+self.info['polarization']]
        return '\n'.join(text)
    
    def stat_text(self):
        text = ['maximum: '+self.stat['maximum'],
                'minimum: '+self.stat['minimum'],
                '   mean: '+self.stat['mean'],
                '    std: '+self.stat['std']]
        return '\n'.join(text)
    
    def is_background(self, f):
        exposure = self.info['exposure']
        gain = self.info['gain']
        polarization = self.info['polarization']
        
        name, suffix = os.path.splitext(f)
        c0 = bool(suffix == self.format_list.currentText())
        c1 = False
        try:
            parts = name.split('_')
            if '/'.join(parts[1:3]) == exposure:
                if (len(parts) == 3) or (parts[3] == polarization) or (parts[3] == gain):
                    c1 = True
        except:
            pass
        return (c0 and c1)
    
    def set_background(self):
        try:
            path = self.path_list.currentText()
            bgs = [f for f in os.listdir(path) if self.is_background(f)]
            self.background = os.path.join(path, bgs[0])
            self.bg_list.blockSignals(True)
            self.bg_list.clear()
            self.bg_list.addItems(bgs)
            self.bg_list.blockSignals(False)
        except:
            self.background = ''
            self.bg_list.blockSignals(True)
            self.bg_list.clear()
            self.bg_list.blockSignals(False)
    
    # data editing methods
    def cal_reflectivity(self, inner_b, outer_bs):
        reflectivity = None
        
        if inner_b != None:
            outer_bs = np.array(outer_bs)
            mask = (outer_bs >= 0)
            outer_bs = outer_bs[mask]
            if (inner_b != -1) and len(outer_bs):
                reflectivity = inner_b/np.mean(outer_bs)
        return reflectivity
    
    def add_point(self):
        data = []
        data.append(self.info['wavelength'])
        data.append(self.info['reflectivity'])
        data.append(self.info['polarization'])
        data.append(self.info['FWHM'])
        self.table.add_data(data)
        self.update_export()
        if self.plot.isVisible():
            self.plot.canvas.update_figure()
        # with open("reflectivity.txt", "a") as f:
        #     f.write('{0} {1:.4f}\n'.format(wavelength, reflectivity))
    
    def add_act(self):
        self.add_btn.click()
    
    def export_point(self):
        filter_string = 'Text files (*.txt)'
        fullname = QtGui.QFileDialog.getSaveFileName(self.parent(),
                'Export data as text file (*.txt)', _home, filter_string)
        try:
            with open(fullname, 'w') as f:
                data = self.table.get_data_text()
                f.writelines(data)
        except:
            msg = 'Sorry, for some reason, exporting has failed...'
            QtGui.QMessageBox.information(self, 'Shit happens', msg)
    
    def export_act(self):
        self.export_btn.click()
    
    def do_restore(self):
        # restore dir
        path, filename = os.path.split(self.image)
        suffix = os.path.splitext(filename)[1]
        self.imag_list.blockSignals(True)
        index_f = _formats.index(suffix)
        self.set_dir(path)
        self.format_list.setCurrentIndex(index_f)
        imags = [f for f in os.listdir(path) \
                 if os.path.splitext(f)[1] == suffix]
        index_i = imags.index(filename)
        self.imag_list.setCurrentIndex(index_i)
        self.imag_list.blockSignals(False)
        # restore the image and paint
        self.update_total('dir')
        # restore menu
        self.parent().zoomin_act.setEnabled(self.scale_factor < 4.7)
        self.parent().zoomout_act.setEnabled(self.scale_factor > 0.21)
        self.parent().sigma_up_act.setEnabled(self.sigma_value_spin.value() < 10.0)
        self.parent().sigma_down_act.setEnabled(self.sigma_value_spin.value() > 0.0)
        self.parent().sigma_line_up_act.setEnabled(
                self.sigma_line_value_spin.value() < 10.0)
        self.parent().sigma_line_down_act.setEnabled(
                self.sigma_line_value_spin.value() > 0.0)
    
    def restore_point(self):
        row = self.table.selected_rows()[0]
        paras = self.record[self.table.item(row, 0).id]
        self.image = paras[0]
        self.scale_factor = paras[1]
        self.lbl.sel_rect = paras[2]
        self.bg_cbox.blockSignals(True)
        self.bg_cbox.setChecked(paras[5])
        self.bg_cbox.blockSignals(False)
        self.bg_list.setEnabled(paras[5])
        self.sigma_value_spin.blockSignals(True)
        self.sigma_value_spin.setValue(paras[3])
        self.sigma_sld.setValue(round(10*paras[3]))
        self.sigma_value_spin.blockSignals(False)
        self.sigma_line_value_spin.blockSignals(True)
        self.sigma_line_value_spin.setValue(paras[4])
        self.sigma_line_sld.setValue(round(10*paras[4]))
        self.sigma_line_value_spin.blockSignals(False)
        self.zoom_sld.blockSignals(True)
        self.zoom_sld.setValue(8+round(np.log(paras[1])/np.log(1.25)))
        self.zoom_value_label.setText("{0}%".format(round(100*paras[1])))
        self.zoom_sld.blockSignals(False)
        
        self.do_restore()
        self.scroll.horizontalScrollBar().setValue(paras[6])
        self.scroll.verticalScrollBar().setValue(paras[7])
    
    def restore_act(self):
        self.restore_btn.click()
    
    def replace_point(self):
        wavelength = self.info['wavelength']
        reflectivity = self.info['reflectivity']
        self.table.replace_data(wavelength, reflectivity)
        if self.plot.isVisible():
            self.plot.canvas.update_figure()
    
    def replace_act(self):
        self.replace_btn.click()
    
    def del_point(self):
        self.table.del_selected_rows()
        self.update_export()
        if self.plot.isVisible():
            self.plot.canvas.update_figure()
    
    def del_act(self):
        self.del_btn.click()
    
    def preview(self, pressed):
        self.sender().setText(["✪", "✩"][pressed])
        self.sender().setToolTip(['Preview data', 'Hide preview window'][pressed])
        self.parent().preview_act.setText(["Show Preview", "Hide Preview"][pressed])
        if pressed:
            self.plot.canvas.update_figure()
            qr = self.parent().frameGeometry()
            self.plot.move(qr.x()+30, qr.y()+30)
        self.plot.setVisible(pressed)
    
    def preview_act(self):
        self.preview_btn.click()
    
    def preview_always_on_top(self):
        if self.parent().preview_always_on_top_act.isChecked():
            self.plot.setWindowFlags(self.plot.windowFlags() |
                    QtCore.Qt.WindowStaysOnTopHint)
        else:
            self.plot.setWindowFlags(self.plot.windowFlags() ^
                    QtCore.Qt.WindowStaysOnTopHint)
        if self.preview_btn.isChecked():
            self.plot.setVisible(True)
        else:
            self.plot.setVisible(False)
    
    # analysis methods
    def p_isvalid(self, dmax, i, N, x, y):
        z = x+y*1j
        return (np.abs(z) >= dmax) and (np.pi/N*2*i <= self.angle(z) <= np.pi/N*2*(i+1))
    
    def isvalid(self, dmax, i, N, x1, x2, y1, y2):
        valid = self.p_isvalid(dmax, i, N, x1, y1) and self.p_isvalid(dmax, i, N, x1, y2) \
                and self.p_isvalid(dmax, i, N, x2, y1) and self.p_isvalid(dmax, i, N, x2, y2)
        return valid
    
    def angle(self, z):
        return np.angle(z) if np.angle(z) >= 0 else 2*np.pi+np.angle(z)
    
    def inner_optimizer(self, x1, y1, xc, yc, dmin, std, factor):
        """ Get the inner brightness and rect for the selected area.
        
        Note that when selected area is empty, brightness would be set to -1.
        Make sure that the image exists before calling this method.
        
        Returns:
        float brightnss, QRect rect.
        """
        inner_b = -1
        inner_rect = QtCore.QRect()
        
        eta = 1.0
        while True:
            a = eta*dmin/np.sqrt(2)
            x1_i = x1+round(xc-a)
            x2_i = x1+round(xc+a)
            y1_i = y1+round(yc-a)
            y2_i = y1+round(yc+a)
            inner_block = self.matrix[y1_i:y2_i, x1_i:x2_i]
            inner_rect = QtCore.QRect(x1_i, y1_i, x2_i-x1_i, y2_i-y1_i)
            if inner_block.size:
                inner_b = np.mean(inner_block)
                std_i = np.std(inner_block)
                if std_i <= std:
                    break
                else:
                    eta *= factor
            else:
                break
        return inner_b, inner_rect
    
    def outer_optimizer(self, x1, y1, xc, yc, dmax, std, factor, N=4):
        """ Get the inner brightness and rect for the selected area.
        
        Note that when selected area is empty, brightness would be set to -1.
        Make sure that the image exists before calling this method.
        
        Returns:
        array b_list, QPolygon rect_list.
        """
        outer_b_list = []
        outer_rect_list = []
        for i in range(N):
            outer_b = -1
            outer_rect = QtCore.QRect()
            
            eta = 1.0
            d = 1.2*dmax
            while True:
                a = 1.0*eta
                xc_o = d*np.cos(np.pi/N*(2*i+1))
                yc_o = d*np.sin(np.pi/N*(2*i+1))
                x1_o = xc_o-a
                x2_o = xc_o+a
                y1_o = yc_o-a
                y2_o = yc_o+a
                if self.isvalid(dmax, i, N, x1_o, x2_o, y1_o, y2_o):
                    x1_o = max(round(x1+xc+x1_o), 0)
                    x2_o = max(round(x1+xc+x2_o), 0)
                    y1_o = max(round(y1+yc+y1_o), 0)
                    y2_o = max(round(y1+yc+y2_o), 0)
                    outer_block = self.matrix[y1_o:y2_o, x1_o:x2_o]
                    if outer_block.size:
                        brightness = np.mean(outer_block)
                        std_o = np.std(outer_block)
                        if std_o <= std:
                            eta *= factor
                            outer_b = brightness
                            outer_rect = QtCore.QRect(x1_o, y1_o, x2_o-x1_o, y2_o-y1_o)
                        else:
                            break
                    else:
                        eta *= factor
                        continue
                else:
                    break
            outer_b_list.append(outer_b)
            outer_rect_list.append(outer_rect)
        return outer_b_list, outer_rect_list
    
    def get_edges(self, sigma=None):
        """ Get the edges in current image. If image is None, returns None, 0, 0.
        
        Returns:
        edges, x1, y1.
        """
        edges = None
        x1 = 0
        y1 = 0
        
        if self.image and self.analyze_btn.isChecked():
            sigma = self.sigma_value_spin.value() if sigma == None else sigma
            imag = self.matrix
            rect = self.lbl.sel_rect.normalized()
            if rect.isEmpty():
                edges = filter.canny(imag, sigma=sigma)
            else:
                x1 = max(rect.left()-1, 0)
                x2 = rect.right()
                y1 = max(rect.top()-1, 0)
                y2 = rect.bottom()
                part = imag[y1:y2, x1:x2]
                if part.size:
                    edges = filter.canny(part, sigma=sigma)
        return edges, x1, y1
    
    def get_lines(self, method=0):
        """ Get the lines in current image. If image is None, returns []
        
        Returns:
        lines -- QLine list
        """
        lines = []
        
        sigma = self.sigma_line_value_spin.value()
        edges, x1, y1 = self.get_edges(sigma)
        if edges != None:
            if method == 0:
                h, theta, d = transform.hough_line(edges)
                rows, cols = edges.shape
                for _, angle, dist in zip(*transform.hough_line_peaks(h, theta, d)):
                    x1_l = x1
                    y1_l = y1+round((dist-0*np.cos(angle))/np.sin(angle))
                    x2_l = x1+cols
                    y2_l = y1+round((dist-cols*np.cos(angle))/np.sin(angle))
                    x1_r = x1+round((dist-0*np.sin(angle))/np.cos(angle))
                    y1_r = y1
                    x2_r = x1+round((dist-rows*np.sin(angle))/np.cos(angle))
                    y2_r = y1+rows
                    X = [x1_l, x2_l, x1_r, x2_r]
                    Y = [y1_l, y2_l, y1_r, y2_r]
                    # don't know why on windows the x and y will be np.float64... so
                    # converting to integer to prevent this
                    p = [QtCore.QPoint(int(x), int(y)) for (x, y) in sorted(zip(X, Y))]
                    lines.append(QtCore.QLine(p[1], p[2]))
            elif method == 1:
                lines = transform.probabilistic_hough_line(edges, threshold=50,
                        line_length=round(80*self.scale_factor),
                        line_gap=round(5*self.scale_factor))
                lines = [QtCore.QLine(QtCore.QPoint(*line[0]), \
                        QtCore.QPoint(*line[1])).translated(x1, y1) for line in lines]
            else:
                pass
        return lines
    
    def analyze(self):
        inner_b, inner_rect = None, QtCore.QRect()
        outer_b_list, outer_rect_list = [], []
        edge_points = QtGui.QPolygon()
        
        edges, x1, y1 = self.get_edges()
        if edges != None:
            h, w = edges.shape
            mask = (edges != 0)
            if mask.any():
                x = (edges*np.arange(w))[mask]
                y = (edges*(np.arange(h).reshape(-1, 1)))[mask]
                for i in range(len(x)):
                    edge_points.append(QtCore.QPoint(x1+x[i], y1+y[i]))
                edge_points = QtGui.QPolygon(edge_points)
                xc = np.mean(x)
                yc = np.mean(y)
                d = np.sqrt((x-xc)**2+(y-yc)**2)
                d_min = np.min(d)
                d_max = np.max(d)
                inner_b, inner_rect = self.inner_optimizer(x1, y1, xc, yc, d_min, 10.0, 0.9)
                outer_b_list, outer_rect_list = self.outer_optimizer(x1, y1, xc,
                        yc, d_max, 3.0, 1.1, 10)
        return inner_b, inner_rect, outer_b_list, outer_rect_list, edge_points
    
    def do_analyze(self, pressed):
        self.sender().setText(["Analyze", "Origin"][pressed])
        self.parent().analyze_act.setText(["Run Analyze", "Origin"][pressed])
        self.update_total('analyze')
    
    def do_analyze_act(self):
        self.analyze_btn.click()
    
    # update methods
    def update_total(self, kind):
        # this method takes care of everything
        if kind == 'dir':
            self.update_exp_info()
            self.parent().update_actions()
            self.update_matrix()
            if self.analyze_btn.isChecked():
                self.update_lines()
                self.update_paint()
            self.update_imag()
            self.update_window()
        elif kind == 'zoom':
            level = self.zoom_sld.value()
            zoom = _zoom_level[level-1]
            self.zoom_value_label.setText("{0}%".format(round(100*zoom)))
            factor = zoom/self.scale_factor
            if factor != 1.0:
                self.scale_factor = zoom
                self.parent().zoomin_act.setEnabled(self.scale_factor < 5.0)
                self.parent().zoomout_act.setEnabled(self.scale_factor > 0.2)
                self.update_matrix()
                self.update_scrollbar(factor)
                self.update_rect(factor)
                if self.analyze_btn.isChecked():
                    self.update_lines()
                    self.update_paint()
                self.update_imag()
                self.update_window()
        elif kind == 'rect':
            self.update_stat()
            if self.analyze_btn.isChecked():
                self.update_lines()
                self.update_paint()
        elif kind == 'sigma_edge':
            self.parent().sigma_up_act.setEnabled(self.sigma_value_spin.value() < 10.0)
            self.parent().sigma_down_act.setEnabled(self.sigma_value_spin.value() > 0.0)
            if self.analyze_btn.isChecked() and self.image:
                self.update_paint(1)
        elif kind == 'sigma_line':
            self.parent().sigma_line_up_act.setEnabled(
                    self.sigma_line_value_spin.value() < 10.0)
            self.parent().sigma_line_down_act.setEnabled(
                    self.sigma_line_value_spin.value() > 0.0)
            if self.analyze_btn.isChecked() and self.image:
                self.update_lines(1)
        elif kind == 'repaint':
            if self.analyze_btn.isChecked() and self.image:
                self.update_paint(1)
        elif kind == 'analyze':
            self.update_lines()
            self.update_paint(1)
        elif kind == 'background':
            self.update_matrix()
            if self.analyze_btn.isChecked():
                self.update_lines()
                self.update_paint()
            self.update_imag()
            self.update_window()
        else:
            pass
    
    def update_matrix(self):
        try:
            array = io.imread(self.image)
            gray = self.array2gray(array)
            if self.bg_cbox.isChecked() and self.background:
                bg_array = io.imread(self.background)
                bg_gray = self.array2gray(bg_array)
                gray = gray.astype(int)-bg_gray.astype(int)
                gray[gray < 0] = 0
                gray = np.require(gray, np.uint8, 'C')
            gray = 255*transform.rescale(gray, self.scale_factor, mode='nearest')
            self.matrix = np.require(gray, np.uint8, 'C')
        except:
            self.matrix = None
    
    def update_imag(self):
        if self.image:
            pixmap = QtGui.QPixmap.fromImage(self.gray2qimage(self.matrix))
            self.scroll.setWidgetResizable(False)
            self.zoom_sld.setEnabled(True)
            self.parent().fit_to_image_act.setEnabled(True)
            # solve the scrollbar shaken issue [0]
            self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            
            self.lbl.resize(self.lbl.sizeHint())
            self.lbl.setPixmap(pixmap)
        else:
            self.scroll.setWidgetResizable(True)
            self.zoom_sld.setEnabled(False)
            self.parent().fit_to_image_act.setEnabled(False)
            self.lbl.clear()
        self.update_stat()
    
    def update_window(self):
        if self.parent().auto_fit_act.isChecked() and (not self.hold):
            self.fit_to_image()
        # solve the scrollbar shaken issue [1]
        self.scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.lbl.update()
    
    def update_rect(self, factor):
        rect = self.lbl.sel_rect.normalized()
        if not rect.isEmpty():
            x = round(factor*(rect.x()-1)+1)
            y = round(factor*(rect.y()-1)+1)
            w = round(factor*rect.width())
            h = round(factor*rect.height())
            self.lbl.sel_rect = QtCore.QRect(x, y, w, h)
    
    def update_scrollbar(self, factor):
        scrollbar_h = self.scroll.horizontalScrollBar()
        scrollbar_v = self.scroll.verticalScrollBar()
        scrollbar_h.setValue(int(factor*scrollbar_h.value()+\
                (factor-1)*scrollbar_h.pageStep()/2))
        scrollbar_v.setValue(int(factor*scrollbar_v.value()+\
                (factor-1)*scrollbar_v.pageStep()/2))
    
    def update_exp_info(self):
        name = os.path.splitext(os.path.split(self.image)[1])[0]
        self.name_parser(name)
        self.set_background()
        self.update_add()
    
    def update_stat(self):
        for key in self.stat.keys():
            self.stat[key] = ''
        
        if self.image:
            rect = self.lbl.sel_rect.normalized()
            if rect.isEmpty():
                matrix = self.matrix
            else:
                x1 = max(rect.left()-1, 0)
                x2 = rect.right()
                y1 = max(rect.top()-1, 0)
                y2 = rect.bottom()
                matrix = self.matrix[y1:y2, x1:x2]
            if matrix.size:
                self.stat['maximum'] = '{0:d}'.format(np.max(matrix))
                self.stat['minimum'] = '{0:d}'.format(np.min(matrix))
                self.stat['mean'] = '{0:.2f}'.format(np.mean(matrix))
                self.stat['std'] = '{0:.2f}'.format(np.std(matrix))
    
    def update_add(self):
        if self.info['wavelength'] and self.info['reflectivity']:
            self.add_btn.setEnabled(True)
            self.parent().add_act.setEnabled(True)
        else:
            self.add_btn.setEnabled(False)
            self.parent().add_act.setEnabled(False)
        self.update_replace()
    
    def update_replace(self):
        if self.add_btn.isEnabled() and self.restore_btn.isEnabled():
            self.replace_btn.setEnabled(True)
            self.parent().replace_act.setEnabled(True)
        else:
            self.replace_btn.setEnabled(False)
            self.parent().replace_act.setEnabled(False)
    
    def update_export(self):
        if self.table.rowCount():
            self.export_btn.setEnabled(True)
            self.parent().export_act.setEnabled(True)
        else:
            self.export_btn.setEnabled(False)
            self.parent().export_act.setEnabled(False)
    
    def update_paint(self, repaint=0):
        """ Analyze the selected area and update the rects and polygon painted,
            and set the label which displays the reflectivity values.
        
        Keyword arguments:
        repaint -- if 0, this method just update the label drawing contents;
            if 1, this method will repaint the label drawings
        """
        inner_b, self.inner_rect, outer_bs, self.outer_rects, \
                self.edge_points = self.analyze()
        ref_text = ''
        if inner_b != None:
            reflectivity = self.cal_reflectivity(inner_b, outer_bs)
            if reflectivity:
                ref_text = '{0:.2f}'.format(100*reflectivity)
        self.info['reflectivity'] = ref_text
        self.update_add()
        if repaint:
            self.lbl.update()
    
    # TODO: update lines should also change the reflectivity value.
    def update_lines(self, repaint=0):
        """ Analyze the selected area and update the lines painted,
            and set the label which displays the reflectivity values.
        
        Keyword arguments:
        repaint -- if 0, this method just update the label drawing contents;
            if 1, this method will repaint the label drawings
        """
        self.lines = self.get_lines()
        if repaint:
            self.lbl.update()
    
    def update_button(self):
        rows = self.table.selected_rows()
        if len(rows) == 0:
            self.restore_btn.setEnabled(False)
            self.del_btn.setEnabled(False)
            self.parent().restore_act.setEnabled(False)
            self.parent().del_act.setEnabled(False)
        elif len(rows) == 1:
            self.restore_btn.setEnabled(True)
            self.del_btn.setEnabled(True)
            self.parent().restore_act.setEnabled(True)
            self.parent().del_act.setEnabled(True)
        else:
            self.restore_btn.setEnabled(False)
            self.del_btn.setEnabled(True)
            self.parent().restore_act.setEnabled(False)
            self.parent().del_act.setEnabled(True)
        self.update_replace()
        if self.plot.isVisible():
            self.plot.canvas.update_figure()
    
    # window size control methods
    def fit_to_image(self):
        if self.image:
            self.scroll.updateGeometry()
            self.parent().resize(self.sizeHint().boundedTo(self.max_size()))
    
    def max_size(self):
        resolution = QtGui.QDesktopWidget().screenGeometry()
        position = self.mapToGlobal(self.pos())
        w = resolution.width()-position.x()
        h = resolution.height()-position.y()
        return QtCore.QSize(w, h)
    
    # show methods
    def show_paints(self):
        self.update_total('repaint')
    
    def show_others(self):
        self.lbl.update()
    
    # zoom methods
    def set_hold(self):
        self.hold = True
    
    def unset_hold(self):
        self.hold = False
    
    def zoomin(self):
        self.zoom_sld.setValue(self.zoom_sld.value()+1)
    
    def zoomout(self):
        self.zoom_sld.setValue(self.zoom_sld.value()-1)
    
    def normalsize(self):
        if (self.zoom_sld.value() == 7) and self.parent().auto_fit_act.isChecked():
            self.fit_to_image()
        else:
            self.zoom_sld.setValue(7)
    
    def change_zoom(self):
        self.update_total('zoom')
    
    # tooltips control methods
    def show_tool_tips(self):
        self.tooltips = not self.tooltips
        self.lbl.show_pos_tip()


def main():
    app = QtGui.QApplication(sys.argv)
    ex = Main()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()