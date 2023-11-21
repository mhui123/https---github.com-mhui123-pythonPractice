from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QVariant

#계좌별 자산, 주문현황 window
class AssetWin(QWidget):
    def __init__(self, parent):
        super().__init__()  # 수정: QWidget 클래스의 생성자에 self를 전달
        
        self.mainWin = parent
        self.SCREEN_NO = "0150"
        self.initUI()
        self.getStockList()

    def initUI(self):
        self.setWindowTitle("테스트")
        self.setGeometry(15,15,800,760)
        
        windowW = self.width()
        windowH = self.height()
        self.frame = QFrame(self)
        self.frame.setGeometry(5, 5, windowW - 10, windowH - 10)
        self.frame.setStyleSheet(u"border: 1px solid rgba(0,0,0,255);background-color: rgba(255, 255, 255, 0);margin-left:5px;")
        #self.setGeometry(300,300,300,200)
        testBtn = QPushButton("test", self)
        testBtn.setGeometry(30,30,100,20)
        testBtn.clicked.connect(self.callRealAsset)
        
        self.combo_box = QComboBox(self)
        self.combo_box.currentIndexChanged.connect(self.selectAccount)
        accounts = self.mainWin.accounts
        for item in accounts :
            self.combo_box.addItem(item)
            
        self.mainWin.assetInfoChanged.connect(self.gridStockList)
        
        self.stockTable = QTableWidget(self)
        self.stockTable.setColumnCount(8)
        
        tbHeaders = ['종목명', '수량', '평균단가', '현재가', '평가금액', '손익', '손익율', '매수금액']
        self.stockTable.insertRow(0)
        for i in range(self.stockTable.columnCount()):
            item = QTableWidgetItem(tbHeaders[i])
            item.setTextAlignment(int(Qt.AlignRight|Qt.AlignVCenter))
            self.stockTable.setItem(0, i, item)
            
        self.setTbStyle(self.stockTable)
        self.setTbGeometry(self.stockTable, 15, 100)
        
    
    def test(self):
        testCd = '068270'
        self.mainWin.writeLog(f"{testCd} 현재가변경이벤트 테스트 시작")
        self.mainWin.SetRealReg(self.SCREEN_NO, testCd, "10;", 0)
        # print(f"{self.mainWin.myAssetInfos}")
    def callRealAsset(self, stockCd):
        stockCds = [item['stockCd'] for item in self.mainWin.myAssetInfos[self.mainWin.thisAccountNo]['assets']]
        print(f"{stockCds}")
    def gridStockList(self):
        charge = self.mainWin.charge[self.mainWin.MODE]
        assets = self.mainWin.myAssetInfos[self.mainWin.thisAccountNo]['assets']
        self.stockTable.setRowCount(len(assets) + 1)
        tableItems = ['stockNm','qty','avgPrice','nowPrice','evalPrice','earnPrice','earnRate','boughtTotal']
        # evalPrice = (nowPrice * qty) - (avgPrice * qty) - (nowPrice * (charge['fee'] * 2)) - (nowPrice * (charge['tax']))
        for row, rowData in enumerate(assets):
            stockNm = assets[row]['stockNm']
            isExist = self.searchTable(stockNm)['isExist']
            nowTot = rowData['avgPrice'] * rowData['qty']
            taxTot = rowData['nowPrice'] * rowData['qty']
            fee = int(nowTot * (charge['fee'] * 2) / 10) * 10
            tax = int(round(taxTot * (charge['tax'])))
            if isExist == False :
                self.stockTable.insertRow(row +1)
                for col, value in enumerate(tableItems) :
                    item = QTableWidgetItem(str(rowData[value]))
                    item.setTextAlignment(int(Qt.AlignRight|Qt.AlignVCenter))
                    self.stockTable.setItem(row +1, col, item)
            else :
                earnPrice = (rowData['nowPrice'] * rowData['qty']) - (rowData['avgPrice'] * rowData['qty']) - fee - tax
                earnRate = round((earnPrice / rowData['nowPrice']) * 100, 2)
                rowData['earnPrice'] = earnPrice
                rowData['earnRate'] = earnRate
                # print(f"테이블수정 {stockNm} ({rowData['nowPrice']} * {rowData['qty']}) - ({rowData['avgPrice']} * {rowData['qty']}) - ({fee}) - ({tax}) = {earnPrice}\n {charge['fee']} : {charge['tax']}")
                for col, value in enumerate(tableItems):
                    item = self.stockTable.item(row +1, col)
                    item.setText(str(rowData[value]))
        self.setTbGeometry(self.stockTable, 15, 100)
        # self.mainWin.
            # for j in range(len(tableItems)) :
            #     item = QTableWidgetItem(str(assets[i][tableItems[j]]))
            #     item.setTextAlignment(int(Qt.AlignRight|Qt.AlignVCenter))
            #     self.stockTable.insertRow(1)
            #     self.stockTable.setItem(i +1, j, item)
            #     print(f"[테이블세팅] ({self.stockTable.rowCount()} {self.stockTable.columnCount()})  r : {i} c : {j} {str(assets[i][tableItems[j]])}")
        
        
    #{'stockCd': 'A005930', 'stockNm': '삼성전자', 'qty': 1, 'avgPrice': 72800, 'nowPrice': 72700, 'evalPrice': 72055, 'earnPrice': -745, 'earnRate': -1.02, 'loanDate': '', 'boughtTotal': 72800, 'paymentBalance': 0}
    # 'stockNm' 'qty' 'avgPrice' 'nowPrice' 'evalPrice' 'earnPrice' 'earnRate' 'boughtTotal'
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
            
    def searchTable(self, value):
        result = {'isExist': False}
        for row in range(self.stockTable.rowCount()):
            item = self.stockTable.item(row, 0)
            if item and item.text() == value :
                result['isExist'] = True
                result['posRow'] = row
        return result
    
    def closeEvent(self, event):
         self.mainWin.DisConnectRealData(self.SCREEN_NO, "")