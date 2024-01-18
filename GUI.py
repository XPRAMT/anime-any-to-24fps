from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import sys
import src
import threading
import queue

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        #初始化變數
        self.filePath = ""
        self.task_num = 0
        # 設定視窗的幾何屬性（位置和大小）
        self.setGeometry(0, 0, 600, 300)
        self.center()
        # 設定視窗的標題
        self.setWindowTitle('移除多餘幀')
        # 建立開始按鈕
        button_star = QPushButton('開始!', self)
        button_star.clicked.connect(self.buttonStarClicked)
        # 建立選擇按鈕
        button_Sel = QPushButton('選擇檔案', self)
        button_Sel.clicked.connect(self.selectFile)
        # 建立任務清單
        self.list_widget = QListWidget()
        # 建立一個垂直佈局管理器，並將按鈕新增至佈局中
        self.vbox = QVBoxLayout()
        #self.vbox.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setLayout(self.vbox)# 將佈局設定為視窗的主佈局
        self.vbox.addWidget(button_Sel)
        self.vbox.addWidget(button_star)
        self.vbox.addWidget(self.list_widget)
        # 添加清單項目
        self.list_widget.addItem('')
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
        current_item = self.list_widget.item(self.task_num)
        if(self.filePath):
            self.SetText(current_item,0,self.filePath)
            # 放進任務序列
            process_queue.put([self.filePath,self.task_num])
            # 重置路徑
            self.filePath=''
            # 建立新的清單
            self.task_num+=1
            self.list_widget.addItem('')
        else:
            current_item.setText('請先選擇檔案')
    # 建立檔案選擇對話框
    def selectFile(self):
        self.filePath,_ = QFileDialog.getOpenFileName(self, 'Select File')
        current_item = self.list_widget.item(self.task_num)
        current_item.setText(f'{self.filePath}')
        if(self.filePath):
           src.GetVideoInfo(self.filePath)
    # 更新狀態  
    def updateChanged(self):
        while (True):
            parameter = state_queue.get() # 等待狀態更新
            self.SetText(self.list_widget.item(parameter[1]),parameter[2],parameter[0])
    # 設定文字
    def SetText(self,item,case,path):
        match case:
            case 0:
                combined_text = path + ' | 等待中...'
                item.setText(combined_text)
                item.setForeground(QColor(255, 0, 0))
            case 1:
                combined_text = path + ' | 處理中...'
                item.setText(combined_text)
                item.setForeground(QColor(255, 255, 0))
            case 2:
                combined_text = path + ' | 完成!'
                item.setText(combined_text)
                item.setForeground(QColor(0, 200, 0))

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



