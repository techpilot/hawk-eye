from __future__ import absolute_import, division, print_function

from functools import partial
from typing import Dict, List, Any
from collections import OrderedDict
import numpy as np
import cv2
import os

from PyQt5.QtWidgets import (QWidget, QDialog, QLabel, QGridLayout, QBoxLayout, QSizePolicy, QApplication, QVBoxLayout,
                             QPushButton)
from PyQt5.QtCore import (QThread, pyqtSignal, pyqtSlot, QSize, Qt, QTimer, QTime, QDate, QObject, QEvent)
from PyQt5.QtGui import (QImage, QPixmap, QFont, QIcon)

from Motion.main import de_main
from alarm import alarm

os.environ['OPENCV_VIDEOIO_DEBUG'] = '1'
os.environ['OPENCV_VIDEOIO_PRIORITY_MSMF'] = '0'

width, height = 480 * 6, 270 * 6
w = 1920 // 2
h = 1080 // 2
capture_delay = 10


class Slot(QThread):
    signal = pyqtSignal(np.ndarray, int, int, bool)

    def __init__(self, parent: QWidget, index: int, cam_id: int, link: str) -> None:
        QThread.__init__(self, parent)
        self.parent = parent
        self.index = index
        self.cam_id = cam_id
        self.link = link

    def run(self) -> None:
        cap = cv2.VideoCapture(self.link)

        while cap.isOpened():
            # print("CAP", cap)
            has, im = cap.read()
            has, im2 = cap.read()
            if not has:
                break

            diff = cv2.absdiff(im, im2)

            gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            blur = cv2.GaussianBlur(gray, (5, 5), 0)

            _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
            # used to get a bi-level (binary) image out of a grayscale image

            dilated = cv2.dilate(thresh, None, iterations=3)
            contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours:
                (x, y, d, e) = cv2.boundingRect(contour)

                if cv2.contourArea(contour) < 900:
                    continue
                # cv2.rectangle(im, (x, y), (x + d, y + e), (0, 255, 0), 2)
                cv2.putText(im, "Status: {}".format('Movement'), (10, 20), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (0, 0, 255), 2)
                # cv2.drawContours(im, contours, -1, (0, 0, 255), 2)

            im = cv2.resize(im, (w, h))
            self.signal.emit(im, self.index, self.cam_id, True)
            cv2.waitKey(capture_delay) & 0xFF

        im = np.zeros((h, w, 3))  # dtype=np.unit8
        self.signal.emit(im, self.index, self.cam_id, False)
        cv2.waitKey(capture_delay) & 0xFF


def clickable(widget):
    class Filter(QObject):
        clicked = pyqtSignal()

        def eventFilter(self, obj, event):
            if obj == widget:
                if event.type() == QEvent.MouseButtonRelease:
                    self.clicked.emit()
                    return True
            return False

    filter_ = Filter(widget)
    widget.installEventFilter(filter_)
    return filter_.clicked


