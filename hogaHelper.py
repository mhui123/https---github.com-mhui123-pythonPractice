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
from AssetWin import *
from OrderInfoPop import *
from InterestPopup import *

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
    assetInfoChanged = pyqtSignal(QVariant)
    orderInfoChanged = pyqtSignal(QVariant)
    originOrdNoChanged = pyqtSignal(QVariant)
    interListInfoChanged = pyqtSignal(QVariant)
    
    originOrdInfo = None
    NOW_ORD_CODE = None
    NOW_ORD_NAME = None
    REQ_OCCUPY = False
    REAL_ON = False
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
        self.myAssetInfos = {}
        self.orderInfos = []
        self.thisAccountNo = None
        self.stockBasicInfo = {}
        
        self.myCash = 0
        self.myUsableCash = 0
        
        self.hogawin_data = None
        self.req_accountNo = None
        
        self.charge = {"virtual" :{ "fee" : 0.0035, "tax" : 0.002}, "real" : {"fee": 0.00015, "tax": 0.002}}
        self.MODE = "virtual" #virtual : 모의투자, real: 실제투자
        
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
        
        myStockBtn = QPushButton("보유종목", self)
        myStockBtn.move(190, self.height() - myStockBtn.height() - self.statusBar().height())
        myStockBtn.clicked.connect(self.openMyStocks)
        
        interStockBtn = QPushButton("관심종목", self)
        interStockBtn.move(190, self.height() - myStockBtn.y() + myStockBtn.height() + 10  - self.statusBar().height())
        interStockBtn.clicked.connect(self.openInterStocks)
        # btns = QVBoxLayout(self)
        # layout.addWidget(myStockBtn)
        # layout.addWidget(interStockBtn)
        
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
        self.thisAccountNo = self.accounts[0]
        data = {"purpose":"계좌조회", 'accountNo':self.thisAccountNo}
        self.callApi(data)
        
        # self.getMyAssetInfo() #보유잔고정보 조회
        
        # self.ocx.KOA_Functions("ShowAccountWindow","")
        # self.code_edit.append(f"계좌번호 : {account_num}")
    def getStockBasicInfo(self, code, screenNo = "0111"): #주식기본정보 요청
        # if isinstance(code, list):
        #     for item in code :
        #         self.REQ_OCCUPY = True
        #         self.requestData("opt10001", "종목코드", item, screenNo)
        #         time.sleep(0.3)    
                
                
        # else :
        self.requestData("opt10001", "종목코드", code, screenNo)
        
    def getAccountInfo(self, accNo): #예수금상세현황요청    
        self.setInputValue("계좌번호", accNo)
        self.setInputValue("비밀번호", "")
        self.setInputValue("조회구분", 2) #2 : 일반조회, 3 : 추정조회
        self.requestData("opw00001", "종목코드", '0', "0362") #0362 예수금상세현황
    def getOrderInfo(self, accNo): #계좌별주문체결내역상세요청
        trCode = "opw00007"
        screenNo = "0351"
        current_time = datetime.datetime.now()
        today = int(current_time.strftime("%Y%m%d"))
        self.setInputValue("주문일자", today)
        self.setInputValue("계좌번호", accNo)
        self.setInputValue("비밀번호", "")
        self.setInputValue("비밀번호입력매체구분", "00")
        self.setInputValue("조회구분", "1") #1:주문순 2:역순 3:미체결 4:체결내역
        self.setInputValue("주식채권구분", "0") #0:전체 1:주식 2:채권
        self.setInputValue("매도수구분", "0") #0:전체 1:매도 2:매수
        self.setInputValue("종목코드", "") #공백일때 전체
        self.setInputValue("시작주문번호", "") #공백일때 전체
        self.requestData(trCode, "", "", screenNo)
    def getMyAssetInfo(self, accountNo): #계좌평가현황요청
        self.thisAccountNo = accountNo
        self.myAssetInfos[accountNo] = {'accountCheck' : True}
        self.myAssetInfos[accountNo]['assets'] = []
        
        self.setInputValue("계좌번호", accountNo)
        self.setInputValue("비밀번호", "") #사용안함 공백
        self.setInputValue("상장폐지조회구분", 0) # 0:전체, 1:상장폐지종목 제외
        self.setInputValue("비밀번호입력매체구분", "00") # 0:전체, 1:상장폐지종목 제외
        self.setInputValue("조회구분", "2") # 1:합산 2:개별
        self.requestData("opw00004", "", '0', "0346") #계좌평가잔고내역
                
    def openMyStocks(self):
        self.openPopup("openMyStocks")
    def openInterStocks(self):
        self.openPopup("openInterStocks")
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
    
    def determinTime(self):
        current_time = datetime.datetime.now()
        hourMin = int(current_time.strftime("%H%M"))
        time = None
        if hourMin < 1530 and hourMin >= 900:
            time = "장중"
        elif hourMin > 0 and hourMin < 900:
            time = "장시작전"
        else :
            time = "장마감"
        return time
    
    def call_hogaData(self): #호가창 호출이벤트
        code = self.stockCode
        time = self.determinTime()
        if time == "장중":
            reqVal = 0 if self.REAL_ON == False else 1 #0 : 신규요청 1: 추가요청
            self.SetRealReg("0111", code, "41;", reqVal) 
        elif time == "장시작전":
            self.text_edit.append("장 시작전입니다. 수동으로 데이터를 호출합니다.")
        elif time == "장마감":
            self.text_edit.append("장 마감되었습니다. 수동호출로 데이터를 요청합니다.")
        
        self.requestData("opt10004", "종목코드", code, "0111")
        
            
    def received_msg(self, screenNo, rqName, trCode, msg): #서버메세지 수신
        self.writeLog(f"[{screenNo}][{rqName}][{trCode}] : {msg}")
    
    def setInputValue(self, itemName, code): #api 데이터요청용 값 입력
        self.ocx.dynamicCall("SetInputValue(QString, QString)", itemName, code)
    
    def requestData(self, trCode, itemNm, code, screenNo, isContinue = False): #api 데이터요청
        isContinue = 2 if isContinue == True else 0
        rqName = trCode+"_req"
        #조회요청 시 SetInputValue로 parameter지정 후 CommRqData로 요청한다.
        if len(code) > 0 :
            # self.ocx.dynamicCall("SetInputValue(QString, QString)", itemNm, code)
            self.setInputValue(itemNm, code)
        result = self.ocx.dynamicCall("CommRqData(QString, QString, int, QString)",rqName, trCode, isContinue, screenNo)
        if result == -202 : #계좌비밀번호 입력필요.
            print(f"계좌 비밀번호 입력설정창을 연다.")    
            showAlert(f"계좌비밀번호를 저장하고 프로그램을 재실행해야합니다.")
            self.ocx.KOA_Functions("ShowAccountWindow","")
        
    
    def receive_trdata(self, screenNo, rqName, trCode, recordName, preNext): #API 응답이벤트
        #복수데이터의 경우 idx가 항목 순서이다.
        nCnt = self.ocx.dynamicCall("GetRepeatCnt(QString, QString)", trCode, rqName)
        print(f"[receive_trdata] nCnt: {nCnt} trCode:{trCode}, rqName:{rqName}")
        # for i in range(0, nCnt):
        if rqName == "opt10001_req": #종목정보 조회
            output = ["종목명", "종목코드", "시가", "고가", "저가", "상한가", "하한가", "기준가", "연중최고", "연중최저", "250최고", "250최저"
                      ,"전일대비", "등락율", "거래량", "거래대비", "현재가", "대비기호"]
            
            name = self.getCommData(trCode, rqName, "종목명")
            self.writeLog(f"조회종목 : {name.strip()}({self.stockCode})")
            temp = {}
            #set stockBasicInfo
            for item in output:
                value = classifyNumStr(self.getCommData(trCode, rqName, item).strip())
                temp[item] = value
            temp['전일대비,등락율'] = f"{temp['전일대비']} ({temp['등락율']}%)"
            self.stockBasicInfo[name] = temp
            if screenNo == "0150" :
                #관심종목창에서 호출
                self.update_InterListInfo(self.stockBasicInfo)
                self.REQ_OCCUPY = False
                
        elif rqName == "opw00001_req": #예수금상세현황요청
            self.myCash = int(self.getCommData(trCode, rqName, "예수금").strip())
            self.myUsableCash = int(self.getCommData(trCode, rqName, "주문가능금액").strip())
            logText = f"예수금요청 예수금:{self.myCash} 주문가능:{self.myUsableCash}"
            self.myAssetInfos[self.thisAccountNo]['myUsableCash'] = self.myUsableCash
            self.myAssetInfos[self.thisAccountNo]['myCash'] = self.myCash
            self.writeLog(logText)
            self.update_account_info()
        elif rqName == "opw00004_req": #계좌평가현황요청
            # myAssetInfo
            nCnt
            totalBought = self.getCommData(trCode, rqName, "총매입금액").strip()
            print(f"[test] : {totalBought}")
            for i in range(nCnt):
                template = {}
                template["stockCd"] = self.getCommData(trCode, rqName, "종목코드", i)
                template["stockNm"] = self.getCommData(trCode, rqName, "종목명", i)
                template["qty"] = int(self.getCommData(trCode, rqName, "보유수량", i))
                template["avgPrice"] = int(self.getCommData(trCode, rqName, "평균단가", i))
                template["nowPrice"] = int(self.getCommData(trCode, rqName, "현재가", i))
                template["evalPrice"] = int(self.getCommData(trCode, rqName, "평가금액", i)) #이 평가금액은 현재가로 매도시에 입금될 금액. 수수료,세금 다 제외한 실제매출
                template["earnPrice"] = int(self.getCommData(trCode, rqName, "손익금액", i))
                template["earnRate"] = round(int(self.getCommData(trCode, rqName, "손익율", i)) / 10000, 2)
                template["loanDate"] = self.getCommData(trCode, rqName, "대출일", i)
                template["boughtTotal"] = int(self.getCommData(trCode, rqName, "매입금액", i))
                template["paymentBalance"] = int(self.getCommData(trCode, rqName, "결제잔고", i))
                template["pQty"] = template["qty"] #보유수량
                
                self.myAssetInfo.append(template)
                self.myAssetInfos[self.thisAccountNo]['assets'].append(template)
            logText = f"[test] self.myAssetInfo: {self.myAssetInfo})"
            self.writeLog(logText)
            self.update_assetData()
        
        elif rqName == "opw00007_req" : #계좌별주문체결내역상세요청
            self.orderInfos = []
            for i in range(nCnt):
                template = {}
                template["주문번호"] = self.getCommData(trCode, rqName, "주문번호", i)
                template["종목번호"] = self.getCommData(trCode, rqName, "종목번호", i)
                template["매매구분"] = self.getCommData(trCode, rqName, "매매구분", i)
                template["신용구분"] = self.getCommData(trCode, rqName, "신용구분", i)
                template["주문수량"] = int(self.getCommData(trCode, rqName, "주문수량", i))
                template["주문단가"] = int(self.getCommData(trCode, rqName, "주문단가", i))
                template["확인수량"] = int(self.getCommData(trCode, rqName, "확인수량", i))
                template["접수구분"] = self.getCommData(trCode, rqName, "접수구분", i)
                template["반대여부"] = self.getCommData(trCode, rqName, "반대여부", i)
                template["주문시간"] = self.getCommData(trCode, rqName, "주문시간", i)
                template["원주문"] = self.getCommData(trCode, rqName, "원주문", i)
                template["종목명"] = self.getCommData(trCode, rqName, "종목명", i)
                template["주문구분"] = self.getCommData(trCode, rqName, "주문구분", i)
                template["대출일"] = self.getCommData(trCode, rqName, "대출일", i)
                template["체결수량"] = int(self.getCommData(trCode, rqName, "체결수량", i))
                template["체결단가"] = int(self.getCommData(trCode, rqName, "체결단가", i))
                template["주문잔량"] = int(self.getCommData(trCode, rqName, "주문잔량", i))
                template["통신구분"] = self.getCommData(trCode, rqName, "통신구분", i)
                template["정정취소"] = self.getCommData(trCode, rqName, "정정취소", i)
                template["확인시간"] = self.getCommData(trCode, rqName, "확인시간", i)
                self.orderInfos.append(template)
            print(f"[체결내역 수신완료] 주문개수 : {len(self.orderInfos)}")
            self.update_orderInfo()
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
                if convertForm.get(item) is not None :
                    key = convertForm[item]
                    self.hoga_dict[key] = result.strip()
            
            self.openPopup("hogaWin")
            self.update_hoga()
    
    def update_hoga(self): #호가창 업데이트
        self.dataChanged.emit(self.hoga_dict)
        if 'code' in self.stock_info and self.stockCode == self.stock_info['code']:
            self.stockInfoChanged.emit(self.stock_info)
    
    def update_account_info(self): #호가창 종목정보 업데이트
        toSend = {"myCash" : self.myCash, "myUsableCash" : self.myUsableCash, "hogawinData": self.hogawin_data}
        self.accountInfoChanged.emit(toSend)
          
    def update_assetData(self):
        self.assetInfoChanged.emit(self.myAssetInfos)
    def update_orderInfo(self):
        self.orderInfoChanged.emit(self.orderInfos)
    def update_originOrdNo(self, data={}):
        if len(data) > 0 :
            self.originOrdInfo = data
            self.originOrdNoChanged.emit(self.originOrdInfo)
            
    def update_InterListInfo(self, data = {}):
        self.update_signal(self.interListInfoChanged, data)
            
    def update_signal(self, signal, data={}):
        if hasattr(signal, 'emit') and len(data) > 0:
            signal.emit(data)
            
    def receive_chejan(self, data): #sendOrder결과 이벤트
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
            received_data[key] = self.ocx.dynamicCall("GetChejanData(QString)", value).strip()
        results = {
            '0' : "접수 및 체결", '1' : "잔고변경", '4' : "파생잔고변경"
        }
        print(f"[receive_chejan] 체결결과 : {data} = {results[data]}")
        print(f"[receive_chejan] 수신데이터 : {received_data}")
        state = results[data]
        accountNo = received_data['계좌번호']
        assets = self.myAssetInfos[accountNo]['assets']

        if results[data] == '잔고변경':
            "매도접수는 주문가능수량 매도체결시에는 보유수량 수정."
            pickData = [e for e in assets if e['stockCd'] == received_data['종목코드']] #myAssetInfos에 종목 존재여부 체크
            if len(pickData) > 0 : #"기존데이터 존재. 수정"
                pickData = pickData[0]
                pickData['qty'] = int(received_data['보유수량'])
                pickData['pQty'] = int(received_data['주문가능수량'])
                pickData['boughtTotal'] = int(received_data['총매입가'])
                pickData['avgPrice'] = 0 if pickData['qty'] == 0 else int(pickData['boughtTotal'] / pickData['qty'])
            else : #"신규데이터. 추가"
                template = {'stockCd': received_data['종목코드'], 
                            'stockNm': received_data['종목명'],
                            'qty': int(received_data['보유수량']),
                            'pQty' : int(received_data['주문가능수량']),
                            'avgPrice': int(int(received_data['총매입가']) / int(received_data['보유수량'])),
                            'nowPrice': int(received_data['현재가']), 'evalPrice': 0, 'earnPrice': 0, 'earnRate': 0, 'loanDate': '',
                            'boughtTotal': int(received_data['총매입가']), 'paymentBalance': 0}
                assets.append(template)
            print(f"[{state} 확인] : {assets}")
    def modifyAssetInfo(self):
        ""
        
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
        self.REAL_ON = True
        print(f"[{screen_no} - {code_list} {fid_list} {real_type}] 실시간데이터 요청")
        self.ocx.dynamicCall("SetRealReg(QString, QString, QString, QString)", 
                              screen_no, code_list, fid_list, real_type)
        self.writeLog(f"[{screen_no}][{code_list}] 실시간데이터 ON")
        # self.statusBar().showMessage("실시간데이터 ON")

    def DisConnectRealData(self, screenNo, stockCd = ""): #실시간 데이터 OFF
        code = "ALL" if stockCd == "" else stockCd
        screenNo = "ALL" if screenNo == "" else screenNo
        
        if code == "All" : self.REAL_ON = False
        
        self.ocx.dynamicCall("SetRealRemove(QString, QString)", screenNo, code) #screenNo, stockCd
        self.writeLog(f"[{screenNo}][{stockCd}] 실시간데이터 OFF")
        # self.statusBar().showMessage("실시간데이터 OFF")
    
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
        elif real_type == "주식체결":
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
            self.stock_info["code"] = code
            
            realData = {"종목명" : "", "종목코드" : code, "시가" : todayStart, "고가" : todayHigh, "저가" : todayLow,
            "전일대비" : priceChange, "등락율" : movePercent, "거래량" : accAmt, "현재가" : nowPrice, "대비기호" : self.GetCommRealData(code, 25)}
            
            #['150540', '+157200', '+1600', '+1.03', '+157300', '+157200', '-57', '517418', '81331', '+156700', '+158700', '+155800', '2', '-727831', ...]
            fString = f"주식체결 ::: {self.stockName}( {code} )"
            fInfos = f" {code} 현재가:{nowPrice} 누적거래량 {accAmt} 누적거래대금 {accPrice} 가격변동:{priceChange} 등락률:{movePercent}"
            # print(fString, fInfos)
            
            print(f"주식체결 확인 : {fInfos}")
            # 관심종목창에 데이터 전달할 필요.
            if self.thisAccountNo is not None: self.comparePrice(code, int(nowPrice))
            self.update_InterListInfo(realData)
        elif real_type == "주식우선호가":
            #호가틱이 변동될 때 발생하는 이벤트.
            now = datetime.datetime.now()
            ask01 =  self.GetCommRealData(code, 27)         
            bid01 =  self.GetCommRealData(code, 28)
            # print(f"현재시간 {now} | 최우선매도호가: {ask01} 최우선매수호가: {bid01}")
        elif real_type == "주식시세":
            nowP = self.GetCommRealData(code, 10)
            print(f"[실시간잔고] {code} {nowP}")
    def getCommData(self, trCode, recordName, itemNm, idx = 0): #데이터추출
        result = self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trCode, recordName, idx, itemNm)
        return result.strip()
          
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
        elif purpose == "openMyStocks":
            self.assetWin = AssetWin(self)
            self.assetWin.show()
        elif purpose == "orderInfoPop":
            self.orderInfoPop = OrderInfoPop(self)
            self.orderInfoPop.show()
        elif purpose == "openInterStocks":
            self.interWin = InterestPopup(self)
            self.interWin.show()
    
    def comparePrice(self, code, nowPrice):
        if hasattr(self, "assetWin"):
            assets = self.myAssetInfos[self.thisAccountNo]['assets']
            if len(assets) > 0 :
                temp = [item for item in assets if code in item['stockCd']]
                if len(temp) > 0 : 
                    temp = temp[0]
                    if(temp['nowPrice'] != nowPrice):
                        temp['nowPrice'] = nowPrice
                        self.update_assetData()
    
    def callApi(self,data):
        purpose = data['purpose']
        print(f"main received data {data}")
        if purpose == "계좌조회":
            self.hogawin_data = data
            self.getMyAssetInfo(data['accountNo'])
            self.getAccountInfo(data['accountNo'])
        elif purpose == "주문":
            print(f"[주문테스트] {data}")
            originOrdNo = data['originOrdNo'] if 'originOrdNo' in data else None
            self.sendOrder("sendOrder", data['accountNo'], data['ordType'], data['ordQty'], data['ordPrice'], None, originOrdNo)
        elif purpose == "주문조회":
            print(f"[주문조회요청처리]")
            self.getOrderInfo(data['accountNo'])
    def closeEvent(self, event): # 창 종료이벤트
        if hasattr(self, "hogaWin"): # self에 팝업변수 존재 체크
            if isinstance(self.hogaWin, QWidget):
                if hasattr(self.hogaWin, "hogaOrderwin"): # self에 팝업변수 존재 체크
                    self.hogaWin.hogaOrderwin.close()
            self.hogaWin.close()
        if hasattr(self, "assetWin"): # self에 팝업변수 존재 체크
            self.assetWin.close()
        if hasattr(self, "orderInfoPop"):
            self.orderInfoPop.close()
        if hasattr(self, "interWin"):
            self.interWin.close()
        event.accept() #프로그램 종료 . 이벤트 회수?
    
    def resizeEvent(self, event): #창크기변경 이벤트
        self.text_edit.setGeometry(10,60,self.width() - 20, int(self.height() * 0.4))
    # def moveEvent(self, event):
    #     print(f"{self.x()} {self.y()}")
        
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
    
def classifyNumStr(data):
    """
        입력값 분류함수 : 데이터가 str인지 number인지 판단하여 해당값만 남겨 반환.
    """
    filtNum = re.sub(r'[^0-9.+-]', '', data)
    returnData = None
    if len(filtNum) > 0 : #number
        returnData = float(filtNum) if '.' in filtNum else int(filtNum)
    else :
        returnData = data
    return returnData

if __name__ == "__main__":  
    main()