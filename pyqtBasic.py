import sys
import json
import typing
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt

with open('./codeList.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

class MyWin(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ocx = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
        self.stockName = ""
        self.stockCode = ""
        self.needSelectData = ""
        self.selectedData = ""
        self.addedCnt = 0
        
        self.loginEvent()
        self.setWindowTitle("pyStock")
        self.setGeometry(300,300,500,150)
        
        #이벤트 처리
        self.ocx.OnReceiveTrData.connect(self.receive_trdata)
        
        #수신 메시지 처리
        self.ocx.OnReceiveMsg.connect(self.received_msg)
        
        #종목코드 입력란
        label = QLabel("종목명: ", self)
        self.code_edit=QLineEdit(self)
        # self.code_edit.setText("039490") #종목코드 입력란
        searchBtn = QPushButton("조회", self)
        testBtn = QPushButton("test", self)
        # testBtn.clicked.connect(self.openPopup)
        testBtn.clicked.connect(self.hoga_test)
        testBtn.move(260, 20)
        
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
        toFind = [item for item in self.needSelectData if item['name'] == inputText][0]
        if toFind :
            self.stockCode = toFind['code']
            self.stockName = toFind['name']
            self.searchBtn_clicked()
        # print("enter event", self.needSelectData)
        # if(len(self.needSelectData) > 1):
        #     self.openPopup()
        
        #CommConnect(사용자 호출) -> 로그인창 출력 -> OnEventConnect(이벤트 발생)
    def searchBtn_clicked(self):
        if len(self.stockCode) > 0:
            code = self.stockCode
            self.text_edit.append("조회 종목코드 : " + code)
        
            self.requestData("opt10001", "종목코드", code, "0101")
    
    def hoga_test(self):
        code = self.stockCode
        result = self.requestData("opt10004", "종목코드", code, "0111")
        
    def loginEvent(self):
        self.ocx.dynamicCall("CommConnect()")
        self.ocx.OnEventConnect.connect(self.loginResult)
        
    def loginResult(self, err_code):
        errCodes = {"0" : "로그인 성공", "101" : "정보교환 실패", "102" : "서버접속 실패", "103" : "버전처리 실패"}
        self.text_edit.append(errCodes[str(err_code)])
            
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
        print("nCnt : ", nCnt)
        # for i in range(0, nCnt):
        if rqName == "opt10001_req":
            name = self.getCommData(trCode, rqName, "종목명")
            volume = self.getCommData(trCode, rqName, "거래량")
            self.text_edit.append("종목명 :" + name.strip())
            self.text_edit.append("거래량 :" + volume.strip())
        else :
            outputParams = ["호가잔량기준시간",
                            "매도10차선잔량", "매도10차선호가",
                            "매도9차선잔량", "매도9차선호가",
                            "매도8차선잔량", "매도8차선호가",
                            "매도7차선잔량", "매도7차선호가",
                            "매도6우선잔량", "매도6차선호가",
                            "매도5차선잔량", "매도5차선호가",
                            "매도4차선잔량", "매도4차선호가",
                            "매도3차선잔량", "매도3차선호가",
                            "매도2차선잔량", "매도2차선호가",
                            "매도최우선잔량", "매도최우선호가",
                            
                            "매수최우선잔량", "매수최우선호가",
                            "매수2차선잔량", "매수2차선호가",
                            "매수3차선잔량", "매수3차선호가",
                            "매수4차선잔량", "매수4차선호가",
                            "매수5차선잔량", "매수5차선호가",
                            "매수6우선잔량", "매수6우선호가",
                            "매수7차선잔량", "매수7차선호가",
                            "매수8차선잔량", "매수8차선호가",
                            "매수9차선잔량", "매수9차선호가",
                            "매수10차선잔량", "매수10차선호가",
                            
                            "총매도잔량", "총매수잔량",
                            "시간외매도잔량","시간외매수잔량"
                            ]
            for item in outputParams :
                a = self.getCommData(trCode, rqName, item)
                #호가잔량기준시간 : hhMMss
                print(item + " : " + a)
      
    def getCommData(self, trCode, recordName, itemNm, idx = 0):
        return self.ocx.dynamicCall("GetCommData(QString, QString, int, QString)", trCode, recordName, idx, itemNm)
    
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
        toPassData = "is came from parent"
        self.newWindow = NewWindow(self, toPassData)
        self.newWindow.show()
    
    def receiveDataFromChild(self, data):
        print(data)

class NewWindow(QWidget):
    # def __init__(self, parent: QWidget | None = ..., flags: WindowFlags | WindowType = ...) -> None:
    #     super().__init__(parent, flags)
    def __init__(self, parent, parent_data):
        super().__init__()  # 수정: QWidget 클래스의 생성자에 self를 전달
        self.initUI(parent, parent_data)
        
    def initUI(self, parent, parent_data):
        self.parent = parent
        self.setWindowTitle("popup")
        self.setGeometry(100,100,300,300)
        
        sendTestBtn = QPushButton("callback test", self)
        sendTestBtn.setGeometry(10, 10, 100, 30)
        sendTestBtn.move(20,20)
        sendTestBtn.clicked.connect(self.testSend)
        
        print(parent_data)
        
        
    
    def testSend(self):
        child_data = "is going from child"
        self.parent.receiveDataFromChild(child_data)
        self.close() #창 닫기
        
def main():
    app = QApplication(sys.argv)
    window = MyWin()
    window.show()
    # app.exec_()
    sys.exit(app.exec_())
    
    
if __name__ == "__main__":  
    main()