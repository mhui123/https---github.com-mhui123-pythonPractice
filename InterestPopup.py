import sys, os
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QVariant, QEvent
from JsonControl import *
from TableControl import *

fileNm = "interestList"

class InterestPopup(QMainWindow):
    listData = None
    selectedNm = None
    def __init__(self):
        super().__init__()
        # btn = QPushButton("test", self)
        # btn.clicked.connect(self.test)
        
        self.readList()
        self.initUi()    
        self.gridList()
    
    def initUi(self):
        layout = QGridLayout(self)
        label = QLabel('<font size="4"><b>관심종목</b></font>')
        layout.addWidget(label, 0, 0)
        
        self.interList = QTableWidget()
        self.interList.setColumnCount(5)
        setTbStyle(self.interList)
        tbHeaders = ['종목명', '현재가', '거래량', '변동', '등락률']
        setTbHeader(self.interList, tbHeaders)
        layout.addWidget(self.interList, 1, 0)
        
        central_widget = QWidget()  # Create a central widget
        central_widget.setLayout(layout)  # Set the layout for the central widget
        self.setCentralWidget(central_widget)  
        
        #화면에 표현하려면 widget에 layout을 붙인 후 해당 widget을 추가해주는 것으로 처리함.
        
    def contextMenuEvent(self, event):
        pos = self.interList.viewport().mapFromGlobal(event.globalPos()) # 전역 좌표에서 시작된 마우스 이벤트의 위치를 QTableWidget의 지역 좌표로 변환
        # item = self.interList.itemAt(pos)
        item = self.interList.indexAt(pos) #row정보가 필요하여 indexAt을 사용.
        # print(f"{pos} :: {item} :: {self.interList.rect()}")
        
        if event.reason() == event.Mouse:
            # Check if the right-click event occurs within the table widget's geometry
            if self.interList.rect().contains(pos) and item is not None: #우클릭좌표가 self.interList 내부일 경우
                row = item.row()
                if item.row() != -1 and item.row() > 0 :
                    self.selectedNm = self.interList.item(row, 0).text()
                    context_menu = QMenu(self)
                    copy_action = QAction("관심종목 제거", self)
                    copy_action.triggered.connect(self.modifyList)
                    context_menu.addAction(copy_action)
                    context_menu.exec_(event.globalPos())
        
        
    def test(self):
        data_to_write = {
                "name": "John",
                "age": 30,
                "city": "New York"
            }
        # writeJson("abc",data_to_write)
        readJson("abc")
        # delJson("abc")
    def gridList(self):
            "listData를 기반으로 QTableWidget을 생성하여 관심종목 리스트를 표현한다."
            if len(self.listData) > 0 :
                self.interList.setRowCount(self.interList.rowCount() + 1)
                for row, key in enumerate(self.listData):
                    item = QTableWidgetItem(str(key))
                    item.setTextAlignment(int(Qt.AlignRight|Qt.AlignVCenter))
                    self.interList.setItem(row +1, 0, item)
                "grid!!"
            else : print(f"관심종목을 표현할 데이터가 존재하지 않습니다.")
                
    def readList(self):
        self.listData = readJson(fileNm)
        print(f"{self.listData}")
        
    def modifyList(self):
        print(f"관심종목 제거 : {self.selectedNm}")
        # data = {}
        # writeJson(fileNm, data)  
    
          
#작업완료후 Qwidget화 할때 제거
def main():
    app = QApplication(sys.argv)
    window = InterestPopup()
    window.show()
    sys.exit(app.exec_())
if __name__ == '__main__':
    main()	
