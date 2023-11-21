from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QVariant

#계좌별 자산, 주문현황 window
class OrderInfoPop(QWidget):
    def __init__(self, parent):
        super().__init__()  # 수정: QWidget 클래스의 생성자에 self를 전달
        self.mainWin = parent
        self.originOrdNo = None
        self.trType = None
        
        self.initUI()

    def initUI(self):
        self.setWindowTitle("테스트")
        self.setGeometry(15,15,1400,760)
        
        windowW = self.width()
        windowH = self.height()
        self.frame = QFrame(self)
        self.frame.setGeometry(5, 5, windowW - 10, windowH - 10)
        self.frame.setStyleSheet(u"border: 1px solid rgba(0,0,0,255);background-color: rgba(255, 255, 255, 0);margin-left:5px;")
        #self.setGeometry(300,300,300,200)
        testBtn = QPushButton("test", self)
        testBtn.setGeometry(30,30,100,20)
        testBtn.clicked.connect(self.test)
        fixBtn = QPushButton("정정", self)
        fixBtn.setGeometry(70,30,100,20)
        fixBtn.clicked.connect(self.fixCancel)
        cBtn = QPushButton("취소", self)
        cBtn.setGeometry(100,30,100,20)
        cBtn.clicked.connect(self.fixCancel)
        
        self.mainWin.orderInfoChanged.connect(self.update_orderInfo)
        
        
        """
        #{'주문번호': '0031931', '종목번호': 'A035600', '매매구분': '보통가', '신용구분': '보통매매', '주문수량': 1, '주문단가': 11330, '확인수량': 1, '접수구분': '주문완료
', '반대여부': '', '주문시간': '09:19:55', '원주문': '0000000', '종목명': 'KG이니시스', '주문구분': '현금매수', '대출일': '', '체결수량': 0, '체결단가': 0, '주문잔량': 1, '통신구분': '오픈API', '정정
취소': '일반', '확인시간': '09:19:55'}
        """
        tbHeaders = ['주문번호', '종목명', '매매구분', '주문단가','주문수량','접수구분','주문시간','체결수량', '체결단가', '주문잔량','주문구분', '정정취소', '신용구분', '확인수량',  '반대여부',  '원주문',   '대출일',  '통신구분', '확인시간']
        
        self.stockTable = QTableWidget(self)
        self.stockTable.setColumnCount(len(tbHeaders))
        self.stockTable.insertRow(0)
        for i in range(self.stockTable.columnCount()):
            item = QTableWidgetItem(tbHeaders[i])
            item.setTextAlignment(int(Qt.AlignRight|Qt.AlignVCenter))
            self.stockTable.setItem(0, i, item)
            
        self.stockTable.cellClicked.connect(self.cellClickEvent)
    def update_orderInfo(self):
        print(f"[orderInfo update test] : {self.mainWin.orderInfos}")
        self.gridList()
        
    def test(self):
        print(f"[orderInfo update test] : {self.mainWin.orderInfos[0]}")
        # print(f"{self.mainWin.myAssetInfos}")
    def fixCancel(self):
        txt = self.sender().text()
        if txt == "정정" :
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
    def gridList(self):
        assets = self.mainWin.orderInfos
        self.stockTable.setRowCount(len(assets) + 1)
        tableItems = ['주문번호', '종목명', '매매구분', '주문단가','주문수량','접수구분','주문시간','체결수량', '체결단가', '주문잔량','주문구분', '정정취소', '신용구분', '확인수량',  '반대여부',  '원주문',   '대출일',  '통신구분', '확인시간']
        # evalPrice = (nowPrice * qty) - (avgPrice * qty) - (nowPrice * (charge['fee'] * 2)) - (nowPrice * (charge['tax']))
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
        # self.mainWin.
            # for j in range(len(tableItems)) :
            #     item = QTableWidgetItem(str(assets[i][tableItems[j]]))
            #     item.setTextAlignment(int(Qt.AlignRight|Qt.AlignVCenter))
            #     self.stockTable.insertRow(1)
            #     self.stockTable.setItem(i +1, j, item)
            #     print(f"[테이블세팅] ({self.stockTable.rowCount()} {self.stockTable.columnCount()})  r : {i} c : {j} {str(assets[i][tableItems[j]])}")
        
        
    #{'stockCd': 'A005930', 'stockNm': '삼성전자', 'qty': 1, 'avgPrice': 72800, 'nowPrice': 72700, 'evalPrice': 72055, 'earnPrice': -745, 'earnRate': -1.02, 'loanDate': '', 'boughtTotal': 72800, 'paymentBalance': 0}
    # 'stockNm' 'qty' 'avgPrice' 'nowPrice' 'evalPrice' 'earnPrice' 'earnRate' 'boughtTotal'
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
    def setTbStyle(self, target):
        if isinstance(target, QTableWidget):
            target.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            target.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
            target.verticalHeader().setVisible(False)
            target.horizontalHeader().setVisible(False)
            target.setEditTriggers(QTableWidget.NoEditTriggers) #테이블 직접수정 불가
            target.setStyleSheet("""
                QTableWidget { border : none; gridline-color: white; border-top:10px}
                QTableWidget::item:selected { background-color: rgba(255, 255, 255, 0); color:black; }
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
            