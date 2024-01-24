from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import threading
import queue
import time
import sys
import src

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        #初始化變數
        self.TaskList = [[0,'path']]
        self.CurTask = 1
        self.CurAdd = 1
        self.isPause = False
        # 設定視窗的幾何屬性（位置和大小）
        self.setGeometry(0, 0, 600, 300)
        self.center()
        # 設定視窗的標題
        self.setWindowTitle('移除多餘幀')
        # 建立一個垂直佈局管理器
        self.vbox = QVBoxLayout()
        self.vbox.setContentsMargins(5, 5, 5, 5)
        self.setLayout(self.vbox)# 將佈局設定為視窗的主佈局
        # 建立選擇按鈕
        button_Sel = QPushButton('選擇檔案', self)
        button_Sel.clicked.connect(self.selectFiles)
        self.vbox.addWidget(button_Sel)
        # 建立一個水平佈局管理器
        self.hbox = QHBoxLayout()
        hbox_container = QWidget()
        hbox_container.setLayout(self.hbox)
        self.hbox.setContentsMargins(0, 0, 0, 0)
        self.vbox.addWidget(hbox_container)
        # 建立停止按鈕
        self.button_stop = QPushButton('停止!', self)
        self.button_stop.clicked.connect(self.buttonStopClicked)
        self.hbox.addWidget(self.button_stop)
        # 建立暫停按鈕
        self.button_pause = QPushButton('暫停', self)
        self.button_pause.clicked.connect(self.buttonPauseClicked)
        self.hbox.addWidget(self.button_pause)
        # 建立開始按鈕
        button_star = QPushButton('開始!', self)
        button_star.clicked.connect(self.buttonStarClicked)
        self.hbox.addWidget(button_star)
        # 建立任務清單
        self.list_widget = QListWidget()
        self.vbox.addWidget(self.list_widget)
        # 建立一個水平佈局管理器
        self.hbox2 = QHBoxLayout()
        self.hbox2.setContentsMargins(0, 0, 0, 0)
        hbox_container2 = QWidget()
        hbox_container2.setLayout(self.hbox2)
        self.vbox.addWidget(hbox_container2)
        # 建立狀態顯示區
        self.status_label = QLabel()
        self.hbox2.addWidget(self.status_label)
        # 建立訊息顯示區
        self.mesg_label = QLabel()
        self.mesg_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.hbox2.addWidget(self.mesg_label)
        self.mesg_label.setText('請選擇或拖放檔案')
        # 計數器
        self.time = [0,10]
        self.mesg_timer= QTimer()
        def reset_mesg():
            self.mesg_label.setText('')
        self.mesg_timer.timeout.connect(reset_mesg)
        # 啟用拖放檔案
        self.setAcceptDrops(True)
        # 更新狀態線程
        t2 = threading.Thread(target=self.updateChanged)
        t2.daemon = True
        t2.start()
    #視窗置中
    def center(self):
            # 取得螢幕的幾何訊息
            screenGeometry = QApplication.primaryScreen().geometry()
            # 計算視窗左上角的座標，使其位於螢幕中心
            x = (screenGeometry.width() - self.width()) // 2
            y = (screenGeometry.height() - self.height()) // 2
            # 設定視窗的位置
            self.setGeometry(x, y, self.width(), self.height())
    # 開始按鈕
    def buttonStarClicked(self):
        if(self.CurTask < len(self.TaskList)):
            # 放進任務序列
            for i in range(self.CurTask, len(self.TaskList)):
                process_queue.put(self.TaskList[i])
                self.SetText(*self.TaskList[i][:2],0)
            self.CurTask = len(self.TaskList)

            self.mesg_label.setText('開始任務!')
            self.mesg_timer.start(2000)
        else:
            self.mesg_label.setText('請先選擇檔案')
            self.mesg_timer.start(2000)
    # 暫停按鈕
    def buttonPauseClicked(self):
        if self.isPause:# 暫停>運作
            self.isPause = False
            src.Pause(self.isPause)
            self.button_pause.setText('暫停')
            self.mesg_label.setText('已恢復')
            self.mesg_timer.start(2000)
        else:# 運作>暫停
            self.isPause = True
            src.Pause(self.isPause)
            self.button_pause.setText('恢復')
            self.mesg_label.setText('已暫停')
            self.mesg_timer.stop()
    # 停止按鈕
    def buttonStopClicked(self):
        self.mesg_timer.start(1000)
        self.time.append(time.time())
        if (self.time[-1] - self.time[-2] < 1):#快速點擊2次
            src.Stop(process_queue,state_queue,False)
            self.mesg_label.setText('再次點擊停止全部任務')
            if (self.time[-1] - self.time[-3] < 2):#快速點擊3次
                if self.isPause:
                    self.buttonPauseClicked()
                src.Stop(process_queue,state_queue,True)
                self.mesg_label.setText('已停止全部任務')
                self.mesg_timer.start(2000)
        else:
            self.mesg_label.setText('再次點擊停止當前任務')

    # 建立檔案選擇對話框
    def selectFiles(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, 'Select Files')
        for file_path in file_paths:
            self.AddItem(file_path)
    # 判斷文件是否含有URL
    def dragEnterEvent(self, event: QDragEnterEvent):
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            event.acceptProposedAction()
    # 放置檔案
    def dropEvent(self,  event:QDropEvent):
        mime_data = event.mimeData()
        # 取得拖放的檔案路徑
        if mime_data.hasUrls():
            for url in mime_data.urls():
                self.AddItem(url.toLocalFile())
    # 添加項目
    def AddItem(self,filePath):
        if(filePath):
            self.TaskList.append([self.CurAdd,filePath]) #num,path
            self.list_widget.addItem('.'.join(map(str, self.TaskList[self.CurAdd])))
            self.CurAdd += 1
            print(filePath)

    # 更新狀態  
    def updateChanged(self):
        while (True):
            parameter = state_queue.get() # 等待狀態更新
            self.SetText(*parameter[:3])
    # 設定文字
    def SetText(self,task_num,text,case):
        if task_num!= None:
            item = self.list_widget.item(task_num-1)
        match case:
            case 0:
                item.setText(f'{task_num}.{text} | 等待中...')
                item.setForeground(QColor(255, 0, 0))
            case 1:
                item.setText(f'{task_num}.{text} | 處理中...')
                item.setForeground(QColor(255, 255, 0))
            case 2:
                item.setText(f'{task_num}.{text} | 完成!')
                item.setForeground(QColor(0, 200, 0))
            case 3:
                self.status_label.setText(text)

# 當腳本作為主程式執行時
if __name__ == '__main__':
    process_queue = queue.Queue() # 任務
    state_queue = queue.Queue()   # 狀態
    # 建立線程
    t = threading.Thread(target=src.Main,args=(process_queue,state_queue,))
    t.daemon = True 
    t.start()
    # 建立GUI
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    # 設定深色主題
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(20, 20, 20))
    app.setPalette(dark_palette)
    # 設定字體
    default_font = QFont('Microsoft JhengHei',12)
    app.setFont(default_font)
    # 建立 MyWindow 實例
    window = MyWindow()
    # 顯示視窗
    window.show()
    # 運行應用程式的主循環
    sys.exit(app.exec())



