from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QVariant
import re
#계좌별 자산, 주문현황 window
class OrderInfoPop(QWidget):
    STOCK_NAME = ""
    STOCK_CODE = ""
    def __init__(self, parent):
        self.STOCK_NAME = parent.stockName
        self.STOCK_CODE = parent.stockCode
        super().__init__()  # 수정: QWidget 클래스의 생성자에 self를 전달
        self.mainWin = parent
        self.originOrdNo = None
        self.trType = None
        self.ordQty = 0
        self.fixQty = 0
        self.gridMode = "YET"
        
        self.initUI()

    def initUI(self):
        self.setWindowTitle("테스트")
        self.setGeometry(15,15,1400,760)
        
        windowW = self.width()
        windowH = self.height()
        self.frame = QFrame(self)
        self.frame.setGeometry(5, 5, windowW - 10, windowH - 10)
        self.frame.setStyleSheet(u"border: 1px solid rgba(0,0,0,255);background-color: rgba(255, 255, 255, 0);margin-left:5px;")
        
        mainContainer = QVBoxLayout(self.frame)
        btnGrid = QGridLayout()
        tbGrid = QGridLayout()
        editGrid = QGridLayout()
        
        mainContainer.addLayout(tbGrid)
        # mainContainer.addLayout(editGrid)
        # mainContainer.addLayout(btnGrid)
        
        #self.setGeometry(300,300,300,200)
        testBtn = QPushButton("test", self)
        fixBtn = QPushButton("정정", self)
        cBtn = QPushButton("취소", self)
        
        btnGrid.addWidget(testBtn, 0, 0)
        btnGrid.addWidget(fixBtn, 0, 1)
        btnGrid.addWidget(cBtn, 0, 2)
        
        testBtn.clicked.connect(self.test)
        fixBtn.clicked.connect(self.fixCancel)
        cBtn.clicked.connect(self.fixCancel)
        
        self.qtyEdit = QLineEdit()
        self.qtyEdit.setPlaceholderText("정정수량")
        self.qtyEdit.setMaximumWidth(50)
        self.qtyEdit.textEdited.connect(self.chkValid)
        editGrid.addWidget(self.qtyEdit)
        # cBtn.setGeometry(100,30,30,20)
        
        self.mainWin.orderInfoChanged.connect(self.update_orderInfo)
        
        tbHeaders = ['주문번호', '종목명', '매매구분', '주문단가','주문수량','접수구분','주문시간','체결수량', '체결단가', '주문잔량','주문구분', '정정취소', '신용구분', '확인수량',  '반대여부',  '원주문',   '대출일',  '통신구분', '확인시간']
        
        self.stockTable = QTableWidget(self)
        
        tbGrid.addWidget(self.stockTable, 0, 0)
        self.stockTable.setColumnCount(len(tbHeaders))
        self.stockTable.insertRow(0)
        for i in range(self.stockTable.columnCount()):
            item = QTableWidgetItem(tbHeaders[i])
            item.setTextAlignment(int(Qt.AlignRight|Qt.AlignVCenter))
            self.stockTable.setItem(0, i, item)
            
        self.stockTable.cellClicked.connect(self.cellClickEvent)
    def chkValid(self):
        text = str(self.filtNumber(self.sender().text()))
        self.sender().setText(text)
        
    def filtNumber(self, data):
        data = re.sub(r'[^0-9]', '', data)
        return int(data) if len(data) > 0 and isinstance(data, str) else 0
    
    def update_orderInfo(self):
        self.gridList()
        
    def test(self):
        text = "주문없음" if len(self.mainWin.orderInfos) == 0 else self.mainWin.orderInfos[0]
        print(f"[orderInfo update test] : {text} {self.qtyEdit.text()}")
        # print(f"{self.mainWin.myAssetInfos}")
    def fixCancel(self):
        txt = self.sender().text()
        if txt == "정정" :
            self.ordQty = self.qtyEdit.text()
            print(f"정정 이벤트 구현필요")
        elif txt == "취소" :
            print(f"취소 이벤트 구현필요")
        
        # ordTypes = ["매수정정", "매도정정", "매수취소", "매도취소"]
        ordType = self.trType[2:4] + txt
        data = {"purpose":"주문","accountNo" : self.mainWin.thisAccountNo, "ordQty":self.ordQty, "ordPrice":self.ordPrice, "ordType":ordType, "originOrdNo" : self.originOrdNo}
        # self.parent.passToMain(data)
        self.mainWin.callApi(data)
        
        """
        #주문전 확인: sendOrder(4989), 8062374811, 1, 035600 11360(2개) 00
        print(f"주문전 확인: {rqName}({self.screenNo}), {accountNo}, {orderTypes[ordType]}, {self.stockCode} {orderPrice}({orderQty}개) {self.hogaGubun} {orgOrdNo}")
        purpose = "주문"
                data = {"purpose":purpose,"accountNo" : accountNo, "ordQty":ordQty, "ordPrice":ordPrice, "ordType":ordType}
                # self.parent.passToMain(data)
                self.mainWin.callApi(data)
        1. 정정주문시 수량과 가격 입력받아 주문전송하는 기능 필요
        2. 주문 체결, 새로운 주문 추가, 주문취소시 테이블 업데이트 기능 필요
        3. 정정주문시 체결,취소된 주문은 전송 못하도록 validate
        """
        
    def cellClickEvent(self, row, col):
        if row > 0:
            ordNo = self.stockTable.cellWidget(row, 0).text()
            ordGubun = self.stockTable.cellWidget(row, 10).text()
            self.ordPrice = self.stockTable.cellWidget(row, 3).text()
            self.ordQty = self.stockTable.cellWidget(row, 4).text()
            self.originOrdNo = ordNo
            self.trType = ordGubun
            print(f"선택한 주문번호 : {ordNo} {self.originOrdNo} {ordGubun} {self.ordPrice} {self.ordQty}")
            self.mainWin.update_originOrdNo({"originOrdNo" : ordNo, "ordPrice" : self.ordPrice, "qty" : self.ordQty, "gubun":ordGubun})
            self.close()
    def gridList(self):
        assets = self.mainWin.orderInfos
        self.stockTable.setRowCount(len(assets) + 1)
        tableItems = ['주문번호', '종목명', '매매구분', '주문단가','주문수량','접수구분','주문시간','체결수량', '체결단가', '주문잔량','주문구분', '정정취소', '신용구분', '확인수량',  '반대여부',  '원주문',   '대출일',  '통신구분', '확인시간']
        notYetDeals = [item for item in self.mainWin.orderInfos if item['종목명'] == self.STOCK_NAME and item['주문잔량'] > 0]
        if self.gridMode == "YET":
            assets = notYetDeals
        canceledOrds = []
        for row, rowData in enumerate(assets):
            stockNm = assets[row]['종목명']
            isExist = self.searchTable(self.stockTable, stockNm)['isExist']
            if isExist == False :
                self.stockTable.insertRow(row +1)
                for col, value in enumerate(tableItems) :
                    if value == "접수구분":
                        rowData[value] = "체결" if rowData['체결수량'] > 0 and rowData['주문잔량'] == 0 else "미체결"
                    elif rowData[value] == "취소":
                        rowData['접수구분'] = "취소"
                        posRow = self.searchTable(self.stockTable, rowData['원주문'])['posRow']
                        canceledOrds.append(posRow)
                        cellwid = self.stockTable.cellWidget(row+1, 5)
                        cellwid.setText("주문취소")
                    # item = QTableWidgetItem(str(rowData[value]))
                    label = QLabel(str(rowData[value]))
                    label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
                    # self.stockTable.setItem(row +1, col, item)
                    self.stockTable.setCellWidget(row +1, col, label)
            else :
                for col, value in enumerate(tableItems):
                    item = self.stockTable.item(row +1, col)
                    item.setText(str(rowData[value]))
        for row in canceledOrds:
            self.stockTable.removeRow(row)
        self.setTbGeometry(self.stockTable, 15, 100)
        self.setTbStyle(self.stockTable)
        
    def searchTable(self, table, ordNo):
        result = {'isExist': False}
        for row in range(self.stockTable.rowCount()):
            # item = table.item(row, 0)
            item = table.cellWidget(row, 0)
            if item and item.text() == ordNo :
                result['isExist'] = True
                result['posRow'] = row
        return result
    def selectAccount(self, mode):
        if mode == "direct":
            accountNo = self.combo_box.currentText()
        else :
            accountNo = self.sender().currentText()
            
        self.mainWin.thisAccountNo = accountNo
    
    def getStockList(self):
        if hasattr(self.mainWin, "myAssetInfos"):
            data = {}
            data['purpose'] = "계좌조회"
            data['accountNo'] = self.mainWin.thisAccountNo
            data['accountPw'] = ''
            if len(self.mainWin.myAssetInfos) == 0 :
                data['accountCheck'] = True
            self.mainWin.callApi(data)
        #self.mainWin.hogawin_data : 
        """
        # 즉, 호가창에서 계좌조회할 떄도 미리 계좌주문정보(현재 미요청)도 같이 넣도록 작성해야할 듯.
        """
    def setTbStyle(self, target, policy = None):
        if isinstance(target, QTableWidget):
            policy = QtCore.Qt.ScrollBarAlwaysOff if policy == None else 1
            target.setVerticalScrollBarPolicy(policy)
            target.setHorizontalScrollBarPolicy(policy)
            target.verticalHeader().setVisible(False)
            target.horizontalHeader().setVisible(False)
            target.setEditTriggers(QTableWidget.NoEditTriggers) #테이블 직접수정 불가
            target.setStyleSheet("""
                QTableWidget { border : none; gridline-color: rgba(255, 255, 255, 0);}
                QTableWidget::item:selected { background-color: rgba(255, 255, 255, 0); color:black; }
                QLabel {border : none; gridline-color: white;}
            """) #테두리제거
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
            