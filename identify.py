from UI import  Ui_MainWindow
import sys
from PySide2 import QtCore,QtGui,QtWidgets
from PySide2.QtWidgets import QApplication,QMainWindow
from PySide2.QtCore import QTimer
from PySide2.QtGui import QImage, QPixmap
from PySide2.QtCore import QCoreApplication
from imutils.perspective import four_point_transform
from imutils import contours
import imutils
import cv2
import numpy as np

import xlwt
import matplotlib.pyplot as plt


class CamShow(QMainWindow,Ui_MainWindow):
    def __init__(self,parent=None):
        super(CamShow,self).__init__(parent)
        self.setupUi(self)
        self.timer_camera = QTimer()
        self.cap = cv2.VideoCapture()
        self.init_excel()
        self.slot_init()
        self.parameter_init()


    def init_excel(self):
        self.workbook = xlwt.Workbook(encoding=ascii)
        self.worksheet = self.workbook.add_sheet('current records')
        self.row = 0

    def slot_init(self):
        # 定时器让其定时读取显示图片
        self.timer_camera.timeout.connect(self.show_camera)
        # 打开摄像头
        self.pushButton.clicked.connect(self.button_open_camera_click)
        self.pushButton_2.clicked.connect(self.start)
        self.pushButton_3.clicked.connect(self.plot)

    def parameter_init(self):
        self.CAM_NUM = 0
        self.FLAG = 0
        self.records = []
        self.DIGITS_LOOKUP = {
            (1, 1, 1, 0, 1, 1, 1): 0,
            (0, 0, 1, 0, 0, 1, 0): 1,
            (1, 0, 1, 1, 1, 0, 1): 2,
            (1, 0, 1, 1, 0, 1, 1): 3,
            (0, 1, 1, 1, 0, 1, 0): 4,
            (1, 1, 0, 1, 0, 1, 1): 5,
            (1, 1, 0, 1, 1, 1, 1): 6,
            (1, 0, 1, 0, 0, 1, 0): 7,
            (1, 1, 1, 1, 1, 1, 1): 8,
            (1, 1, 1, 1, 0, 1, 1): 9
        }

    def button_open_camera_click(self):
        if self.timer_camera.isActive() == False:
            flag = self.cap.open(self.CAM_NUM)
            if flag == False:
                msg = QtWidgets.QMessageBox.Warning(self, u'Warning', u'请检测相机与电脑是否连接正确',
                                                            buttons=QtWidgets.QMessageBox.Ok,
                                                            defaultButton=QtWidgets.QMessageBox.Ok)
                # if msg==QtGui.QMessageBox.Cancel:
                #                     pass
            else:
                self.timer_camera.start(1000)
                self.pushButton.setText(u'close')
        else:
            self.timer_camera.stop()
            self.cap.release()
            self.label.clear()
            self.label_2.clear()
            self.label_5.clear()
            # self.label_2.clear()
            self.workbook.save('current.xls')
            print(self.records)
            self.pushButton.setText(u'open')

    def show_camera(self):
        flag, self.image = self.cap.read()
        show = cv2.resize(self.image, (640, 480))
        # opencv格式不能直接显示，需要用下面代码转换一下
        show = cv2.cvtColor(show, cv2.COLOR_BGR2RGB)
        showImage = QtGui.QImage(show.data, show.shape[1], show.shape[0], QtGui.QImage.Format_RGB888)
        self.label.setPixmap(QtGui.QPixmap.fromImage(showImage))

        if self.FLAG == 1 :
            gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edged = cv2.Canny(blurred, 128, 200)
            cnts, hi = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # the largest contour(default: target) is in the first place after sorting
            cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
            displayCnt = None
            for c in cnts:
                # approximate the contour
                peri = cv2.arcLength(c, True)
                approx = cv2.approxPolyDP(c, 0.02 * peri, True)
                # if the contour has four vertices, then we have found
                # the thermostat display
                if len(approx) == 4:
                    displayCnt = approx
                    break
            warped = four_point_transform(gray, displayCnt.reshape(4, 2))
            thresh = cv2.threshold(warped, 0, 255,
                                   cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (1, 5))
            thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, 2)
            show1 = cv2.resize(thresh, (280,190))

            print("thresh",thresh.shape)
            ROI = show1.copy()[37:185,17:246]

            show1 = cv2.cvtColor(show1, cv2.COLOR_BGR2RGB)
            showImage1 = QtGui.QImage(show1.data, show1.shape[1], show1.shape[0], QtGui.QImage.Format_RGB888)
            self.label_2.setPixmap(QtGui.QPixmap.fromImage(showImage1))

            print(ROI.shape)
            where_0 = np.where(ROI == 0)
            where_255 = np.where(ROI == 255)
            ROI[where_0] = 255
            ROI[where_255] = 0
            rows, cols = ROI.shape
            ver_list = [0] * cols
            for j in range(cols):
                for i in range(rows):
                    if ROI.item(i, j) == 0:
                        ver_list[j] = ver_list[j] + 1
            '''
            对ver_list中的元素进行筛选，可以去除一些噪点qq
            '''
            ver_arr = np.array(ver_list)
            ver_arr[np.where(ver_arr < 1)] = 0
            ver_list = ver_arr.tolist()
            # 绘制垂直投影
            img_white = np.ones(shape=(rows, cols), dtype=np.uint8) * 255
            for j in range(cols):
                pt1 = (j, rows - 1)
                pt2 = (j, rows - 1 - ver_list[j])
                cv2.line(img_white, pt1, pt2, (0,), 1)
            cv2.imshow('垂直投影', img_white)

            digits = []

            #切割单一字符
            vv_list = self.get_vvList(ver_list)
            for i in vv_list:
                img_ver = ROI.copy()[:, i[0]:i[-1]]
                where_0 = np.where(img_ver == 0)
                where_255 = np.where(img_ver == 255)
                img_ver[where_0] = 255
                img_ver[where_255] = 0
                (roiH, roiW) = img_ver.shape
                (dW, dH) = (int(roiW * 0.3), int(roiH * 0.1))
                dHC = int(roiH * 0.05)
                # define the set of 7 segments
                segments = [
                    ((0, 0), (roiW, dH)),  # top
                    ((0, 0), (dW, roiH // 2)),  # top-left
                    ((roiW - dW, 0), (roiW, roiH // 2)),  # top-right
                    ((0, (roiH // 2) - dHC), (roiW, (roiH // 2) + dHC)),  # center
                    ((0, roiH // 2), (dW, roiH)),  # bottom-left
                    ((roiW - dW, roiH // 2), (roiW, roiH)),  # bottom-right
                    ((0, roiH - dH), (roiW, roiH))  # bottom
                ]
                on = [0] * len(segments)
                # loop over the segments
                for (i, ((xA, yA), (xB, yB))) in enumerate(segments):
                    # extract the segment ROI, count the total number of
                    # thresholded pixels in the segment, and then compute
                    # the area of the segment
                    segROI = img_ver[yA:yB, xA:xB]
                    total = cv2.countNonZero(segROI)
                    area = (xB - xA) * (yB - yA)
                    # if the total number of non-zero pixels is greater than
                    # 50% of the area, mark the segment as "on"
                    proportion = total / float(area)
                    print(proportion)
                    if proportion > 0.35:
                        on[i] = 1
                # lookup the digit and draw it on the image
                # special: digit = 1
                print(" ")
                if roiH > 5 * roiW:
                    digit = 1
                else:
                    digit = self.DIGITS_LOOKUP[tuple(on)]
                digits.append(digit)

            current = digits[0] * 10.0 + digits[1] * 1.0 + digits[2] * 0.1 + digits[3] * 0.01
            a = int(current * 100)
            b = a/100
            # current = int(current)
            print("b",b)
            print(current)
            num = str(digits[0]) + str(digits[1]) + "." +str(digits[2]) + str(digits[3]) +"mA"
            self.label_5.setText(QCoreApplication.translate("MainWindow", num, None))
            self.records.append(current)
            self.worksheet.write(self.row,0,current)
            self.row = self.row + 1

    def start(self):
        if self.FLAG == 0:
            self.FLAG = 1
            self.pushButton_2.setText(u'stop')
        else:
            self.FLAG = 0
            self.pushButton_2.setText(u'start')
    def plot(self):
        x_data = list(range(len(self.records)))
        y_data = self.records
        plt.plot(x_data, y_data, 'bo-', linewidth=1)
        plt.title('current records')
        plt.legend()
        plt.xlabel('time/s')
        plt.ylabel('current/mA')

        plt.show()
    def get_vvList(self,list_data):
        #取出list中像素存在的区间
        vv_list=list()
        v_list=list()
        for index,i in enumerate(list_data):
            if i>0:
                v_list.append(index)
            else:
                if v_list:
                    vv_list.append(v_list)
                    #list的clear与[]有区别
                    v_list=[]
        return vv_list

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui=CamShow()
    ui.show()
    sys.exit(app.exec_())
