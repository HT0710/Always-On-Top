import sys
import keyboard as kb
import win32gui
import pygetwindow
from PyQt5 import QtWidgets, QtGui
from win32gui import GetWindowText, GetForegroundWindow
from PyQt5.QtCore import QThread, pyqtSignal


class AOT(QThread):
	update_process = pyqtSignal()

	def __init__(self, parent=None):
		QThread.__init__(self, parent=parent)
		self.continue_run = True
		self.__on_top = False
		self.__keyboard_shortcut = {
			'start': 'ctrl+alt+up',
			'stop': 'ctrl+alt+down',
			'end': 'ctrl+alt+end'
		}
		self.__window_name = ''
		self.__window_id = 0

	def run(self):
		while self.continue_run:
			state = self.__wait_for_input()
			if (self.__on_top is False) and (state == 'start'):
				self.__start()
			elif (self.__on_top is True) and (state == 'stop'):
				self.__stop()
			elif state == 'end':
				if self.__on_top is True:
					self.__stop()
				self.continue_run = False
		self.update_process.emit()

	def __wait_for_input(self):
		key = kb.read_hotkey(False)
		for state, shortcut in self.__keyboard_shortcut.items():
			if key == shortcut:
				return state

	@staticmethod
	def __get_window(window_name):
		window_list = []
		win32gui.EnumWindows(lambda hwnd, window_list: window_list.append((win32gui.GetWindowText(hwnd), hwnd)), window_list)
		cmd_window = [i for i in window_list if window_name in i[0]]
		return cmd_window[0][1]

	@staticmethod
	def __get_window_size(window_name):
		window = pygetwindow.getWindowsWithTitle(window_name)[0]
		x, y = window.topleft
		w = window.width
		h = window.height
		return x, y, w, h

	def __start(self):
		self.__window_name = GetWindowText(GetForegroundWindow())
		self.__window_id = self.__get_window(self.__window_name)
		x, y, w, h = self.__get_window_size(self.__window_name)
		win32gui.SetWindowPos(self.__window_id, -1, x, y, w, h, 0)
		self.__on_top = True

	def __stop(self):
		self.__window_id = self.__get_window(self.__window_name)
		x, y, w, h = self.__get_window_size(self.__window_name)
		win32gui.SetWindowPos(self.__window_id, -2, x, y, w, h, 0)
		self.__on_top = False


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
	def __init__(self, icon, parent=None):
		super().__init__(icon, parent)
		self.on_tray(parent)

	def double_click(self, reason):
		if reason == self.DoubleClick:
			self.shortcut()

	def on_tray(self, parent):
		self.setToolTip('Always On Top')
		menu = QtWidgets.QMenu(parent)
		open_app = menu.addAction("Shortcut")
		open_app.triggered.connect(self.shortcut)
		menu.addSeparator()
		exit_ = menu.addAction("Exit")
		exit_.triggered.connect(sys.exit)
		menu.addSeparator()
		self.setContextMenu(menu)
		self.activated.connect(self.double_click)

		self.worker = AOT()
		self.worker.start()
		self.worker.update_process.connect(sys.exit)

		self.show()
		self.showMessage('Always On Top', 'Open tray icon to change shortcut')

	@staticmethod
	def shortcut():
		pass


if __name__ == '__main__':
	app = QtWidgets.QApplication(sys.argv)
	wg = QtWidgets.QWidget()
	SystemTrayIcon(QtGui.QIcon("icon.png"), wg)
	sys.exit(app.exec_())
