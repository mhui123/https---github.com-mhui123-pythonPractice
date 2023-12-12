import sys, os
import typing
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QVariant, QEvent
from PyQt5.QtGui import QFont, QColor, QFontInfo
from JsonControl import *
from TableControl import *

fileNm = "interestList"
app = QApplication([])
current_font = app.font()
# Get the font info
font_info = QFontInfo(current_font)
# Get the font family name
font_family_name = font_info.family()

# class InterestPopup(QMainWindow):
class InterestPopup(QWidget):
    listData = None
    selectedNm = None
    SCREEN_NO = "0150"
    HOGA_SCREEN = "0111"
    codeList = []
    callIdx = 0
    timeGubun = None
    def __init__(self, parent):
        self.mainWin = parent
        self.timeGubun = self.mainWin.determinTime()
        super().__init__()
        self.readList()
        self.initUi()    
        self.initList()
        self.callRealTimeData()
        
    
    def initUi(self):
        layout = QGridLayout(self)
        label = QLabel('<font size="4"><b>관심종목</b></font>')
        layout.addWidget(label, 0, 0)
        
        self.interList = QTableWidget()
        self.interList.setColumnCount(5)
        setTbStyle(self.interList)
        tbHeaders = ['종목명', '현재가', '거래량', '전일대비', '등락률']
        setTbHeader(self.interList, tbHeaders)
        layout.addWidget(self.interList, 1, 0)
        
        central_widget = QWidget(self)  # Create a central widget
        central_widget.setLayout(layout)  # Set the layout for the central widget
        # self.setCentralWidget(central_widget)  
        
        #화면에 표현하려면 widget에 layout을 붙인 후 해당 widget을 추가해주는 것으로 처리함.
        self.mainWin.interListInfoChanged.connect(self.test)
        
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
        
    def test(self, data):
        # print(f"[관심종목 데이터수신 테스트] : {data}")
        
        if self.timeGubun != "장중":
            if len(self.codeList) > 1 :
                print(f"[관심종목] - !장중data : {data}")
                self.callIdx += 1
                if self.callIdx <= len(self.codeList) -1 :
                    self.callBasicInfo(self.codeList[self.callIdx])
                    # self.callIdx = 0 #조회완료 후 호출인덱스 초기화
                else :
                    """
                    data= {'KG이니시스': {'250최고': 14470, '250최저': -10080, '거래대비': -79.41, '거래량': 257275, '고가': 13120, '기준가': 12960, '대비기호': 5, '등락율': -0.08, '상한가': 16840, '시가': 12960, '연중최고': 14470, '연중최저': -10080, '저가': -12770, '전일대비': -10, '전일대비,등락율': '-10 (-0.08%)', '종목명': 'KG이니시스', '종목코드': 35600, '하한가': -9080, '현재가': -12950}, '셀트리온': {'250최고': 184900, '250최저': -131000, '거래대비': 110.28, '거래량': 1321770, '고가': 184900, '기준가': 177700, '대비기호': 2, '등락율': 3.21, '상한가': 231000, '시가': 178600, '연중최고': 184900, '연중최저': -131000, '저가': -177300, '전일대비': 5700, '전일대비,등락율': '5700 (3.21%)', '종목명': '셀트리온', '종목코드': 68270, '하한가': -124400, '현재가': 183400}}
                    #해당 data를 self.interList에 뿌려주기.
                    """
                    for key in data.keys():
                        self.gridData(data[key])
        else : 
            self.gridData(data)
            
    def gridData(self, data):
        rowIdx = self.codeList.index(data['종목코드']) if data['종목코드'] in self.codeList else None
        if rowIdx != None:
            gridKeys = ['현재가', '거래량', '전일대비', '등락율']
            for idx, key in enumerate(gridKeys) :
                value = 0
                intVal = 0
                if key == '등락율' :
                    intVal = float(data[key])
                    value = str(intVal)+"%"
                else :
                    intVal = int(data[key])
                    value = format(abs(intVal), ',') if key != '전일대비' else format(intVal, ',')
                
                font = QFont(font_family_name, 12, QFont.Bold)
                
                isToInsert = True if self.interList.item(rowIdx +1, idx +1) == None else False
                item = QTableWidgetItem(value) if isToInsert == True else self.interList.item(rowIdx +1, idx +1)
                item.setFont(font)
                
                if intVal > 0 :
                    item.setForeground(QColor("red"))
                else :
                    item.setForeground(QColor("blue"))
                    
                if isToInsert == True:
                    item.setTextAlignment(int(Qt.AlignRight|Qt.AlignVCenter))
                    self.interList.setItem(rowIdx +1, idx +1, item)
                else :    
                    item.setText(value)
                
    def initList(self):
            "listData를 기반으로 QTableWidget을 생성하여 관심종목 리스트를 표현한다."
            if self.listData is not None and len(self.listData) > 0 :
                for row, key in enumerate(self.listData):
                    self.interList.setRowCount(self.interList.rowCount() + 1)
                    item = QTableWidgetItem(str(key))
                    item.setTextAlignment(int(Qt.AlignRight|Qt.AlignVCenter))
                    self.interList.setItem(row +1, 0, item)
                
                tbColCnt = self.interList.columnCount()
                tbColWidth = self.interList.columnWidth(0)
                w = tbColCnt * tbColWidth
                tbRowCnt = self.interList.rowCount()
                tbRowHeight = self.interList.rowHeight(0)
                h = tbRowCnt * tbRowHeight
                self.interList.setMinimumWidth(w)
                self.interList.setMinimumHeight(h)
            else : print(f"관심종목을 표현할 데이터가 존재하지 않습니다.")
                
    def readList(self):
        self.listData = readJson(fileNm)
        if self.listData is not None :
            self.codeList = [value['code'] for value in self.listData.values()]
        
    def modifyList(self):
        #관심종목 테이블에서 제거
        delPos = self.find_text_position(self.interList, self.selectedNm)
        stockCd = self.listData[self.selectedNm]
        self.mainWin.DisConnectRealData(self.SCREEN_NO, stockCd) #삭제종목 실시간데이터요청 해제
        toDelRow = delPos[0] if delPos[0] is not None else -1
        if toDelRow != -1:
          self.interList.removeRow(toDelRow)  
          
        #json파일에서 제거
        del self.listData[self.selectedNm]
        data = self.listData
        writeJson(fileNm, data) #관심종목리스트 업데이트
    
    def find_text_position(self, tb, target_text):
        rows = tb.rowCount()
        cols = tb.columnCount()

        for row in range(rows):
            for col in range(cols):
                item = tb.item(row, col)
                if item is not None and item.text() == target_text:
                    return row, col

        # 찾지 못한 경우
        return None, None
    def callRealTimeData(self):
        timeGubun = self.timeGubun
        print(f"시간구분: {timeGubun}")
        # self.listData = {'KG이니시스': '035600', 'GS리테일': '007070', '셀트리온': '068270'}
        
        if self.listData is not None :
            for idx, key in enumerate(self.listData):
                mode = 0
                code = self.listData[key]['code']
                if idx > 0 : mode = 1
                
                if timeGubun == "장중":
                    print(f'self.SetRealReg({self.SCREEN_NO}, {code}, "10;", {mode})') 
                    #mainWin에 추가했을떄 해당코드 활성화처리
                    self.mainWin.SetRealReg(self.SCREEN_NO, code, "10;", mode) #0 : 신규요청 1: 추가요청
            if timeGubun != "장중":
                firstCode = self.codeList[self.callIdx]
                self.callBasicInfo(firstCode)
        # if timeGubun != "장중":
        #     self.mainWin.getStockBasicInfo(codeList, self.SCREEN_NO)
    def callBasicInfo(self, code):
        """
        code : 조회할 종목코드
        """
        print(f"조회대상 : {self.codeList} {code}")
        self.mainWin.getStockBasicInfo(code, self.SCREEN_NO)
    
    def closeEvent(self, event):
        self.mainWin.DisConnectRealData(self.SCREEN_NO)
          
#작업완료후 Qwidget화 할때 제거
# def main():
#     app = QApplication(sys.argv)
#     window = InterestPopup()
#     window.show()
#     sys.exit(app.exec_())
# if __name__ == '__main__':
#     main()	
