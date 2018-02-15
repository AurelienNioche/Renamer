import sys
import os
import threading
from shutil import copyfile

from PyQt5 import QtWidgets
from PyQt5 import QtCore


class Communicate(QtCore.QObject):

    """
    Communication between
    GUI and
    Converter component

    """

    done = QtCore.pyqtSignal()
    wait = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal()
    update_prog = QtCore.pyqtSignal(int)


class RenamerWindow(QtWidgets.QWidget):

    """
    Gui component

    """

    def __init__(self):

        super().__init__()

        self.dir_path = None
        self.renamer = None

        self.communicate = Communicate()
        self.communicate.wait.connect(self.wait)
        self.communicate.done.connect(self.done)
        self.communicate.error.connect(self.error)
        self.communicate.update_prog.connect(self.update_prog)

        self.prog = QtWidgets.QProgressBar(self)
        self.logs = QtWidgets.QTextEdit(self)
        self.logs.setReadOnly(True)

        self.layout = QtWidgets.QGridLayout(self)

        self.layout.addWidget(self.prog)
        self.layout.addWidget(self.logs)

        self.is_closing = False

        self.init()

    def init(self):

        self.set_dir_path()

        self.init_renamer()

        self.init_UI()

        self.rename_data()

    def init_renamer(self):

        self.renamer = Renamer(
            dir_path=self.dir_path,
            ui=self
        )

    def init_UI(self):

        self.prog.setValue(0)

        self.logs.append(
            "Selected folder for renaming is '{dir_path:}'."
            "\nFolder for renamed files will be '{save_path:}'.".format(
                dir_path=self.dir_path,
                save_path=self.renamer.save_path
            )
        )

        self.setWindowTitle("Renamer")
        self.show()

    def set_dir_path(self):

        directory = os.getenv("HOME")

        dir_path = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            'Select folder',
            directory,
        )

        if dir_path:
            self.dir_path = dir_path

        else:
            self.close()

    def rename_data(self):

        self.renamer.start()

    def done(self):

        self.prog.setValue(100)
        self.logs.append("Done!")

    def wait(self):

        self.logs.append("Renaming please wait...")

    def update_prog(self, x):

        self.prog.setValue(x)

    def closeEvent(self, event):

        print("Closing app...")
        self.is_closing = True

        if self.renamer is not None:
            self.renamer.stop()

        super().closeEvent(event)
        sys.exit()

    @staticmethod
    def error():

        msgbox = QtWidgets.QMessageBox()
        msgbox.setIcon(QtWidgets.QMessageBox.Critical)
        msgbox.setWindowTitle("Error")
        msgbox.setText("Something went wrong!")
        close = msgbox.addButton("Close", QtWidgets.QMessageBox.ActionRole)

        msgbox.exec_()

        if msgbox.clickedButton() == close:
            sys.exit()


class Renamer(threading.Thread):

    """

    Renamer

    """

    dic_num = {
        "1": "1_1",
        "2": "1_2",
        "3": "1_3",
        "4": "2_1",
        "5": "2_2",
        "6": "2_3",
        "7": "3_1",
        "8": "3_2",
        "9": "3_3",
    }

    dic_color = {
        "GREEN": "1",
        "RED": "2",
        "MASKG": "3",
        "MASKR": "4",
        "MASKO": "5"
    }

    def __init__(self, dir_path, ui):

        super().__init__()

        self.dir_path = dir_path
        self.ui = ui

        self.save_path = self.get_save_path()

        self._stopped = False

    def run(self):

        """
        main method

        """

        try:

            file_list = os.listdir(self.dir_path)
            n = len(file_list)

            for i, filename in enumerate(file_list):

                if not self._stopped:

                    new_filename = self.replace(filename)

                    if new_filename is not None:
                        copyfile(os.path.join(self.dir_path, filename), os.path.join(self.save_path, new_filename))

                    self.ui.communicate.update_prog.emit(int(i/n * 100))

            if not self._stopped:
                self.ui.communicate.done.emit()

        except:
            self.ui.communicate.error.emit()

    def replace(self, filename):

        """
        :param filename: string as 'FFI-129 TopHat GREEN_E3_5_00d00h00m'
        :return: string as '129_1_E_03_2_2'
        """

        if filename.startswith("FFI-"):

            first, second, third, fourth = filename.split("_")

            first_1, first_2, first_3 = first.split(" ")

            # Remove 'FFI-'
            first_1 = first_1.split("-")[-1]

            # Replace ('green', 'red', ... ) by ('1', '2', '3')
            for i in self.dic_color.keys():
                if first_3 == i:
                    first_3 = self.dic_color[i]
                    break

            # Add filling zeros for '[A-H]1'
            second_1, second_2 = second[0], second[1:]
            second_2 = second_2.zfill(2)

            third = self.dic_num[third]

            # Change numbering
            new = first_1 + "_" + first_3 + "_" + second_1 + "_" + second_2 + "_" + third

            return new

        else:
            return None

    def get_save_path(self):

        save_path = self.dir_path + "_new"
        os.makedirs(save_path, exist_ok=True)

        return save_path

    def stop(self):
        self._stopped = True


if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)
    win = RenamerWindow()
    win.setGeometry(100, 200, 800, 300)
    sys.exit(app.exec_())
