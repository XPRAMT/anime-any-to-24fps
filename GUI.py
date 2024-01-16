from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *
import sys
import src

class MyWindow(QWidget):
    def __init__(self):
        super().__init__()
        #初始化變數
        self.filePath = ""
        # 初始化視窗介面
        self.initUI()

    def initUI(self):
        # 建立開始按鈕
        button_star = QPushButton('開始!', self)
        button_star.clicked.connect(self.buttonStarClicked)
        # 建立選擇按鈕
        button_Sel = QPushButton('選擇檔案', self)
        button_Sel.clicked.connect(self.selectFile)
        # 建立文字框
        self.label = QLabel()
        # 建立一個垂直佈局管理器，並將按鈕新增至佈局中
        vbox = QVBoxLayout()
        vbox.addWidget(button_Sel)
        vbox.addWidget(button_star)
        vbox.addWidget(self.label)
        # 將佈局設定為視窗的主佈局
        self.setLayout(vbox)
        # 設定視窗的幾何屬性（位置和大小）
        self.setGeometry(0, 0, 600, 300)
        self.center()
        # 設定視窗的標題
        self.setWindowTitle('移除多餘幀')

    def center(self):
            # 取得螢幕的幾何訊息
            screenGeometry = QApplication.primaryScreen().geometry()
            # 計算視窗左上角的座標，使其位於螢幕中心
            x = (screenGeometry.width() - self.width()) // 2
            y = (screenGeometry.height() - self.height()) // 2
            # 設定視窗的位置
            self.setGeometry(x, y, self.width(), self.height())

    # 自訂的按鈕點擊事件處理方法
    def buttonStarClicked(self):
        src.Main(self.filePath)
        #self.label.setText(f'<p style="color:white;">處理中</p>')
        
    def selectFolder(self):# 建立資料夾選擇對話框
        self.folder_path = QFileDialog.getExistingDirectory(self, 'Select Folder')
        self.label.setText(f'<p style="color:white;">folder path:{self.folder_path}</p>')
    
    def selectFile(self):# 建立檔案選擇對話框
        self.filePath,_ = QFileDialog.getOpenFileName(self, 'Select File')
        self.label.setText(f'<p style="color:white;">file path:{self.filePath}</p>')
        if(self.filePath):
            src.GetVideoInfo(self.filePath)


# 當腳本作為主程式執行時
if __name__ == '__main__':
    # 建立 QApplication 實例
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    dark_palette = QPalette()
    dark_palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0))
    dark_palette.setColor(QPalette.ColorRole.Button, QColor(20, 20, 20))
    app.setPalette(dark_palette)
    # 建立 MyWindow 實例
    window = MyWindow()
    # 顯示視窗
    window.show()
    # 運行應用程式的主循環
    sys.exit(app.exec())
























