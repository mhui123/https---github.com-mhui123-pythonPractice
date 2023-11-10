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
    def __init__(self):
        super().__init__()
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1") #키움API 통신용 변수
        self.stockName = ""
        self.stockCode = ""
        self.needSelectData = ""
        self.selectedData = ""
        self.addedCnt = 0
        self.testVal = 1
        self.hoga_dict = {}
        
        self.loginEvent()
        self.setWindowTitle("hogaHelper")
        self.setGeometry(300,300,300,200)
        
        """ocx 이벤트구간"""
        self.ocx.OnReceiveTrData.connect(self.receive_trdata) #이벤트 처리
        self.ocx.OnReceiveMsg.connect(self.received_msg) #수신 메시지 처리
        self.ocx.OnReceiveRealData.connect(self._handler_real_data) #실시간 데이터 처리
        
        #종목코드 입력란
        label = QLabel("종목명: ", self)
        self.code_edit=QLineEdit(self)
        # self.code_edit.setText("039490") #종목코드 입력란
        searchBtn = QPushButton("조회", self)
        
        # testBtn = QPushButton("test", self)
        # testBtn2 = QPushButton("실시간 해제", self)
        # testBtn3 = QPushButton("popup test", self)
        # testBtn.move(280, 20)
        # testBtn2.move(280, 60)
        # testBtn3.move(280, 90)
        # testBtn.clicked.connect(self.hoga_test)
        # testBtn2.clicked.connect(self.DisConnectRealData)
        # testBtn3.clicked.connect(self.openPopup)
        
        
        self.code_edit.textChanged.connect(self.typing) #텍스트 입력하는 동시에 이벤트 발생
        self.code_edit.returnPressed.connect(self.pressEnter) #엔터를 입력해야 인식하는 이벤트 returnPressed editingFinished
        # self.code_edit.returnPressed.connect(lambda: self.pressEnter()) #엔터이벤트 2
        
        searchBtn.clicked.connect(self.searchBtn_clicked)
        
        
        label.move(20, 20)
        self.code_edit.move(80, 20)
        searchBtn.move(190, 20)
        
        
        self.text_edit = QTextEdit(self)
        self.text_edit.setGeometry(10,60,280,80)
        self.text_edit.setEnabled(False)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.code_edit)
    
    def update_data_test(self, newVal):
        self.testVal = newVal
        self.dataChanged.emit(QVariant(self.testVal))
        
    def update_hoga(self):
        self.dataChanged.emit(self.hoga_dict)
    
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
        inputText = self.code_edit.text().upper()
        toFind = [item for item in self.needSelectData if item['name'] == inputText][0] if len([item for item in self.needSelectData if item['name'] == inputText]) > 0 else False
        if toFind :
            self.stockCode = toFind['code']
            self.stockName = toFind['name']
            if len(self.stockCode) > 0:
                code = self.stockCode
                self.requestData("opt10001", "종목코드", code, "0101")
                self.hoga_test()
        
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
            self.openPopup()
        elif hourMin > 0 and hourMin < 900:
            self.text_edit.append("장 시작전입니다. 수동으로 데이터를 호출합니다.")
            self.requestData("opt10004", "종목코드", code, "0111")
        else :
            print("장 마감되었습니다. 수동호출로 데이터를 요청합니다.")
            self.requestData("opt10004", "종목코드", code, "0111")
        # 41:매도호가1 61:매도호가수량1 81:매도호가직전대비1;51:매수호가1;71:매수호가수량1;91:매수호가직전대비1
        
    def loginEvent(self):
        self.ocx.dynamicCall("CommConnect()")
        self.ocx.OnEventConnect.connect(self.loginResult)
        
    def loginResult(self, err_code):
        errCodes = {"0" : "로그인 성공", "101" : "정보교환 실패", "102" : "서버접속 실패", "103" : "버전처리 실패"}
        self.statusBar().showMessage(errCodes[str(err_code)])
            
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
            self.text_edit.append(f"종목명 : {name}({self.stockCode})")
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
            #'150407\t+157000\t+1400\t+0.90\t+157100\t+157000\t-6\t513591\t80730\t+156700\t+158700\t+155800\t2\t-731658\t-115546970500\t-41.24\t0.35\t362\t79.37\t229852\t2\t0\t-41.13\t000000\t000000\t4421\t090013\t090921\t100140\t280474\t222618\t-44.25\t15077\t7039\t-942\t-6\t 0\t-6\t62800\t50240\t157187\t788\t630'
            #'151133\t+157500\t+1900\t+1.22\t+157500\t+157400\t+24\t532229\t83661\t+156700\t+158700\t+155800\t2\t-713020\t-112615784100\t-42.74\t0.36\t364\t80.63\t230584\t2\t0\t-42.62\t000000\t000000\t4519\t090013\t090921\t100140\t288846\t232884\t-44.64\t15416\t7289\t+3780\t 0\t+24\t+24\t63000\t50400\t157190\t791\t632'
            str = data.split('\t')
            nowTime = str[0]
            amtChange = str[6]
            tradeAmt = str[7]
            todayStart = str[9]
            todayHigh = str[10]
            todayLow = str[11]
            
            
            
            #['150540', '+157200', '+1600', '+1.03', '+157300', '+157200', '-57', '517418', '81331', '+156700', '+158700', '+155800', '2', '-727831', ...]
            fString = f"주식체결 ::: {self.stockName}( {code} )"
            fInfos = f"현재시간: {nowTime}\n 거래량변동:{amtChange}\t거래량:{tradeAmt}\t 시작가:{todayStart}\t 고가:{todayHigh}\t 저가:{todayLow}\t"
            print(fString, fInfos)
        if real_type == "주식우선호가":
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

        self.sellPrices = []
        self.sellAmts = []
        self.buyPrices = []
        self.buyAmts = []
        self.sellChanges = []
        self.buyChanges = []
        self.sPs = []
        self.bPs = []
        self.mode = "price"
        
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
        self.setGeometry(620,300,300,660)
        #self.setGeometry(300,300,300,200)
        self.c_hoga_dict = {}
        
        self.changeModeBtn = QPushButton("수량으로 보기", self)
        self.changeModeBtn.setGeometry(100, 615, 100, 30)
        self.changeModeBtn.clicked.connect(self.changeMode)
        
        # sendTestBtn.move(20,20)
        
        # print(parent_data)

        #호가테이블생성
        
        self.tableWidget = QTableWidget(self)
        self.tableWidget.resize(290, 620)
        self.tableWidget.setColumnCount(3) # 3열
        self.tableWidget.setRowCount(20) # 20행
        
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.horizontalHeader().setVisible(False)

        #self.tableWidget.setAlternatingRowColors(True)
        self.tableWidget.setColumnWidth(0, int(self.tableWidget.width() * 0.4))
        self.tableWidget.setColumnWidth(1, int(self.tableWidget.width() * 0.2))
        self.tableWidget.setColumnWidth(2, int(self.tableWidget.width() * 0.4)) 
        
        #가로스크롤바 제거
        self.tableWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        
        # price 
        for i in range(20):
            price = 0
            item = QTableWidgetItem(format(price, ","))
            item.setTextAlignment(int(Qt.AlignRight|Qt.AlignVCenter))
            self.tableWidget.setItem(i, 1, item)

        # quantity
        # asks
        for i in range(10):
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
            self.tableWidget.setCellWidget(i, 0, widget)

            # set data 
            pbar.setRange(0, 100000000)
            pbar.setFormat(str(quantity))
            pbar.setValue(quantity)

        # bids
        for i in range(10, 20):
            quantity = 0

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
            self.tableWidget.setCellWidget(i, 2, widget)

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
            
    def updateTable(self):
        #수량 최대값 구하기용 리스트 제작
        for i in range(10):
            self.sPs.append(int(self.c_hoga_dict[self.sellAmts[i]]))
            self.bPs.append(int(self.c_hoga_dict[self.buyAmts[i]]))
            
        sMax = max(self.sPs)
        bMax = max(self.bPs)
        realMax = sMax if sMax > bMax else bMax
        
        #update 매도가격과 호가
        for i in range(10):
            # print(f"{new_data[self.sellPrices[i]]} {new_data[self.sellAmts[i]]} {new_data[self.sellChanges[i]]}")
            # print(f"{new_data[self.buyPrices[i]]} {new_data[self.buyAmts[i]]} {new_data[self.buyChanges[i]]}")
            
            #가격 업데이트
            # item = QTableWidgetItem(format(price, ","))
            purePrice = int(re.sub(r'[+-]', '', self.c_hoga_dict[self.sellPrices[i]]))
            sAmt = int(self.c_hoga_dict[self.sellAmts[i]])
            sP = self.tableWidget.item(i, 1)
            sP.setText(format(purePrice, ","))
            sQ = self.tableWidget.cellWidget(i, 0)
            sQBar = sQ.findChild(QProgressBar)
            calToWon = purePrice * int(self.c_hoga_dict[self.sellAmts[i]])
            wonTxt = str(calToWon) if not isinstance(self.print10T(calToWon), str) else self.print10T(calToWon)
            calToWon = format(purePrice * sAmt, ",")
            
            if isinstance(sQBar, QProgressBar):
                sQBar.setRange(0, realMax)
                # sQBar.setFormat(new_data[self.sellAmts[i]])
                if self.mode == "price" :
                    sQBar.setFormat(wonTxt)
                else : sQBar.setFormat(format(sAmt, ","))
                sQBar.setValue(sAmt)
        
        #update 매수가격과 호가
        for i in range(10,20):
            idx = i - 10
            purePrice = int(re.sub(r'[+-]', '', self.c_hoga_dict[self.buyPrices[idx]]))
            bP = self.tableWidget.item(i, 1)
            bP.setText(format(purePrice, ","))
            bQ = self.tableWidget.cellWidget(i, 2)
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
        self.parent.DisConnectRealData()
        
def main():
    app = QApplication(sys.argv)
    window = MyWin()
    window.show()
    # app.exec_()
    sys.exit(app.exec_())

if __name__ == "__main__":  
    main()