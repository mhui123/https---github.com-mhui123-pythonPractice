from hogaHelper import *
from hogaHelper import showAlert
import re
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QVariant

class HogaOrderWin(QWidget):
    # 보유종목 호출로직 필요.(매도)
    # 미체결내역 호출로직 필요 (정정,취소)
    def __init__(self, parent, parent_data):
        super().__init__()  # 수정: QWidget 클래스의 생성자에 self를 전달
        self.parent = parent
        self.initUI(parent_data)
        parent.childSignal.connect(self.receiveAccountInfo)
        parent.posSignal.connect(self.posTest)
        
    def posTest(self, data):
        print(f"[posTest] : {data}")
        x = data['x'] + self.parent.width()
        y = data['y']
        self.move(x, y)
        
    def initUI(self, parent_data):
        self.parent_data = parent_data
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowTitle("호가주문")
        self.myQty = parent_data['myQty']
        
        windowW = self.parent.width()
        windowH = int(self.parent.height() / 3)
        parent_x = self.parent.x()
        parent_y = self.parent.y() 
        child_y = self.parent.y() + int(self.parent.height() / 2)
        x = parent_x + windowW
        self.setGeometry(x, parent_y, windowW, windowH)
        
        self.frame = QFrame(self)
        self.frame.setGeometry(5, 5, windowW - 10, windowH - 10)
        self.frame.setStyleSheet(u"border: 1px solid rgba(0,0,0,255);background-color: rgba(255, 255, 255, 0);margin-left:5px;")
        
        print(f"[hogawin initUi] parentData : {parent_data}")
        self.hoga_interval = int(parent_data['hoga_interval'])
        self.order_hoga = int(parent_data['price'])
        self.purePw = ""
        self.myUsableCash = int(parent_data['myUsableCash'])
        self.possibleQty = int(self.myUsableCash / self.order_hoga)
        self.qty = 0
        self.qtyMode = "amount"
        self.account_checked = False
        
        
        # self.resize(windowW, windowH)
        
        self.combo_box = QComboBox(self)
        self.inputPw = QLineEdit(self)
        self.inputPw.setPlaceholderText("계좌비밀번호")
        self.inputQty = QLineEdit(self)
        self.inputQty.setPlaceholderText("수량")
        self.checkBtn = QPushButton("계좌조회", self)
        self.inputPrice = QLineEdit(self)
        self.accountTable = QTableWidget(self)
        self.tableWidget = QTableWidget(self)
        self.ordTable = QTableWidget(self)
        self.inputPw.hide()
        
        
        #계좌번호 비밀번호입력
        accounts = self.parent.parent_data['account']
        self.myaccounts = {}
        for item in accounts :
            self.combo_box.addItem(item)
            self.myaccounts[item] = False
        self.combo_box.currentIndexChanged.connect(self.selectAccount)
        # self.inputQty.textChanged.connect(lambda: self.filtNumber(self.inputQty.text()))
        self.account_checked = False if parent_data['hogawinData'] is None else parent_data['hogawinData']['accountCheck'][self.combo_box.currentText()]
        
        self.accountTable.setColumnCount(3) # 3열
        self.accountTable.setRowCount(1) # 20행
        self.accountTable.setCellWidget(0,0, self.combo_box)
        # self.accountTable.setCellWidget(0,1, self.inputPw)
        self.accountTable.setCellWidget(0,2, self.checkBtn)
        self.accountTable.setStyleSheet("QTableWidget { border : none; gridline-color: white}") #테두리제거
        
        x = 15
        y = 15
        self.setTbGeometry(self.accountTable, x, y)
        
        self.inputPw.textChanged.connect(self.maskingPw)
        self.checkBtn.clicked.connect(self.getAccountInfo)
        
        
        self.tableWidget.setColumnCount(5) # 3열
        self.tableWidget.setRowCount(1) # 20행
        
        plusBtn = QPushButton("+", self)
        minusBtn = QPushButton("-", self)
        buyBtn = QPushButton("매수", self)
        sellBtn = QPushButton("매도", self)
        
        # item = QTableWidgetItem(format(parent_data['price'],","))
        # self.tableWidget.setItem(0, 2, item)
        self.inputPrice.setText(format(parent_data['price'],","))
        self.tableWidget.setCellWidget(0, 0, buyBtn)
        self.tableWidget.setCellWidget(0, 1, minusBtn)
        self.tableWidget.setCellWidget(0, 2, self.inputPrice)
        self.tableWidget.setCellWidget(0, 3, plusBtn)
        self.tableWidget.setCellWidget(0, 4, sellBtn)
        
        x = 15
        y = self.accountTable.height() + 5 + 15
        self.setTbGeometry(self.tableWidget, x, y)
        
        self.setStyle(self)
        self.setStyle(self.accountTable)
        self.setStyle(self.tableWidget)
        self.setStyle(self.ordTable)
        
        layout = QHBoxLayout() #가로로 배열. QVBoxLayout() : 세로로 배열
        self.changeModeCheckbox = QCheckBox(self)
        self.chkBoxLabel = QLabel("금액으로", self)
        self.changeModeCheckbox.stateChanged.connect(self.changeMode)
        
        layout.addWidget(self.changeModeCheckbox)
        layout.addWidget(self.chkBoxLabel)
        widget = QWidget()
        widget.setLayout(layout)
        
        # self.inputAsPrice = QPushButton("금액으로 수량입력")
        # self.inputAsPrice.clicked.connect(self.priceToQty)
        
        self.ordTable.setColumnCount(2) # 3열
        self.ordTable.setRowCount(4) # 20행
        col_width = self.ordTable.columnWidth(0)
        col_cnt = self.ordTable.columnCount()
        # row_height = self.ordTable.rowHeight(0)
        # row_cnt = self.ordTable.rowCount()
        # tbY = self.tableWidget.height() + self.accountTable.height() + 10
        # self.ordTable.setGeometry( 50, tbY, col_width * col_cnt , row_cnt * row_height)
        
        x = 50
        y = self.tableWidget.height() + self.accountTable.height() + 10 + 15
        self.setTbGeometry(self.ordTable, x, y, col_width * col_cnt)
        
        # self.ordTable(self.tableWidget, x, y)
        self.ordTable.setCellWidget(0,0, self.inputQty)
        self.ordTable.setCellWidget(0,1, widget)
        
        plusBtn.clicked.connect(self.btnClicked)
        minusBtn.clicked.connect(self.btnClicked)
        buyBtn.clicked.connect(self.callTradeEvent)
        sellBtn.clicked.connect(self.callTradeEvent)
        self.inputPrice.setObjectName("inputPrice")
        self.inputQty.setObjectName("inputQty")
        
        self.inputPrice.textChanged.connect(self.inputNumberChk)
        self.inputPrice.editingFinished.connect(self.inputNumberChk)
        self.inputQty.textChanged.connect(self.inputNumberChk)
        
        # 이전에 계좌조회를 이미 수행했을 경우 기입력처리 이벤트
        if self.account_checked == True:
            accountNo = self.combo_box.currentText()
            self.myaccounts[accountNo] = True
            self.inputPw.setText(parent_data['hogawinData']['accountPw'])
            self.selectAccount("direct")
            self.writeAccountInfo()
        
        # hideTest = QPushButton("test", self)
        # hideTest.move(0, 200)
        # hideTest.clicked.connect(self.btnHideShow)
    def priceToQty(self):
        price = self.filtNumber(self.inputQty.text())
        qty = int(price / self.order_hoga)
        return qty
        
    def writeAccountInfo(self):
        label = QLabel(f"주문가능금액 : {format(self.myUsableCash, ',')}")
        qtyLabel = QLabel(f"보유수량 : {self.myQty}")
        pQtyLabel = QLabel(f"주문가능수량 : {self.possibleQty}")
        
        self.ordTable.setCellWidget(1, 0, label)
        self.ordTable.setCellWidget(2, 0, qtyLabel)
        self.ordTable.setCellWidget(3, 0, pQtyLabel)
        for i in range(self.ordTable.rowCount()):
            if i > 0: self.ordTable.setSpan(i, 0, 1, 2)
            
    def updateAccountInfo(self):
        pQtyWidget = self.ordTable.cellWidget(3, 0)
        price = self.filtNumber(self.inputPrice.text())
        self.possibleQty = int(self.myUsableCash / price)
        pQtyWidget.setText(f"주문가능수량 : {self.possibleQty}")
        
    def btnHideShow(self):
        buyBtn = self.tableWidget.cellWidget(0, 0)
        sellBtn = self.tableWidget.cellWidget(0, 4)
        if buyBtn.isHidden():
            buyBtn.show()
            sellBtn.show()
        else :
            buyBtn.hide()
            sellBtn.hide()
        print(f"[HogaOrderWin][btnHideShow] : 확인")
            
    def changeMode(self, state):
        # checkLabel = self.ordTable.cellWidget(0, 1).findChild(QLabel)
        if state == 2: #checked
            state = "checked"
            self.inputQty.setPlaceholderText("금액")
            self.qtyMode = "price"
        else : #unchecked
            state = "unchecked"
            self.qtyMode = "amount"
            self.inputQty.setPlaceholderText("수량")
        
    def selectAccount(self, mode):
        if mode == "direct":
            accountNo = self.combo_box.currentText()
        else :
            accountNo = self.sender().currentText()
        
        if self.myaccounts[accountNo] == True:
            self.checkBtn.setDisabled(True)
            self.inputPw.setDisabled(True)
            # self.combo_box.setDisabled(True)
            self.chkAccountNoIsSearched()
        else :
            self.checkBtn.setDisabled(False)
            self.inputPw.setDisabled(False)
            self.chkAccountNoIsSearched()
        
    def btnClicked(self, event):
        sender = self.sender().text()
        if sender == "-":
            self.order_hoga -= self.hoga_interval
        else :
            self.order_hoga += self.hoga_interval
        # hogaPrice = self.tableWidget.item(0, 2)
        # hogaPrice.setText(format(self.order_hoga,","))
        self.inputPrice.setText(format(self.order_hoga,","))
        price = int(self.filtNumber(self.inputPrice.text()))
        self.possibleQty = int(self.myUsableCash / price)
        self.updateAccountInfo()
    
    def callTradeEvent(self, event): #주문요청
        if self.account_checked == False :
            showAlert("계좌정보를 먼저 조회해주세요")
        elif len(self.inputQty.text()) == 0 or int(self.inputQty.text()) == 0:
            showAlert("수량을 입력해주세요")
        else :
            sender = self.sender()
            print(f"거래요청 버튼 : {sender.text()}")
            if self.validateInputQty(sender.text()) == True :
                ordType = "신규매수" if sender.text() == "매수" else "신규매도"
                accountNo = self.combo_box.currentText()
                ordPrice = self.filtNumber(self.inputPrice.text())
                
                self.qty = self.inputQty.text() if self.qtyMode == "amount" else self.priceToQty()
                
                ordQty = self.qty
                purpose = "주문"
                data = {"purpose":purpose,"accountNo" : accountNo, "ordQty":ordQty, "ordPrice":ordPrice, "ordType":ordType}
                self.parent.passToMain(data)
    
    def passToMain(self, data):
        print(f"[주문창]passToMain {data}")
        self.parent.receiveDataFromChild(data)
    
    def filtNumber(self, data):
        data = re.sub(r'[^0-9]', '', data)
        return int(data) if len(data) > 0 and isinstance(data, str) else 0
    
    def inputNumberChk(self) :
        sender = self.sender().objectName()
        if sender == "inputPrice":
            if len(self.sender().text()) > 0:
                price = int(self.filtNumber(self.sender().text()))
                if isinstance(price, int):
                    self.order_hoga = price
                else : self.order_hoga = int(self.parent_data['price'])
        elif sender == "inputQty":
            if self.qtyMode == "amount" : 
                qty = self.filtNumber(self.sender().text())
                if qty > self.possibleQty : 
                    qty = self.possibleQty
                self.inputQty.setText(format(qty, ","))
            
    def validateInputQty(self, gubun) : 
        result = True
        qty = self.filtNumber(self.inputQty.text())
        if gubun == "매수":
            if self.qtyMode == "amount":
                if qty > self.possibleQty : 
                    qty = self.possibleQty
                    self.inputQty.setText(format(qty, ","))
                    showAlert("주문가능수량을 초과하여 입력하였습니다.")
                    result = False
            elif self.qtyMode == "price":
                if qty > self.myUsableCash :
                    showAlert("주문가능수량을 초과하여 입력하였습니다.")
                    result = False
        elif gubun == "매도":
            if self.qtyMode == "amount":
                if qty > self.myQty : 
                    qty = self.myQty
                    self.inputQty.setText(format(qty, ","))
                    showAlert("보유수량을 초과하여 입력하였습니다.")
                    result = False
            elif self.qtyMode == "price":
                if qty > self.myQty *  self.filtNumber(self.inputPrice.text()):
                    showAlert("보유한 주식금액을 초과하여 입력하였습니다.")
                    result = False
        return result
        
    def maskingPw(self):
        # text = re.sub(r'\D', '', text)
        self.inputPw.textChanged.disconnect(self.maskingPw)
        text = self.inputPw.text()
        text = re.sub(r'[^0-9*]', '', text)
        lastChar = text if len(self.purePw) == 0 else ( text[len(text) -1] if len(text) > 0 else "")
        if len(self.purePw) < len(text) :
            self.purePw += lastChar
        elif len(self.purePw) > len(text) :
            self.purePw = self.purePw[:-1]
        
        self.purePw = self.purePw[:4]
        text = text[:4]
        masked = re.sub(r'.', '*', text) #masking
        self.inputPw.setText(masked)
        self.inputPw.textChanged.connect(self.maskingPw)
    
    def getAccountInfo(self):
        accountNo = self.combo_box.currentText()
        accountPw = self.purePw
        print(f"계좌조회용 파라미터 : {accountNo}:{accountPw}")
        data = {}
        data['purpose'] = "계좌조회"
        data['accountNo'] = accountNo
        data['accountPw'] = accountPw
        data['accountCheck'] = self.myaccounts
        self.parent.passToMain(data)
        
    def receiveAccountInfo(self, data):
        self.myUsableCash = data['myUsableCash']
        self.myQty = data['myQty']
        print(f"조회테스트 : {data}\n{data['myUsableCash']} self.myUsableCash : {self.myUsableCash}")
        self.writeAccountInfo()
        self.updateAccountInfo()
        accountNo = self.combo_box.currentText()
        
        self.myaccounts[accountNo] = True
        self.account_checked = self.myaccounts[accountNo]
        
        self.checkBtn.setDisabled(True)
        self.inputPw.setDisabled(True)
    
    def chkAccountNoIsSearched(self, accountNo) :
        if accountNo not in self.myaccounts or self.myaccounts[accountNo] == False :
            self.possibleQty = 0
            self.myUsableCash = 0
            self.myQty = 0
        self.writeAccountInfo()
        self.updateAccountInfo()
    def setStyle(self, target):
        if isinstance(target, QTableWidget):
            target.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            target.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            target.verticalHeader().setVisible(False)
            target.horizontalHeader().setVisible(False)
            target.setEditTriggers(QTableWidget.NoEditTriggers) #테이블 직접수정 불가
            target.setStyleSheet("QTableWidget { border : none; gridline-color: white; border-top:10px}"
                                       "QTableWidget::item:selected { background-color: transparent; }"
                                       ) #테두리제거
        elif isinstance(target, QWidget) or isinstance(target, QMainWindow):
            target.setStyleSheet("background-color:white") #테두리제거
            
    def setTbGeometry(self, target, x, y, w = ""):
        if isinstance(target, QTableWidget):
            row_height = target.rowHeight(0)
            row_cnt = target.rowCount()
            w = self.frame.width() - 20 if w == "" else w
            h = row_height * row_cnt
            target.setGeometry(x, y, w, h)
        for i in range(target.columnCount()):
            target.setColumnWidth(i, int(target.width() / target.columnCount())) 