import sys, os
import json
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QVariant, QTimer

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

jsonPath = ""
if getattr(sys, 'frozen', False):
    jsonPath = resource_path("codeList.json")
else :
    jsonPath = 'codeList.json'
    
with open(jsonPath, 'r', encoding='utf-8') as file:
    data = json.load(file)
    
class AutoTrWin(QWidget):
    resultRow = 0
    resultCol = 0
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Dynamic QWidget Example')
        self.mainWidget = QWidget(self)
        self.mainLayout = QVBoxLayout(self.mainWidget)
        
        self.inputbox = QLineEdit()
        self.inputbox.textChanged.connect(self.sortout)
        
        searchLayout = QHBoxLayout() # QWidget(target)
        searchLayout.addWidget(self.inputbox)
        
        self.resultLayout = QGridLayout()
        self.stepLayout = QVBoxLayout()
        
        self.mainLayout.addLayout(searchLayout) #종목명입력란
        self.mainLayout.addLayout(self.resultLayout) #검색결과 표시
        self.mainLayout.addLayout(self.stepLayout) #거래방식 입력란
        
        self.mainWidget.setLayout(self.mainLayout)
        self.mainWidget.setMinimumHeight(100)
        self.mainWidget.setMinimumWidth(400)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.typingTimeout)
        self.timer.setInterval(500)

        # List to store dynamically created widgets
        self.dynamic_widgets = []
        
        
    def sortout(self):
        text = self.inputbox.text().upper()
        typeLen = len(text)
        if typeLen >= 2 :
            self.timer.start()
            filtered_data = [item for item in data if item["name"].find(text) != -1] # string.find(txt) == -1이면 해당 텍스트 없음
            if(len(filtered_data) > 10) :
                filtered_data = filtered_data[:10]
            
            if len(filtered_data) > 0 :
                self.showResult(filtered_data)
            print(f"{text} 검색결과 : {filtered_data}")
            # widget.setParent(None)
        else :
            self.clearResult()
    
    def showResult(self, data):
        self.clearResult()
        #self.resultLayout에 검색결과를 "새롭게" 붙여야 한다.
        print(f"버튼붙이기 : {data}")
        if len(data) > 0:
            for idx, object in enumerate(data):
                stockName = object['name']
                btn = QPushButton(stockName)
                btn.clicked.connect(self.stockChoice)
                self.resultLayout.addWidget(btn, self.resultRow, self.resultCol)
                self.resultCol = self.resultCol + 1
                if self.resultCol >= 5 :
                    self.resultCol = 0
                    self.resultRow = self.resultRow + 1
            print(f"row: {self.resultRow} col: {self.resultCol}")
    def clearResult(self) :
        gridLen = self.resultLayout.count()
        if gridLen > 0 :
            for i in range(gridLen):
                item = self.resultLayout.itemAt(i)
                if item is not None:
                    widget = item.widget()
                    widget.deleteLater()
        self.resultRow = 0
        self.resultCol = 0
        
    def stockChoice(self):
        chooseItem = self.sender().text()
        filtered_data = [item for item in data if item["name"] == chooseItem] # string.find(txt) == -1이면 해당 텍스트 없음
        print(f"[stockChoice] {chooseItem}({filtered_data[0]['code']})")
        
    def typingTimeout(self): #타이머가 멈출때 enter키를 누른것과 동일한 효과가 발생한다.
        self.timer.stop()  # Stop the timer
        # text = self.inputbox.text()
        # # print(f"Text changed: {text}. Simulating Enter key press.")
        
    def add_dynamic_widget(self):
        new_widget = QWidget(self)
        new_widget.setWindowTitle(f'Dynamic Widget {len(self.dynamic_widgets) + 1}')

        # Add the new widget to the layout
        self.layout().insertWidget(self.layout().count() - 1, new_widget)

        # Store the widget reference for future removal
        self.dynamic_widgets.append(new_widget)

    def remove_last_widget(self):
        if self.dynamic_widgets:
            last_widget = self.dynamic_widgets.pop()
            last_widget.deleteLater()  # Remove the widget from the layout and delete it

def main():
    app = QApplication(sys.argv)
    example = AutoTrWin()
    example.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
