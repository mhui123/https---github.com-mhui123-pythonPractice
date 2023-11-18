import sys, os
import json
import datetime
import re
import platform
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QVariant, QEvent
from HogaWin import *

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

#메인창class
class MyWin(QMainWindow):
    dataChanged = pyqtSignal(QVariant)
    stockInfoChanged = pyqtSignal(QVariant)
    accountInfoChanged = pyqtSignal(QVariant)
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
        self.accounts = None
        self.selected_account = None
        self.account_pw = None
        self.myAssetInfo = []
        
        self.myCash = 0
        self.myUsableCash = 0
        
        self.hogawin_data = None
        
        self.loginEvent()
        """ocx 이벤트구간"""
        self.ocx.OnReceiveTrData.connect(self.receive_trdata) #이벤트 처리
        self.ocx.OnReceiveMsg.connect(self.received_msg) #수신 메시지 처리
        self.ocx.OnReceiveRealData.connect(self._handler_real_data) #실시간 데이터 처리
        self.ocx.OnReceiveChejanData.connect(self.receive_chejan)
        
        self.setWindowTitle("hogaHelper")
        self.setGeometry(300,300,300,200)
        # self.setFixedSize(self.size()) #창크기고정
        
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
        
        self.text_edit = QTextBrowser(self) #QTextEdit(self)
        self.text_edit.setGeometry(10,60,self.width() - 20, int(self.height() * 0.4))
        # self.text_edit.setEnabled(False)
        
        #검색어완성 위젯
        layout = QVBoxLayout(self)
        layout.addWidget(self.code_edit)
        
        testBtn = QPushButton("test", self)
        testBtn.move(190, self.height() - testBtn.height() - self.statusBar().height())
        testBtn.clicked.connect(self.test)
        
        self.isClicked = False
    def writeLog(self, text):
        text += "\n----------------------"
        self.text_edit.append(text)
        
    def loginEvent(self):
        self.ocx.dynamicCall("CommConnect()")
        self.ocx.OnEventConnect.connect(self.loginResult)
        
    def loginResult(self, err_code):
        errCodes = {"0" : "로그인 성공", "101" : "정보교환 실패", "102" : "서버접속 실패", "103" : "버전처리 실패"}
        self.statusBar().showMessage(errCodes[str(err_code)])
        if errCodes[str(err_code)] == "로그인 성공":
            self.loginPassed = True
        account_num = self.ocx.dynamicCall("GetLoginInfo(QString)", "ACCNO")
        self.accounts = []
        accounts = account_num.split(';')
        for item in accounts :
            if len(item) > 0 :
                self.accounts.append(item)
        self.getMyAssetInfo() #보유잔고정보 조회

        # self.ocx.KOA_Functions("ShowAccountWindow","")
        # self.code_edit.append(f"계좌번호 : {account_num}")
    
    def getAccountInfo(self, accNo, accPw): #예수금상세현황요청    
        self.setInputValue("계좌번호", accNo)
        self.setInputValue("비밀번호", "")
        self.setInputValue("조회구분", 2) #2 : 일반조회, 3 : 추정조회
        self.requestData("opw00001", "종목코드", '0', "0362")
    def getOrderInfo(self): #계좌별주문체결내역상세요청
        trCode = "opw00007"
        screenNo = "0351"
        current_time = datetime.datetime.now()
        today = int(current_time.strftime("%Y%m%d"))
        self.setInputValue("주문일자", today)
        self.setInputValue("계좌번호", self.accounts[0])
        self.setInputValue("비밀번호", "")
        self.setInputValue("비밀번호입력매체구분", "00")
        self.setInputValue("조회구분", "1") #1:주문순 2:역순 3:미체결 4:체결내역
        self.setInputValue("주식채권구분", "0") #0:전체 1:주식 2:채권
        self.setInputValue("매도수구분", "0") #0:전체 1:매도 2:매수
        self.setInputValue("종목코드", "") #공백일때 전체
        self.setInputValue("시작주문번호", "") #공백일때 전체
        self.requestData(trCode, "", "", screenNo)
    def getMyAssetInfo(self): #계좌평가현황요청
        for i in range(len(self.accounts)):
            self.setInputValue("계좌번호", self.accounts[i])
            self.setInputValue("비밀번호", "") #사용안함 공백
            self.setInputValue("상장폐지조회구분", 0) # 0:전체, 1:상장폐지종목 제외
            self.setInputValue("비밀번호입력매체구분", "00") # 0:전체, 1:상장폐지종목 제외
            self.setInputValue("조회구분", "2") # 1:합산 2:개별
            # self.requestData("opw00018", "", '0', "0391")
            self.requestData("opw00004", "", '0', "0391")
        # self.ocx.KOA_Functions("ShowAccountWindow","")
                
    def update_hoga(self): #호가창 업데이트
        self.dataChanged.emit(self.hoga_dict)
        self.stockInfoChanged.emit(self.stock_info)
    def update_account_info(self): #호가창 종목정보 업데이트
        toSend = {"myCash" : self.myCash, "myUsableCash" : self.myUsableCash, "hogawinData": self.hogawin_data}
        self.accountInfoChanged.emit(toSend)
    
    def test(self):
        # self.getMyAssetInfo()
        # self.getOrderInfo()
        self.openPopup("test")
    def typing(self): #종목명 타이핑 이벤트
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
        
    def pressEnter(self): #종목명 입력 엔터입력 이벤트
        if self.loginPassed == True :
            inputText = self.code_edit.text().upper()
            toFind = [item for item in self.needSelectData if item['name'] == inputText][0] if len([item for item in self.needSelectData if item['name'] == inputText]) > 0 else False
            if toFind :
                self.stockCode = toFind['code']
                self.stockName = toFind['name']
                if len(self.stockCode) > 0:
                    code = self.stockCode
                    self.requestData("opt10001", "종목코드", code, "0101")
                    self.call_hogaData()
        else :
            showAlert("로그인 대기중입니다.")
            
    def searchBtn_clicked(self): #조회이벤트
        inputText = self.code_edit.text().upper()
        toFind = [item for item in self.needSelectData if item['name'] == inputText][0] if len([item for item in self.needSelectData if item['name'] == inputText]) > 0 else False
        if toFind :
            self.pressEnter()
        else :
            self.text_edit.append("정확한 종목명을 입력하여 조회해주세요.")
    
    def call_hogaData(self): #호가창 호출이벤트
        code = self.stockCode
        current_time = datetime.datetime.now()
        hourMin = int(current_time.strftime("%H%M"))
        
        if hourMin < 1530 and hourMin >= 900:
            self.SetRealReg("0111", code, "41;", 0) #0 : 신규요청 1: 추가요청
            # self.requestData("opt10004", "종목코드", code, "0111")
            # self.openPopup()
        elif hourMin > 0 and hourMin < 900:
            self.text_edit.append("장 시작전입니다. 수동으로 데이터를 호출합니다.")
            # self.requestData("opt10004", "종목코드", code, "0111")
        else :
            print("장 마감되었습니다. 수동호출로 데이터를 요청합니다.")
            # self.requestData("opt10004", "종목코드", code, "0111")
        self.requestData("opt10004", "종목코드", code, "0111")
        # 41:매도호가1 61:매도호가수량1 81:매도호가직전대비1;51:매수호가1;71:매수호가수량1;91:매수호가직전대비1
            
    def received_msg(self, screenNo, rqName, trCode, msg): #서버메세지 수신
        self.writeLog(f"[{screenNo}][{rqName}][{trCode}] : {msg}")
    
    def setInputValue(self, itemName, code): #api 데이터요청용 값 입력
        self.ocx.dynamicCall("SetInputValue(QString, QString)", itemName, code)
    
    def requestData(self, trCode, itemNm, code, screenNo, isContinue = 0): #api 데이터요청
        isContinue = 2 if isContinue == True else 0
        rqName = trCode+"_req"
        #조회요청 시 SetInputValue로 parameter지정 후 CommRqData로 요청한다.
        if len(code) > 0 :
            # self.ocx.dynamicCall("SetInputValue(QString, QString)", itemNm, code)
            self.setInputValue(itemNm, code)
        self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)",rqName, trCode, isContinue, screenNo)
    
    def receive_trdata(self, screenNo, rqName, trCode, recordName, preNext): #API 응답이벤트
        #복수데이터의 경우 idx가 항목 순서이다.
        nCnt = self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trCode, rqName)
        print(f"[receive_trdata] nCnt: {nCnt} trCode:{trCode}, rqName:{rqName}")
        # for i in range(0, nCnt):
        if rqName == "opt10001_req": #종목정보 조회
            name = self.getCommData(trCode, rqName, "종목명")
            self.stockMaxPrice = self.getCommData(trCode, rqName, "상한가").strip()
            self.stockMinPrice = self.getCommData(trCode, rqName, "하한가").strip()
            self.nowP = self.getCommData(trCode, rqName, "현재가").strip()
            self.nowTAmt = self.getCommData(trCode, rqName, "거래량").strip()
            self.nowChangePer = self.getCommData(trCode, rqName, "등락율").strip()
            self.nowChangePrice = self.getCommData(trCode, rqName, "전일대비").strip()
            self.writeLog(f"조회종목 : {name.strip()}({self.stockCode})")
        elif rqName == "opw00001_req": #예수금상세현황요청
            self.myCash = int(self.getCommData(trCode, rqName, "예수금").strip())
            self.myUsableCash = int(self.getCommData(trCode, rqName, "주문가능금액").strip())
            logText = f"예수금요청 예수금:{self.myCash} 주문가능:{self.myUsableCash}"
            self.writeLog(logText)
            self.update_account_info()
        elif rqName == "opw00004_req": #계좌평가현황요청
            # myAssetInfo
            nCnt
            totalBought = self.getCommData(trCode, rqName, "총매입금액").strip()
            print(f"[test] : {totalBought}")
            for i in range(nCnt):
                template = {}
                template["stockCd"] = self.getCommData(trCode, rqName, "종목코드", i).strip()
                template["stockNm"] = self.getCommData(trCode, rqName, "종목명", i).strip()
                template["qty"] = int(self.getCommData(trCode, rqName, "보유수량", i).strip())
                template["avgPrice"] = int(self.getCommData(trCode, rqName, "평균단가", i).strip())
                template["nowPrice"] = int(self.getCommData(trCode, rqName, "현재가", i).strip())
                template["evalPrice"] = int(self.getCommData(trCode, rqName, "평가금액", i).strip())
                template["earnPrice"] = int(self.getCommData(trCode, rqName, "손익금액", i).strip())
                template["earnRate"] = round(int(self.getCommData(trCode, rqName, "손익율", i).strip()) / 10000, 2)
                template["loanDate"] = self.getCommData(trCode, rqName, "대출일", i).strip()
                template["boughtTotal"] = int(self.getCommData(trCode, rqName, "매입금액", i).strip())
                template["paymentBalance"] = int(self.getCommData(trCode, rqName, "결제잔고", i).strip())
                
                print(f"[test] : {template})")
                self.myAssetInfo.append(template)
            logText = f"[test] self.myAssetInfo: {self.myAssetInfo})"
            self.writeLog(logText)
        elif rqName == "opw00007_req" : #계좌별주문체결내역상세요청
            self.orderInfos = []
            for i in range(nCnt):
                template = {}
                template["ordNo"] = self.getCommData(trCode, rqName, "주문번호", i).strip()
                template["stockNo"] = self.getCommData(trCode, rqName, "종목번호", i).strip()
                template["tradeGubun"] = self.getCommData(trCode, rqName, "매매구분", i).strip()
                template["creditGubun"] = self.getCommData(trCode, rqName, "신용구분", i).strip()
                template["ordQty"] = self.getCommData(trCode, rqName, "주문수량", i).strip()
                template["ordPrice"] = self.getCommData(trCode, rqName, "주문단가", i).strip()
                template["confirmQty"] = self.getCommData(trCode, rqName, "확인수량", i).strip()
                template["receiptGubun"] = self.getCommData(trCode, rqName, "접수구분", i).strip()
                template["opposeYn"] = self.getCommData(trCode, rqName, "반대여부", i).strip()
                template["ordTime"] = self.getCommData(trCode, rqName, "주문시간", i).strip()
                template["originOrder"] = self.getCommData(trCode, rqName, "원주문", i).strip()
                template["stockName"] = self.getCommData(trCode, rqName, "종목명", i).strip()
                template["orderGubun"] = self.getCommData(trCode, rqName, "주문구분", i).strip()
                template["loanDate"] = self.getCommData(trCode, rqName, "대출일", i).strip()
                template["dealQty"] = self.getCommData(trCode, rqName, "체결수량", i).strip()
                template["dealPrice"] = self.getCommData(trCode, rqName, "체결단가", i).strip()
                template["orderRemain"] = self.getCommData(trCode, rqName, "주문잔량", i).strip()
                template["connectGubun"] = self.getCommData(trCode, rqName, "통신구분", i).strip()
                template["fixCancel"] = self.getCommData(trCode, rqName, "정정취소", i).strip()
                template["confirmTime"] = self.getCommData(trCode, rqName, "확인시간", i).strip()
                self.orderInfos.append(template)
            print(f"[체결내역상세요청] : {self.orderInfos}")
        elif rqName == "sendOrder": #주문응답
            #비정상 주문의 경우 주문번호가 ""(공백)
            ordNo = self.getCommData(trCode, rqName, "주문번호").strip()
            print(f"[receive_trdata][sendOrder] 주문번호 : {ordNo}")
        elif rqName == "opt10004_req" : #수동 호가데이터 호출
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
            
            self.openPopup("hogaWin")
            self.update_hoga()
    
    def receive_chejan(self, data): #sendOrder결과 이벤트
        # accNo = self.ocx.dynamicCall("GetChejanData(QString)", 9201)
        # ordNo = self.ocx.dynamicCall("GetChejanData(QString)", 9203)
        # stockCd = self.ocx.dynamicCall("GetChejanData(QString)", 9001)
        # ordState = self.ocx.dynamicCall("GetChejanData(QString)", 913)
        # ordGubun = self.ocx.dynamicCall("GetChejanData(QString)", 905)
        # ordRemain = self.ocx.dynamicCall("GetChejanData(QString)", 902)
        # trGubun = self.ocx.dynamicCall("GetChejanData(QString)", 906)
        # buySellGubun = self.ocx.dynamicCall("GetChejanData(QString)", 907)
        # buySellGubun2 = self.ocx.dynamicCall("GetChejanData(QString)", 946)
        # dealTime = self.ocx.dynamicCall("GetChejanData(QString)", 908)
        # dealNo = self.ocx.dynamicCall("GetChejanData(QString)", 909)
        # dealPrice = self.ocx.dynamicCall("GetChejanData(QString)", 910)
        # dealAmt = self.ocx.dynamicCall("GetChejanData(QString)", 911)
        
        fidList = {
            "계좌번호" : "9201",
            "주문번호" : "9203",
            "종목코드" : "9001",
            "주문상태" : "913",
            "종목명" : "302",
            "주문수량" : "900",
            "주문가격" : "901",
            "미체결수량" : "902",
            "체결누계금액" : "903",
            "원주문번호" : "904",
            "주문구분" : "905",
            "매매구분" : "906",
            "매도수구분" : "907",
            "주문/체결시간" : "908",
            "체결번호" : "909",
            "체결가" : "910",
            "체결량" : "911",
            "현재가" : "10",
            "(최우선)매도호가" : "27",
            "(최우선)매수호가" : "28",
            "단위체결가" : "914",
            "단위체결량" : "915",
            "거부사유" : "919",
            "화면번호" : "920",
            "신용구분" : "917",
            "대출일" : "916",
            "보유수량" : "930",
            "매입단가" : "931",
            "총매입가" : "932",
            "주문가능수량" : "933",
            "당일순매수수량" : "945",
            "매도/매수구분" : "946",
            "당일총매도손일" : "950",
            # "예수금"  (지원안함): "951",
            "기준가" : "307",
            "손익율" : "8019",
            "신용금액" : "957",
            "신용이자" : "958",
            "만기일" : "918",
            "당일실현손익(유가)" : "990",
            "당일실현손익률(유가)" : "991",
            "당일실현손익(신용)" : "992",
            "당일실현손익률(신용)" : "993",
            "파생상품거래단위" : "397",
            "상한가" : "305",
            "하한가": "306"
        }
        received_data = {}
        for key, value in fidList.items():
            received_data[key] = self.ocx.dynamicCall("GetChejanData(QString)", value)
        results = {
            0 : "접수 및 체결", 1 : "잔고변경", 4 : "파생잔고변경"
        }
        print(f"[receive_chejan] 체결결과 : {data} = {results[data]}")
        print(f"[receive_chejan] 수신데이터 : {received_data}")
    
    def sendOrder(self, rqName, accountNo, ordType, orderQty, orderPrice, hogaGubun, orgOrdNo = ""): #주문전송
        self.hogaGubun = None
        orderTypes = {"신규매수":"1", "신규매도":"2", "매수취소":"3", "매도취소":"4", "매수정정":"5", "매도정정":"6"}
        gubuns = {"지정가" : "00", "시장가": "03", "시간외" : "62"} #모의투자는 지정가와 시장가만 가능
        
        #시장가와 주문취소시 orderPrice = 0
        if hogaGubun == None:
            self.hogaGubun = gubuns['지정가']
        self.screenNo = "4989" #키움주문
        #호가창에서 주문가격과 수량을 호출해야 한다. 정정시에 orgOrdNo입력필요. 신규 = 공백
        print(f"주문전 확인: {rqName}({self.screenNo}), {accountNo}, {orderTypes[ordType]}, {self.stockCode} {orderPrice}({orderQty}개) {self.hogaGubun} {orgOrdNo}")
        self.ocx.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)"
                             ,[rqName, self.screenNo, accountNo, orderTypes[ordType], self.stockCode, orderQty, orderPrice, self.hogaGubun, orgOrdNo])
        #받아온 메세지 출력 :4989 sendOrder KOA_NORMAL_BUY_KP_ORD [RC4027] 모의투자 상/하한가 오류입니다.
        
    def SetRealReg(self, screen_no, code_list, fid_list, real_type): #실시간 데이터 ON
        print(screen_no + "실시간데이터 요청시작")
        self.ocx.dynamicCall("SetRealReg(QString, QString, QString, QString)", 
                              screen_no, code_list, fid_list, real_type)
        self.statusBar().showMessage("실시간데이터 ON")

    def DisConnectRealData(self, screen_no=""): #실시간 데이터 OFF
        screen_no
        code = self.stockCode
        # self.ocx.dynamicCall("DisConnectRealData(QString)", screen_no)
        self.ocx.dynamicCall("SetRealRemove(QString, QString)", "ALL", "ALL")
        self.statusBar().showMessage("실시간데이터 OFF")
    
    def _handler_real_data(self, code, real_type, data): #실시간 데이터 처리
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
    
    def getCommData(self, trCode, recordName, itemNm, idx = 0): #데이터추출
        return self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trCode, recordName, idx, itemNm)
          
    def GetCommRealData(self, code, fid): #실시간데이터 추출
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
    
    def openPopup(self, purpose):
        if purpose == "hogaWin":
            print("새로운 호가창을 열기위해 기존의 호가창을 닫는다.")
            if hasattr(self, "hogaWin"): # self에 팝업변수 존재 체크
                if isinstance(self.hogaWin, QWidget):
                    if hasattr(self.hogaWin, "hogaOrderwin"): # self에 팝업변수 존재 체크
                        self.hogaWin.hogaOrderwin.close()
                self.hogaWin.close()
            toPassData = {"account":self.accounts, "myCash":self.myCash, "myUsableCash" : self.myUsableCash, "hogawinData": self.hogawin_data, "myAssetInfo":self.myAssetInfo}
            self.hogaWin = HogaWin(self, toPassData)
            self.hogaWin.show()
        elif purpose == "test":
            toPassData = 1
            self.testWin = TestWin(self, toPassData)
            self.testWin.show()
    
    def receiveDataFromChild(self, data):
        purpose = data['purpose']
        print(f"main received data {data}")
        if purpose == "계좌조회":
            self.hogawin_data = data
            self.getAccountInfo(data['accountNo'], data['accountPw'])
        elif purpose == "주문":
            print(f"[주문테스트] {data}")
            self.sendOrder("sendOrder", data['accountNo'], data['ordType'], data['ordQty'], data['ordPrice'], None)
        
    def closeEvent(self, event): # 창 종료이벤트
        if hasattr(self, "hogaWin"): # self에 팝업변수 존재 체크
            if isinstance(self.hogaWin, QWidget):
                if hasattr(self.hogaWin, "hogaOrderwin"): # self에 팝업변수 존재 체크
                    self.hogaWin.hogaOrderwin.close()
            self.hogaWin.close()
        event.accept() #프로그램 종료 . 이벤트 회수?
    
    def resizeEvent(self, event): #창크기변경 이벤트
        self.text_edit.setGeometry(10,60,self.width() - 20, int(self.height() * 0.4))
    # def moveEvent(self, event):
    #     print(f"{self.x()} {self.y()}")
class TestWin(QWidget):
    def __init__(self, parent, parent_data):
        super().__init__()  # 수정: QWidget 클래스의 생성자에 self를 전달
        
        self.parent = parent
        self.initUI(parent_data)

    def initUI(self, parent_data):
        self.parent_data = parent_data
        print(parent_data)
        self.setWindowTitle("테스트")
        self.setGeometry(15,15,300,760)
        #self.setGeometry(300,300,300,200)
    
    def closeEvent(self, event):
        if hasattr(self, "hogaOrderwin"): # self에 팝업변수 존재 체크
            self.hogaOrderwin.close()
        self.parent.DisConnectRealData()
    
        
def showAlert(msg):
        alert = QMessageBox()
        alert.setIcon(QMessageBox.Information)
        alert.setWindowTitle("경고")
        alert.setText(msg)
        alert.setStandardButtons(QMessageBox.Ok)
        
        # Executing the QMessageBox
        result = alert.exec_()
        #CommConnect(사용자 호출) -> 로그인창 출력 -> OnEventConnect(이벤트 발생)        
def main():
    app = QApplication(sys.argv)
    window = MyWin()
    window.show()
    # app.exec_()
    sys.exit(app.exec_())

if __name__ == "__main__":  
    main()