import sys, os
import json
import datetime
import re
import platform
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QVariant

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

bitness = platform.architecture()[0]
if bitness == '32bit' : 
    print("run in 32bit")
elif bitness == '64bit' :
    print("run in 64bit")
else :
    print(f"undetermined platform ::: {bitness}")

class MyWin(QMainWindow):
    dataChanged = pyqtSignal(QVariant)
    stockInfoChanged = pyqtSignal(QVariant)
    def __init__(self):
        super().__init__()
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1") #키움API 통신용 변수
        self.stockName = ""
        self.stockCode = ""
        self.stockMaxPrice = 0
        self.stockMinPrice = 0
        self.nowP = 0 #현재가
        self.nowTAmt = 0 #거래량
        self.nowChangePer = 0 #등락률
        self.nowChangePrice = 0 #전일대비
        
        self.needSelectData = ""
        self.selectedData = ""
        self.addedCnt = 0
        self.testVal = 1
        self.hoga_dict = {}
        self.stock_info = {}
        self.loginPassed = False
        
        self.loginEvent()
        """ocx 이벤트구간"""
        self.ocx.OnReceiveTrData.connect(self.receive_trdata) #이벤트 처리
        self.ocx.OnReceiveMsg.connect(self.received_msg) #수신 메시지 처리
        self.ocx.OnReceiveRealData.connect(self._handler_real_data) #실시간 데이터 처리
        
        self.setWindowTitle("hogaHelper")
        self.setGeometry(300,300,300,200)
        
        #종목코드 입력란
        label = QLabel("종목명: ", self)
        self.code_edit=QLineEdit(self)
        # self.code_edit.setText("039490") #종목코드 입력란
        searchBtn = QPushButton("조회", self)
        

        
        
        self.code_edit.textChanged.connect(self.typing) #텍스트 입력하는 동시에 이벤트 발생
        self.code_edit.returnPressed.connect(self.pressEnter) #엔터를 입력해야 인식하는 이벤트 returnPressed editingFinished
        # self.code_edit.returnPressed.connect(lambda: self.pressEnter()) #엔터이벤트 2
        searchBtn.clicked.connect(self.searchBtn_clicked)
        
        label.move(20, 20)
        searchBtn.move(190, 20)
        self.code_edit.move(80, 20)
        
        self.text_edit = QTextEdit(self)
        self.text_edit.setGeometry(10,60,280,80)
        self.text_edit.setEnabled(False)
        
        #검색어완성 위젯
        layout = QVBoxLayout(self)
        layout.addWidget(self.code_edit)
        
    def loginEvent(self):
        self.ocx.dynamicCall("CommConnect()")
        self.ocx.OnEventConnect.connect(self.loginResult)
        
    def loginResult(self, err_code):
        errCodes = {"0" : "로그인 성공", "101" : "정보교환 실패", "102" : "서버접속 실패", "103" : "버전처리 실패"}
        self.statusBar().showMessage(errCodes[str(err_code)])
        if errCodes[str(err_code)] == "로그인 성공":
            self.loginPassed = True
    
    def update_data_test(self, newVal):
        self.testVal = newVal
        self.dataChanged.emit(QVariant(self.testVal))
        
    def update_hoga(self):
        self.dataChanged.emit(self.hoga_dict)
        self.stockInfoChanged.emit(self.stock_info)
    
    def testBtn2Clicked(self):
        self.DisConnectRealData("0101")
        print("실시간통신 해제 : 0101")
    
    def test(self):
        print("test")
    
    def typing(self):
        word_list = []
        
        text = self.code_edit.text().upper()
        if len(text) > 0:
            self.code_edit.setCursorPosition(len(text) +1)
            filtered_data = [item for item in data if item["name"].find(text) != -1] # string.find(txt) == -1이면 해당 텍스트 없음
            if(len(filtered_data) > 15) :
                filtered_data = filtered_data[:15]
            
            #자동완성 항목들 json에서 추출
            filtered_name = [item['name'] for item in filtered_data]
            word_list = filtered_name
            completer = QCompleter(word_list, self)
            completer.setCaseSensitivity(0) #대소문자 미구문
            completer.setFilterMode(Qt.MatchContains) #중간일치여부 필터링
            self.code_edit.setCompleter(completer)
            
            self.needSelectData = filtered_data #추출된 데이터 needSelectData에 바인딩
        
    def pressEnter(self):
        if self.loginPassed == True :
            inputText = self.code_edit.text().upper()
            toFind = [item for item in self.needSelectData if item['name'] == inputText][0] if len([item for item in self.needSelectData if item['name'] == inputText]) > 0 else False
            if toFind :
                self.stockCode = toFind['code']
                self.stockName = toFind['name']
                if len(self.stockCode) > 0:
                    code = self.stockCode
                    self.requestData("opt10001", "종목코드", code, "0101")
                    self.hoga_test()
        else :
            self.showAlert("로그인 대기중입니다.")
            
    def showAlert(self, msg):
        alert = QMessageBox()
        alert.setIcon(QMessageBox.Information)
        alert.setWindowTitle("경고")
        alert.setText(msg)
        alert.setStandardButtons(QMessageBox.Ok)
        
        # Executing the QMessageBox
        result = alert.exec_()
        #CommConnect(사용자 호출) -> 로그인창 출력 -> OnEventConnect(이벤트 발생)
    def searchBtn_clicked(self):
        inputText = self.code_edit.text().upper()
        toFind = [item for item in self.needSelectData if item['name'] == inputText][0] if len([item for item in self.needSelectData if item['name'] == inputText]) > 0 else False
        if toFind :
            self.pressEnter()
        else :
            self.text_edit.append("정확한 종목명을 입력하여 조회해주세요.")
    
    def hoga_test(self):
        code = self.stockCode
        current_time = datetime.datetime.now()
        hourMin = int(current_time.strftime("%H%M"))
        
        if hourMin < 1530 and hourMin >= 900:
            self.SetRealReg("0111", code, "41;", 0) #0 : 신규요청 1: 추가요청
            # self.requestData("opt10004", "종목코드", code, "0111")
            self.openPopup()
        elif hourMin > 0 and hourMin < 900:
            self.text_edit.append("장 시작전입니다. 수동으로 데이터를 호출합니다.")
            self.requestData("opt10004", "종목코드", code, "0111")
        else :
            print("장 마감되었습니다. 수동호출로 데이터를 요청합니다.")
            self.requestData("opt10004", "종목코드", code, "0111")
        # 41:매도호가1 61:매도호가수량1 81:매도호가직전대비1;51:매수호가1;71:매수호가수량1;91:매수호가직전대비1
            
    def received_msg(self, screenNo, rqName, trCode, msg):
        print("받아온 메세지 출력 :" + screenNo, rqName, trCode, msg)
    
    def requestData(self, trCode, itemNm, code, screenNo, isContinue = 0):
        isContinue = 2 if isContinue == "연속" else 0
        rqName = trCode+"_req"
        #조회요청 시 SetInputValue로 parameter지정 후 CommRqData로 요청한다.
        self.ocx.dynamicCall("SetInputValue(QString, QString)", itemNm, code)
        self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)",rqName, trCode, isContinue, screenNo)
    
    def receive_trdata(self, screenNo, rqName, trCode, recordName, preNext):
        #복수데이터의 경우 idx가 항목 순서이다.
        nCnt = self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trCode, rqName)
        # for i in range(0, nCnt):
        if rqName == "opt10001_req":
            name = self.getCommData(trCode, rqName, "종목명")
            self.stockMaxPrice = self.getCommData(trCode, rqName, "상한가").strip()
            self.stockMinPrice = self.getCommData(trCode, rqName, "하한가").strip()
            self.nowP = self.getCommData(trCode, rqName, "현재가").strip()
            self.nowTAmt = self.getCommData(trCode, rqName, "거래량").strip()
            self.nowChangePer = self.getCommData(trCode, rqName, "등락율").strip()
            self.nowChangePrice = self.getCommData(trCode, rqName, "전일대비").strip()
            self.text_edit.append(f"종목명 : {name.strip()}({self.stockCode})")
            # volume = self.getCommData(trCode, rqName, "거래량")
            # self.text_edit.append("거래량 :" + volume.strip())
        else :
            outputParams = ["호가잔량기준시간",
                            "매도10차선잔량", "매도10차선호가","매도9차선잔량", "매도9차선호가","매도8차선잔량", "매도8차선호가","매도7차선잔량", "매도7차선호가","매도6우선잔량", "매도6차선호가",
                            "매도5차선잔량", "매도5차선호가","매도4차선잔량", "매도4차선호가","매도3차선잔량", "매도3차선호가","매도2차선잔량", "매도2차선호가","매도최우선잔량", "매도최우선호가",
                            
                            "매수최우선잔량", "매수최우선호가","매수2차선잔량", "매수2차선호가","매수3차선잔량", "매수3차선호가","매수4차선잔량", "매수4차선호가","매수5차선잔량", "매수5차선호가",
                            "매수6우선잔량", "매수6우선호가","매수7차선잔량", "매수7차선호가","매수8차선잔량", "매수8차선호가","매수9차선잔량", "매수9차선호가","매수10차선잔량", "매수10차선호가",
                            
                            "총매도잔량", "총매수잔량","시간외매도잔량","시간외매수잔량"
                            ]
            convertForm = {
                "매도10차선잔량":"매도호가수량10","매도10차선호가":"매도호가10",
                "매도9차선잔량":"매도호가수량9","매도9차선호가":"매도호가9",
                "매도8차선잔량":"매도호가수량8","매도8차선호가":"매도호가8",
                "매도7차선잔량":"매도호가수량7","매도7차선호가":"매도호가7",
                "매도6우선잔량":"매도호가수량6","매도6차선호가":"매도호가6",
                "매도5차선잔량":"매도호가수량5","매도5차선호가":"매도호가5",
                "매도4차선잔량":"매도호가수량4","매도4차선호가":"매도호가4",
                "매도3차선잔량":"매도호가수량3","매도3차선호가":"매도호가3",
                "매도2차선잔량":"매도호가수량2","매도2차선호가":"매도호가2",
                "매도최우선잔량":"매도호가수량1","매도최우선호가":"매도호가1",
                
                "매수최우선잔량":"매수호가수량1","매수최우선호가":"매수호가1",
                "매수2차선잔량":"매수호가수량2","매수2차선호가":"매수호가2",
                "매수3차선잔량":"매수호가수량3","매수3차선호가":"매수호가3",
                "매수4차선잔량":"매수호가수량4","매수4차선호가":"매수호가4",
                "매수5차선잔량":"매수호가수량5","매수5차선호가":"매수호가5",
                "매수6우선잔량":"매수호가수량6","매수6우선호가":"매수호가6",
                "매수7차선잔량":"매수호가수량7","매수7차선호가":"매수호가7",
                "매수8차선잔량":"매수호가수량8","매수8차선호가":"매수호가8",
                "매수9차선잔량":"매수호가수량9","매수9차선호가":"매수호가9",
                "매수10차선잔량":"매수호가수량10","매수10차선호가":"매수호가10",
            }
            """
                self.hoga_dict[key] = result
            """
            for item in outputParams :
                result = self.getCommData(trCode, rqName, item)
                #호가잔량기준시간 : hhMMss
                if convertForm.get(item) is not None :
                    key = convertForm[item]
                    self.hoga_dict[key] = result.strip()
            
            self.openPopup()
            self.update_hoga()
      
    def getCommData(self, trCode, recordName, itemNm, idx = 0):
        return self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trCode, recordName, idx, itemNm)
    
    #실시간 데이터 ON
    def SetRealReg(self, screen_no, code_list, fid_list, real_type):
        print(screen_no + "실시간데이터 요청시작")
        self.ocx.dynamicCall("SetRealReg(QString, QString, QString, QString)", 
                              screen_no, code_list, fid_list, real_type)
        self.statusBar().showMessage("실시간데이터 ON")

    #실시간 데이터 OFF
    def DisConnectRealData(self, screen_no=""):
        screen_no
        code = self.stockCode
        # self.ocx.dynamicCall("DisConnectRealData(QString)", screen_no)
        self.ocx.dynamicCall("SetRealRemove(QString, QString)", "ALL", "ALL")
        self.statusBar().showMessage("실시간데이터 OFF")
    
    #실시간 데이터 처리
    def _handler_real_data(self, code, real_type, data):
        if real_type == "주식호가잔량":
            # 시작지점부터 20개
            # 필요정보는 41번부터 100번까지 모두 필요하므로 60개를 전부 호출할 것.
            startPoint = 41
            self.hoga_dict = {}
            cnt = 1
            for i in range(60):
                reqCode = startPoint + i
                result = self.GetCommRealData(code, reqCode)
                key = ""
                if reqCode <= 50:
                    key = f"매도호가{cnt}"
                elif reqCode <= 60:
                    if reqCode == 51 : cnt = 1
                    key = f"매수호가{cnt}"
                elif reqCode <= 70:
                    if reqCode == 61 : cnt = 1
                    key = f"매도호가수량{cnt}"
                elif reqCode <= 80:
                    if reqCode == 71 : cnt = 1
                    key = f"매수호가수량{cnt}"
                elif reqCode <= 90:
                    if reqCode == 81 : cnt = 1
                    key = f"매도직전대비{cnt}"
                elif reqCode <= 100:
                    if reqCode == 91 : cnt = 1
                    key = f"매수직전대비{cnt}"
                cnt += 1
                self.hoga_dict[key] = result
            self.update_hoga()
            # for key,val in toSend.items():
            #     print(f"{key} : {val}")
        if real_type == "주식체결":
            nowTime = self.GetCommRealData(code, 20)
            todayStart = self.GetCommRealData(code, 16)
            todayHigh = self.GetCommRealData(code, 17)
            todayLow = self.GetCommRealData(code, 18)
            tradeAmt = self.GetCommRealData(code, 15) #+는 매수체결 -는 매도체결
            
            nowPrice = self.GetCommRealData(code, 10)
            accAmt = self.GetCommRealData(code, 13)
            accPrice = self.GetCommRealData(code, 14)
            priceChange = self.GetCommRealData(code, 11)
            movePercent = self.GetCommRealData(code, 12)
            
            self.stock_info["nowTime"] = nowTime
            self.stock_info["todayStart"] = todayStart
            self.stock_info["todayHigh"] = todayHigh
            self.stock_info["todayLow"] = todayLow
            self.stock_info["tradeAmt"] = tradeAmt
            
            self.stock_info["nowPrice"] = nowPrice
            self.stock_info["accAmt"] = accAmt
            self.stock_info["accPrice"] = accPrice
            self.stock_info["priceChange"] = priceChange
            self.stock_info["movePercent"] = movePercent
            
            #['150540', '+157200', '+1600', '+1.03', '+157300', '+157200', '-57', '517418', '81331', '+156700', '+158700', '+155800', '2', '-727831', ...]
            fString = f"주식체결 ::: {self.stockName}( {code} )"
            fInfos = f" {self.stockName} 현재가:{nowPrice} 누적거래량 {accAmt} 누적거래대금 {accPrice} 가격변동:{priceChange} 등락률:{movePercent}"
            # print(fString, fInfos)
        if real_type == "주식우선호가":
            #호가틱이 변동될 때 발생하는 이벤트.
            now = datetime.datetime.now()
            ask01 =  self.GetCommRealData(code, 27)         
            bid01 =  self.GetCommRealData(code, 28)
            print(f"현재시간 {now} | 최우선매도호가: {ask01} 최우선매수호가: {bid01}")
            
    def GetCommRealData(self, code, fid):
        data = self.ocx.dynamicCall("GetCommRealData(QString, int)", code, fid) 
        return data
        
    def getMarketInfo(self):
        #GetCodeListByMarket(gubun) : 종목코드 리스트 호출 # 구분값 없을 시 전체 코드리스트
        gubun = {
            "코스피": 0,
            "코스닥": 10,
            "ELW": 3,
            "ETF": 8,
            "KONEX": 50,
            "뮤추얼펀드": 4,
            "신주인수권": 5,
            "리츠": 6,
            "하이얼펀드": 9,
            "K-OTC": 30
        }
        result = self.ocx.dynamicCall("GetCodeListByMarket(QString)", gubun["코스닥"])
        arr = result.split(";")
        name = list(map(self.getStockName, arr))
        nameString = ";".join(name)
        nameString
        
        # code_list = self.dynamicCall("GetCodeListByMarket(QString)", market)
    
    def getStockName(self, code):
        stockName = self.ocx.dynamicCall("GetMasterCodeName(QString)", code)
        return stockName
    
    def openPopup(self):
        toPassData = self.testVal
        self.newWindow = NewWindow(self, toPassData)
        self.newWindow.show()
    
    def receiveDataFromChild(self, data):
        print(data)
    
    # 창 종료이벤트
    def closeEvent(self, event):
        if hasattr(self, "newWindow"): # self에 팝업변수 존재 체크
            if isinstance(self.newWindow, QWidget):
                if hasattr(self.newWindow, "hogaOrderwin"): # self에 팝업변수 존재 체크
                    self.newWindow.hogaOrderwin.close()
            self.newWindow.close()
        event.accept() #프로그램 종료 . 이벤트 회수?

