import re
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QVariant
from HogaOrderWin import *

#호가창class
class HogaWin(QWidget):
    childSignal = pyqtSignal(QVariant)
    posSignal = pyqtSignal(QVariant)
    def __init__(self, parent, parent_data):
        super().__init__()  # 수정: QWidget 클래스의 생성자에 self를 전달
        
        #호가창변수
        self.sellPrices = []
        self.sellAmts = []
        self.buyPrices = []
        self.buyAmts = []
        self.sellChanges = []
        self.buyChanges = []
        self.sPs = []
        self.bPs = []
        self.mode = "price"
        self.hoga_interval = 0
        self.myUsableCash = 0
        self.hogawinData = {}
        self.myQty = 0
        
        self.parent = parent
        self.initUI(parent_data)
        
        parent.dataChanged.connect(self.on_data_changed)
        parent.stockInfoChanged.connect(self.on_stock_info_changed)
        parent.accountInfoChanged.connect(self.on_account_info_changed)

        for i in range(10, 0, -1):
            v = i
            self.sellPrices.append(f"매도호가{v}")
            self.sellAmts.append(f"매도호가수량{v}")
            self.sellChanges.append(f"매도직전대비{v}")
            
        for i in range(10):
            v = i + 1
            self.buyPrices.append(f"매수호가{v}")
            self.buyAmts.append(f"매수호가수량{v}")
            self.buyChanges.append(f"매수직전대비{v}")
            
    def initUI(self, parent_data):
        self.parent_data = parent_data
        self.hogawin_data = self.parent_data['hogawinData']
        self.myUsableCash = self.parent_data['myUsableCash']
        
        #filtered_data = [item for item in data if item["name"].find(text) != -1] # string.find(txt) == -1이면 해당 텍스트 없음
        self.myQty = [item['qty'] for item in parent_data['myAssetInfo'] if item['stockNm'] == self.parent.stockName]
        if len(self.myQty) == 0:
            self.myQty = 0
        else : self.myQty = self.myQty[0]
        
        self.setWindowTitle("호가창")
        self.setGeometry(620,300,300,760)
        #self.setGeometry(300,300,300,200)
        self.c_hoga_dict = {}
        self.stockNm = ""
        
        self.changeModeBtn = QPushButton("수량으로 보기", self)
        self.changeModeBtn.setGeometry(100, 675, 100, 30)
        self.changeModeBtn.clicked.connect(self.changeMode)
        
        # sendTestBtn.move(20,20)
        
        #정보테이블 생성
        self.infoTable = QTableWidget(self)
        self.infoTable.resize(290, 100)
        self.infoTable.setColumnCount(2) # 2열
        self.infoTable.setRowCount(3) # 3행
        
        """
        self.nowP = 0 #현재가
        self.nowTAmt = 0 #거래량
        self.nowChangePer = 0 #등락률
        self.nowChangePrice = 0 #전일대비
        """
        item = QTableWidgetItem(self.parent.stockName)
        item.setTextAlignment(int(Qt.AlignRight|Qt.AlignVCenter))
        self.infoTable.setItem(0, 0, item)
        item = QTableWidgetItem(f"{int(self.parent.nowP)}")
        item.setTextAlignment(int(Qt.AlignRight|Qt.AlignVCenter))
        self.infoTable.setItem(1, 0, item)
        item = QTableWidgetItem(f"{self.parent.nowChangePrice} ({self.parent.nowChangePer})")
        item.setTextAlignment(int(Qt.AlignRight|Qt.AlignVCenter))
        self.infoTable.setItem(0, 1, item)
        item = QTableWidgetItem(f"{self.parent.nowTAmt}")
        item.setTextAlignment(int(Qt.AlignRight|Qt.AlignVCenter))
        self.infoTable.setItem(1, 1, item)
        
        self.infoTable.verticalHeader().setVisible(False)
        self.infoTable.horizontalHeader().setVisible(False)
        self.infoTable.setColumnWidth(0, int(self.infoTable.width() * 0.5))
        self.infoTable.setColumnWidth(1, int(self.infoTable.width() * 0.5))
        self.infoTable.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        
        #호가테이블생성
        self.tableWidget = QTableWidget(self)
        self.tableWidget.move(0,60)
        self.tableWidget.resize(290, 620)
        self.tableWidget.setColumnCount(5) # 3열
        self.tableWidget.setRowCount(20) # 20행
        
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.horizontalHeader().setVisible(False)

        #self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setColumnWidth(0, int(self.tableWidget.width() * 0.2))
        self.tableWidget.setColumnWidth(1, int(self.tableWidget.width() * 0.2))
        self.tableWidget.setColumnWidth(2, int(self.tableWidget.width() * 0.2))
        self.tableWidget.setColumnWidth(3, int(self.tableWidget.width() * 0.2))
        self.tableWidget.setColumnWidth(4, int(self.tableWidget.width() * 0.2))  
        
        #가로스크롤바 제거
        self.tableWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tableWidget.itemClicked.connect(self.handle_tbItem_click) #price column만 클릭했을때 이벤트 동작
        self.tableWidget.cellClicked.connect(self.cellClickEvent)
        # price 
        for i in range(20):
            price = 0
            item = QTableWidgetItem(format(price, ","))
            item.setTextAlignment(int(Qt.AlignRight|Qt.AlignVCenter))
            self.tableWidget.setItem(i, 2, item)
        # quantity
        # asks
        for i in range(10):
            self.tableWidget.setSpan(i, 0, 1, 2)
            quantity = 0

            widget = QWidget()
            layout = QVBoxLayout(widget)
            pbar = QProgressBar()
            pbar.setFixedHeight(20)
            pbar.setInvertedAppearance(True)  
            pbar.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
            pbar.setStyleSheet("""
                QProgressBar {background-color : rgba(0, 0, 0, 0%);border : 1}
                QProgressBar::Chunk {background-color : rgba(0, 0, 255, 20%);border : 1}
            """)
            layout.addWidget(pbar)
            layout.setAlignment(Qt.AlignVCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            widget.setLayout(layout)
            self.tableWidget.setCellWidget(i, 1, widget)

            # set data 
            pbar.setRange(0, 100000000)
            pbar.setFormat(str(quantity))
            pbar.setValue(quantity)

        # bids
        for i in range(10, 20):
            quantity = 0
            self.tableWidget.setSpan(i, 3, 1, 2)
            widget = QWidget()
            layout = QVBoxLayout(widget)
            pbar = QProgressBar()
            pbar.setFixedHeight(20)
            #pbar.setInvertedAppearance(True)  
            pbar.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
            pbar.setStyleSheet("""
                QProgressBar {background-color : rgba(0, 0, 0, 0%);border : 1}
                QProgressBar::Chunk {background-color : rgba(255, 0, 0, 20%);border : 1}
            """)
            layout.addWidget(pbar)
            layout.setAlignment(Qt.AlignVCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            widget.setLayout(layout)
            self.tableWidget.setCellWidget(i, 3, widget)

            # set data 
            pbar.setRange(0, 100000000)
            pbar.setFormat(str(quantity))
            pbar.setValue(quantity)
            
    def changeMode(self):
        btnTxt = self.changeModeBtn.text()
        print(f"test change : {btnTxt}")
        if btnTxt == "수량으로 보기" : 
            btnTxt = "가격으로 보기"
            self.mode = "amount"
        else :
            btnTxt = "수량으로 보기"
            self.mode = "price"
        print(f"현재모드 {self.mode}")
        self.changeModeBtn.setText(btnTxt)
        self.updateTable()
        
    
    def on_account_info_changed(self, new_data):
        self.myUsableCash = new_data['myUsableCash']
        self.hogawin_data = new_data['hogawinData']
        new_data['myQty'] = self.myQty
        self.childSignal.emit(new_data)
        
    def on_data_changed(self, new_data):
        if type(new_data) is dict:
            self.c_hoga_dict = new_data
            self.updateTable()
    def on_stock_info_changed(self, data):
        if type(data) is dict :
            key = None
            dataStr = ""
            # for key, value in data.items():
            #     dataStr += f"{key} : {value}\t"
            if len(data) > 0:
                pStart = data['todayStart']
                pHigh = data['todayHigh']
                pLow = data['todayLow']
                pChange = data['priceChange']
                nowPrice = format(int(data['nowPrice']),",")
                tAmt = format(int(data['accAmt']),",")
                signAmt = data['tradeAmt']
                movePercent = data['movePercent']
                dataStr = f"시가:{pStart}\t고가:{pHigh}\t저가:{pLow}\t등락:{pChange}\t거래량:{tAmt}\t 체결량:{signAmt}"
                # print(dataStr)
                # item = QTableWidgetItem(f"{self.parent.nowChangePrice} ({self.parent.nowChangePer})")
                # item.setTextAlignment(int(Qt.AlignRight|Qt.AlignVCenter))
                # self.infoTable.setItem(0, 1, item)
                
                self.infoTable.item(0, 1).setText(f"{pChange}({movePercent}%)")
                self.infoTable.item(1, 0).setText(f"{nowPrice}")
                self.infoTable.item(1, 1).setText(f"{tAmt}")
                
    def handle_tbItem_click(self, item):
        row = item.row()
        col = item.column()
        itemCheck = item.text() if len(item.text()) > 0 else "0"
        self.toSendPrice = int(re.sub(r'[,]', '', itemCheck))
        if col == 2 :
            self.openPopup()
        # print(f"table click : {row} {col} {text}")
    
    def openPopup(self):
        if hasattr(self, "hogaOrderwin"): # self에 팝업변수 존재 체크
            self.hogaOrderwin.close()
        
        toPassData = {"hoga_interval" : self.hoga_interval, "price" : self.toSendPrice, "hogawinData":self.hogawin_data, "myUsableCash":self.myUsableCash, "myQty" : self.myQty}
        self.hogaOrderwin = HogaOrderWin(self, toPassData)
        self.hogaOrderwin.show()
    def cellClickEvent(self, row,col):
        if col != 2 :
            if hasattr(self, "hogaOrderwin"): # self에 팝업변수 존재 체크
                self.hogaOrderwin.close()
        
    def mousePressEvent(self, event):
        clicked_pos = event.pos()
        print(f"x : {clicked_pos.x()} {clicked_pos.y()}")
        if hasattr(self, "hogaOrderwin"): # self에 팝업변수 존재 체크
            self.hogaOrderwin.close()
            
    def updateTable(self):
        #수량 최대값 구하기용 리스트 제작
        for i in range(10):
            self.sPs.append(int(self.c_hoga_dict[self.sellAmts[i]]))
            self.bPs.append(int(self.c_hoga_dict[self.buyAmts[i]]))
            
        sMax = max(self.sPs)
        bMax = max(self.bPs)
        realMax = sMax if sMax > bMax else bMax
        
        hoga_interval_chk = 0
        #update 매도가격과 호가
        for i in range(10):
            # print(f"{new_data[self.sellPrices[i]]} {new_data[self.sellAmts[i]]} {new_data[self.sellChanges[i]]}")
            # print(f"{new_data[self.buyPrices[i]]} {new_data[self.buyAmts[i]]} {new_data[self.buyChanges[i]]}")
            
            #가격 업데이트
            # item = QTableWidgetItem(format(price, ","))
            purePrice = int(re.sub(r'[+-]', '', self.c_hoga_dict[self.sellPrices[i]]))
            sAmt = int(self.c_hoga_dict[self.sellAmts[i]])
            sP = self.tableWidget.item(i, 2)
            
            sQ = self.tableWidget.cellWidget(i, 1)
            sQBar = sQ.findChild(QProgressBar)
            calToWon = purePrice * int(self.c_hoga_dict[self.sellAmts[i]])
            wonTxt = str(calToWon) if not isinstance(self.print10T(calToWon), str) else self.print10T(calToWon)
            calToWon = format(purePrice * sAmt, ",")
            
            if self.hoga_interval == 0 and hoga_interval_chk == 0 :
                hoga_interval_chk = purePrice
            elif self.hoga_interval == 0 and hoga_interval_chk > 0 :
                self.hoga_interval = hoga_interval_chk - purePrice
            
            hogaV = None
            if self.mode == "price":
                hogaV = wonTxt
            elif self.mode == "amount" :
                hogaV = format(sAmt, ",")
                
            purePrice = "" if purePrice == 0 else format(purePrice, ",")
            hogaV = "" if purePrice == 0 else hogaV
            sP.setText(purePrice)
            
            if isinstance(sQBar, QProgressBar):
                sQBar.setRange(0, realMax)
                # sQBar.setFormat(new_data[self.sellAmts[i]])
                sQBar.setFormat(hogaV)
                sQBar.setValue(sAmt)
            
            #표시할 호가수량 변동: self.c_hoga_dict['매도직전대비1~10']
            key = f"매도직전대비{i+1}"
            if key in self.c_hoga_dict :
                sQChange = self.c_hoga_dict[key]
                check = int(re.sub(r'[+-]', '', sQChange))
                if check != 0:
                    label = QLabel(sQChange, self)
                    label.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
                    label.setStyleSheet("background-color: rgba(255, 255, 255, 0);margin-left:5px;") 
                    self.tableWidget.setCellWidget(9 - i, 0, label)
                else :
                    label = QLabel("", self)
                    label.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
                    label.setStyleSheet("background-color: rgba(255, 255, 255, 0);margin-left:5px;") 
                    self.tableWidget.setCellWidget(9 - i, 0, label)
        #update 매수가격과 호가
        for i in range(10,20):
            idx = i - 10
            purePrice = int(re.sub(r'[+-]', '', self.c_hoga_dict[self.buyPrices[idx]]))
            bP = self.tableWidget.item(i, 2)
            bQ = self.tableWidget.cellWidget(i, 3)
            bQBar = bQ.findChild(QProgressBar)
            bAmt = int(self.c_hoga_dict[self.buyAmts[idx]])
            
            calToWon = purePrice * bAmt
            wonTxt =  str(calToWon) if not isinstance(self.print10T(calToWon), str) else self.print10T(calToWon)
            calToWon = format(purePrice * bAmt, ",")
            
            hogaV = None
            if self.mode == "price":
                hogaV = wonTxt
            elif self.mode == "amount" :
                hogaV = format(bAmt, ",")
                
            purePrice = "" if purePrice == 0 else format(purePrice, ",")
            hogaV = "" if purePrice == 0 else hogaV
            bP.setText(purePrice)
            
            if isinstance(bQBar, QProgressBar):
                bQBar.setRange(0, realMax)
                bQBar.setFormat(hogaV)
                bQBar.setValue(bAmt)
            #표시할 호가수량 변동: self.c_hoga_dict['매도직전대비1~10']
            key = f"매수직전대비{idx +1}"
            if key in self.c_hoga_dict :
                bQChange = self.c_hoga_dict[key]
                check = int(re.sub(r'[+-]', '', bQChange))
                if check != 0:
                    label = QLabel(bQChange, self)
                    label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
                    label.setStyleSheet("background-color: rgba(255, 255, 255, 0);margin-right:5px;") 
                    self.tableWidget.setCellWidget(i, 4, label)
                else :
                    label = QLabel("", self)
                    label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
                    label.setStyleSheet("background-color: rgba(255, 255, 255, 0);margin-right:5px;") 
                    self.tableWidget.setCellWidget(i, 4, label)

    def print10T(self, num):
        self.number = num
        if not isinstance(num, int) :
            if isinstance(num, str) :
                self.number = int(num)
            else : self.number = 0
            
        result = ""
        to10Thousand = self.number / 10000
        if num < 10000 : return str(self.number) + "원"
        elif to10Thousand >= 10000 :
            int_part = int(to10Thousand / 10000)
            fractional_part = str((to10Thousand / 10000) - int_part).split('.')[1][0:4]
            
            result = str(int_part) +"억" + str(fractional_part) +"만원"
        else :
            result = str(int(to10Thousand)) + "만원"
        return result
        
        
    def passToMain(self, data):
        print(f"[호가창]passToMain {data}")
        if data['purpose'] == "계좌조회":
            accountNo = data['accountNo']
            data['accountCheck'][accountNo] = True
        self.parent.receiveDataFromChild(data)
    def closeEvent(self, event):
        if hasattr(self, "hogaOrderwin"): # self에 팝업변수 존재 체크
            self.hogaOrderwin.close()
        self.parent.DisConnectRealData()
        
    def moveEvent(self, event):
        self.posSignal.emit({"x" : self.x(), "y":self.y()})