class NewWindow(QDialog):
    def __init__(self, parent: QWidget) -> None:
        QDialog.__init__(self, parent)
        self.parent = parent
        self.index: int = 0
        self.link = 0
        self.slot = Slot.run

        self.emailBTN = QPushButton("Send Email")
        self.emailBTN.clicked.connect(self.send_email)

        self.alarmBTN = QPushButton("Alarm")
        self.alarmBTN.clicked.connect(self.sound_alarm)

        self.label = QLabel()
        self.label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.label.setScaledContents(True)
        self.label.setFont(QFont("Times", 30))
        self.label.setStyleSheet(
            "color: rgb(255, 0, 0);"
            "background-color: rgb(0, 0, 0);"
            "qproperty-alignment: AlignCenter;"
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        # layout.setSpacing(2)

        layout.addWidget(self.label)
        layout.addWidget(self.emailBTN)
        layout.addWidget(self.alarmBTN)

        self.setLayout(layout)
        self.setWindowTitle('Hawkeye {}'.format(self.index))

    def send_email(self):
        de_main(0)

    def sound_alarm(self):
        # alarm(self.slot.cap)
        print(self.slot)

    def sizeHint(self) -> QSize:
        return QSize(width // 3, height // 3)

    def resizeEvent(self, event) -> None:
        self.update()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            self.accept()


class Window(QWidget):
    def __init__(self, cams: Dict[int, str]) -> None:
        super(Window, self).__init__()

        # initialize the cameras with empty  values
        self.cameras: Dict[int, List[Any]] = OrderedDict()
        index: int
        for index in range(len(cams.keys())):
            #            index      id   link  active
            self.cameras[index] = [None, None, False]

        index = 0
        for cam_id, link in cams.items():
            #            index      id     link  active
            self.cameras[index] = [cam_id, link, False]
            index += 1

        # main layout
        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self.labels: List[QLabel] = []
        self.threads: List[Slot] = []
        # self.dialogs: List[NewWindow] = []
        for index, value in self.cameras.items():
            cam_id, link, active = value

            # thread
            slot = Slot(self, index, cam_id, link)
            slot.signal.connect(self.ReadImage)
            self.threads.append(slot)

            # screen
            label = QLabel()
            label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            label.setScaledContents(True)
            label.setFont(QFont("Times", 30))
            label.setStyleSheet(
                "color: rgb(255, 0, 255); background-color: rgb(0, 0, 0);"
                "qproperty-alignment: AlignCenter;"
            )

            clickable(label).connect(partial(self.showCam, index))
            self.labels.append(label)

            if index == 0:
                layout.addWidget(label, 0, 0)  # row1, col1
            elif index == 1:
                layout.addWidget(label, 0, 1)  # row1, col2
            elif index == 2:
                layout.addWidget(label, 0, 2)  # row1, col3
            elif index == 3:
                layout.addWidget(label, 0, 3)  # row1, col4

            elif index == 4:
                layout.addWidget(label, 1, 0)  # row2, col1
            elif index == 5:
                layout.addWidget(label, 1, 1)  # row2, col2
            elif index == 6:
                layout.addWidget(label, 1, 2)  # row2, col3
            elif index == 7:
                layout.addWidget(label, 1, 3)  # row2, col4

            elif index == 8:
                layout.addWidget(label, 2, 0)  # row3, col1
            elif index == 9:
                layout.addWidget(label, 2, 1)  # row3, col2
            elif index == 10:
                layout.addWidget(label, 2, 2)  # row3, col3
            elif index == 11:
                layout.addWidget(label, 2, 3)  # row3, col4

            elif index == 12:
                layout.addWidget(label, 3, 0)  # row4, col1
            elif index == 13:
                layout.addWidget(label, 3, 1)  # row4, col2
            elif index == 14:
                layout.addWidget(label, 3, 2)  # row4, col3
            elif index == 15:
                layout.addWidget(label, 3, 3)  # row4, col4
            else:
                raise ValueError("n Camera != rows/cols")

        #  Timer Screen
        timer = QTimer(self)
        timer.timeout.connect(self.showTime)
        timer.start(1000)
        self.showTime()

        # Timer auto restart threads( restarts every 3 hours)
        timer_th = QTimer(self)
        timer_th.timeout.connect(self.refresh)
        timer_th.start(6000 * 60 * 3)

        self.setLayout(layout)
        self.setWindowTitle('hawkeyes')

        # cam_id, link, active = self.cameras[index]

        self.newWindow = NewWindow(self)
        self.refresh()

    def sizeHint(self) -> QSize:
        return QSize(width, height)

    def resizeEvent(self, event) -> None:
        self.update()

    def keyPressEvent(self, event) -> None:
        if event.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        pass

    def showCam(self, index: Any) -> None:
        self.newWindow.index = index
        if not self.cameras[index][2]:
            text_ = "Hawkeye {}\nNot active".format(self.cameras[index][0])
            self.newWindow.label.setText(text_)
        self.newWindow.setWindowTitle('Hawkeye {}'.format(self.cameras[index][0]))
        self.newWindow.show()

    def showTime(self) -> None:
        time = QTime.currentTime()
        textTime = time.toString('hh:mm:ss')
        date = QDate.currentDate()
        textDate = date.toString('ddd, MMMM d')

        text = "{}\n{}".format(textTime, textDate)

        for index, value in self.cameras.items():
            cam_id, link, active = value
            if not active:
                text_ = "Hawkeye{}\n".format(cam_id) + text
                self.labels[index].setText(text_)

    @pyqtSlot(np.ndarray, int, int, bool)
    def ReadImage(self, im: np.ndarray, index: int, cam_id: int, active: bool) -> None:
        self.cameras[index][2] = active
        cam_id, link, active = self.cameras[index]
        # print("Link", link)

        im = QImage(im.data, im.shape[1], im.shape[0], QImage.Format_RGB888).rgbSwapped()
        self.labels[index].setPixmap(QPixmap.fromImage(im))

        if index == self.newWindow.index:
            self.newWindow.label.setPixmap(QPixmap.fromImage(im))
            self.newWindow.link = link

    def refresh(self) -> None:
        for slot in self.threads:
            slot.start()


if __name__ == '__main__':
    import sys

    cams: Dict[int, Any] = OrderedDict()

    cams[1] = 0
    cams[2] = "videos/mardi.mp4"
    cams[3] = "videos/vid1.mp4"
    cams[4] = "videos/videvo.mp4"
    cams[5] = "videos/video.mp4"
    cams[6] = "videos/subway.mp4"
    cams[7] = "videos/videvo.mp4"
    cams[8] = "videos/Caltrans.mp4"
    cams[9] = "videos/vid2.avi"
    cams[10] = "videos/nasa.mp4"
    cams[11] = "videos/Caltrans.mp4"
    cams[12] = "videos/mardi.mp4"
    cams[13] = "videos/videvo.mp4"
    cams[14] = "videos/Caltrans.mp4"
    cams[15] = "videos/subway.mp4"
    cams[16] = "videos/video.mp4"

    app = QApplication(sys.argv)
    win = Window(cams=cams)
    win.show()
    sys.exit(app.exec_())