class NewWindow(QWidget):
    # def __init__(self, parent: QWidget | None = ..., flags: WindowFlags | WindowType = ...) -> None:
    #     super().__init__(parent, flags)
    def __init__(self, parent, parent_data):
        super().__init__()  # 수정: QWidget 클래스의 생성자에 self를 전달
        self.parent = parent
        self.initUI(parent_data)
        parent.dataChanged.connect(self.on_data_changed)
        parent.stockInfoChanged.connect(self.on_stock_info_changed)

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
        self.setWindowTitle("호가창")
        self.setGeometry(620,300,300,760)
        #self.setGeometry(300,300,300,200)
        self.c_hoga_dict = {}
        
        self.changeModeBtn = QPushButton("수량으로 보기", self)
        self.changeModeBtn.setGeometry(100, 675, 100, 30)
        self.changeModeBtn.clicked.connect(self.changeMode)
        
        # sendTestBtn.move(20,20)
        
        # print(parent_data)
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
        
        
    def on_data_changed(self, new_data):
        if type(new_data) is dict:
            self.c_hoga_dict = new_data
            # print(f"부모창 값 변경 테스트 : {self.c_hoga_dict}")
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
        text = ""
        if col == 2 :
            text = int(re.sub(r'[,]', '', item.text()))
            toPassData = {"hoga_interval" : self.hoga_interval, "price" : text}
            self.hogaOrderwin = HogaOrderWin(self, toPassData)
            self.hogaOrderwin.show()
        print(f"table click : {row} {col} {text}")
        
    def cellClickEvent(self, row,col):
        if col != 2 :
            print(f"{row} {col}")
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
            sP.setText(format(purePrice, ","))
            sQ = self.tableWidget.cellWidget(i, 1)
            sQBar = sQ.findChild(QProgressBar)
            calToWon = purePrice * int(self.c_hoga_dict[self.sellAmts[i]])
            wonTxt = str(calToWon) if not isinstance(self.print10T(calToWon), str) else self.print10T(calToWon)
            calToWon = format(purePrice * sAmt, ",")
            
            if self.hoga_interval == 0 and hoga_interval_chk == 0 :
                hoga_interval_chk = purePrice
            elif self.hoga_interval == 0 and hoga_interval_chk > 0 :
                self.hoga_interval = hoga_interval_chk - purePrice
            
            if isinstance(sQBar, QProgressBar):
                sQBar.setRange(0, realMax)
                # sQBar.setFormat(new_data[self.sellAmts[i]])
                if self.mode == "price" :
                    sQBar.setFormat(wonTxt)
                else : sQBar.setFormat(format(sAmt, ","))
                sQBar.setValue(sAmt)
            
            #표시할 호가수량 변동: self.c_hoga_dict['매도직전대비1~10']
            key = f"매도직전대비{i+1}"
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
            bP.setText(format(purePrice, ","))
            bQ = self.tableWidget.cellWidget(i, 3)
            bQBar = bQ.findChild(QProgressBar)
            bAmt = int(self.c_hoga_dict[self.buyAmts[idx]])
            
            calToWon = purePrice * bAmt
            wonTxt =  str(calToWon) if not isinstance(self.print10T(calToWon), str) else self.print10T(calToWon)
            calToWon = format(purePrice * bAmt, ",")
            
            if isinstance(bQBar, QProgressBar):
                bQBar.setRange(0, realMax)
                # bQBar.setFormat(new_data[self.buyAmts[idx]])
                if self.mode == "price" :
                    bQBar.setFormat(wonTxt)
                else : bQBar.setFormat(format(bAmt, ","))
                bQBar.setValue(bAmt)
            #표시할 호가수량 변동: self.c_hoga_dict['매도직전대비1~10']
            key = f"매수직전대비{idx +1}"
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
        
        
    def testSend(self):
        child_data = "is going from child"
        print(self.parent_data)
        # self.parent.receiveDataFromChild(child_data)
        # self.close() #창 닫기
    
    def closeEvent(self, event):
        if hasattr(self, "hogaOrderWin"): # self에 팝업변수 존재 체크
            self.hogaOrderWin.close()
        self.parent.DisConnectRealData()
        
class HogaOrderWin(QWidget):
    # def __init__(self, parent: QWidget | None = ..., flags: WindowFlags | WindowType = ...) -> None:
    #     super().__init__(parent, flags)
    def __init__(self, parent, parent_data):
        super().__init__()  # 수정: QWidget 클래스의 생성자에 self를 전달
        self.parent = parent
        self.initUI(parent_data)
            
    def initUI(self, parent_data):
        self.parent_data = parent_data
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowTitle("호가주문")
        
        windowW = self.parent.width() + 5
        windowH = int(self.parent.height() * 0.2)
        parent_x = self.parent.x()
        child_y = self.parent.y() + int(self.parent.height() / 2)
        
        self.setGeometry(parent_x, child_y, windowW, windowH)
        print(f"parentData : {parent_data}")
        
        self.tableWidget = QTableWidget(self)
        # self.tableWidget.move(0,60)
        # self.tableWidget.resize(290, 620)
        self.tableWidget.setColumnCount(5) # 3열
        self.tableWidget.setRowCount(2) # 20행
        
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.horizontalHeader().setVisible(False)
        self.tableWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        #self.tableWidget.setAlternatingRowColors(True)
        
        # self.resize(windowW, windowH)
        self.tableWidget.resize(windowW, windowH)
        
        self.tableWidget.setColumnWidth(0, int(self.tableWidget.width() * 0.2))
        self.tableWidget.setColumnWidth(1, int(self.tableWidget.width() * 0.2))
        self.tableWidget.setColumnWidth(2, int(self.tableWidget.width() * 0.2))
        self.tableWidget.setColumnWidth(3, int(self.tableWidget.width() * 0.2))
        self.tableWidget.setColumnWidth(4, int(self.tableWidget.width() * 0.2))
        
        plusWidget = QWidget()
        minusWidget = QWidget()
        plusBtn = QPushButton("+", self)
        minusBtn = QPushButton("-", self)
        item = QTableWidgetItem(format(parent_data['price'],","))
        self.tableWidget.setItem(1, 2, item)
        self.tableWidget.setCellWidget(1, 3, plusBtn)
        self.tableWidget.setCellWidget(1, 1, minusBtn)
        
        plusBtn.clicked.connect(self.btnClicked)
        minusBtn.clicked.connect(self.btnClicked)
        
    def btnClicked(self, event):
        print(f"btnClicked {event}")
        
        
        # print(f"tableW : {self.tableWidget.width()} tableH : {self.tableWidget.height()}")
        # print(f"windowW : {windowW} windowH : {windowH}")
        # print(f"parentW : {self.parent.width()} H : {self.parent.height()}")
        
def main():
    app = QApplication(sys.argv)
    window = MyWin()
    window.show()
    # app.exec_()
    sys.exit(app.exec_())

if __name__ == "__main__":  
    main()