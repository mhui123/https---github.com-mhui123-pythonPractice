import sys, os
import json
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QVariant, QTimer

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
    
class AutoTrWin(QWidget):
    resultRow = 0
    resultCol = 0
    lineShow = False
    orderCondition = {}
    clickedBtn = {"subject": None, "period":None}
    nowStep = 0
    steps = {1 : "종목검색", 2 : "종목선택", 3 : "가격조건", 4 : "매집기간주기", 5 : "수량금액입력", 6 : "완료"}
    step = 1
    
    def __init__(self):
        super().__init__()

        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('주식모으기')
        self.mainWidget = QWidget(self)
        self.mainLayout = QVBoxLayout(self.mainWidget)
        
        self.inputbox = QLineEdit()
        self.inputbox.textChanged.connect(self.sortout)
        self.testBtn = QPushButton("test")
        self.testBtn.clicked.connect(self.test)
        
        searchLayout = QHBoxLayout() # QWidget(target)
        searchLayout.addWidget(self.inputbox)
        searchLayout.addWidget(self.testBtn)
        
        self.resultLayout = QGridLayout()
        self.stepLayout = QVBoxLayout()
        self.nextPrevLayout = QHBoxLayout()
        self.prevBtn = QPushButton("이전")
        self.nextBtn = QPushButton("다음")
        self.prevBtn.clicked.connect(self.goToPrev)
        self.nextBtn.clicked.connect(self.goToNext)
        
        self.nextPrevLayout.addWidget(self.prevBtn)
        self.nextPrevLayout.addWidget(self.nextBtn)
        
        self.mainLayout.addLayout(searchLayout) #종목명입력란
        self.mainLayout.addLayout(self.resultLayout) #검색결과 표시
        self.mainLayout.addLayout(self.stepLayout) #거래방식 입력란
        self.mainLayout.addLayout(self.nextPrevLayout) #이전다음버튼
        
        self.mainWidget.setLayout(self.mainLayout)
        self.mainWidget.setMinimumHeight(300)
        self.mainWidget.setMinimumWidth(600)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.typingTimeout)
        self.timer.setInterval(1000)

        # List to store dynamically created widgets
        self.dynamic_widgets = []
        self.setStepUI()
        
    def test(self):
        print(f"[test] {self.orderCondition}")
                            
    def setStepUI(self):
        self.priceBtn = QPushButton("현재가")
        self.priceConditionInput = QLineEdit()
        self.updownBtn = QPushButton("이상")
        self.updownBtn.clicked.connect(self.updownChange)
        
        line = QHBoxLayout()
        line.addWidget(self.priceBtn)
        line.addWidget(self.priceConditionInput)
        line.addWidget(self.updownBtn)
        
        step2 = QGridLayout()
        label = QLabel("매집기간")
        step2.addWidget(label, 0, 0)
        subjectTags = ["1주일", "1개월", "3개월", "6개월", "1년"]
        periodTags = ["매일", "매주", "매월"]
        daysTags = ["월", "화", "수", "목", "금"]
        # self.dateSpinBox = QSpinBox()
        # self.dateSpinBox.setMinimum(1)
        # self.dateSpinBox.setMaximum(31)
        
        self.dateCombo = QComboBox()
        for i in range(31):
            self.dateCombo.addItem(str(i + 1))
        self.dateCombo.currentIndexChanged.connect(self.setDateMonth)
            
        for i in range(len(subjectTags)):
            btn = QPushButton(subjectTags[i])
            btn.clicked.connect(self.setBtnStyle)
            step2.addWidget(btn, 1, i)
        
        
        label2 = QLabel("주기")
        step2.addWidget(label2, 2, 0)
        for i in range(len(periodTags)):
            btn = QPushButton(periodTags[i])
            step2.addWidget(btn, 3, i)
            btn.clicked.connect(self.setBtnStyle)
        for i in range(len(daysTags)):
            btn = QPushButton(daysTags[i])
            btn.clicked.connect(self.setBtnStyle)
            step2.addWidget(btn, 4, i)
        step2.addWidget(self.dateCombo, 5, 0)
        
        step3 = QGridLayout()
        label3 = QLabel("매입수량")
        self.howManyInput = QLineEdit()
        label4 = QLabel("매입금액")
        self.howMuchInput = QLineEdit()
        step3.addWidget(label3, 0, 0)
        step3.addWidget(self.howManyInput, 0, 1)
        step3.addWidget(label4, 1, 0)
        step3.addWidget(self.howMuchInput, 1, 1)
        
        step4 = QGridLayout()
        self.step4Table = QTableWidget()
        self.step4Table.setColumnCount(2)
        self.step4Table.setRowCount(6)
        step4.addWidget(self.step4Table, 0,0)
            
        self.orderCondition["priceTarget"] = "nowPrice"
        self.orderCondition["updown"] = "up"
        
        self.stepLayout.addLayout(line)
        self.stepLayout.addLayout(step2)
        self.stepLayout.addLayout(step3)
        self.stepLayout.addLayout(step4)
        self.layoutShowHide("hide")
        
    # step1 종목검색
    def sortout(self):
        self.lineShow = False
        self.layoutShowHide("hide")
        text = self.inputbox.text().upper()
        typeLen = len(text)
        if typeLen >= 2 :
            self.timer.start()
            filtered_data = [item for item in data if item["name"].find(text) != -1] # string.find(txt) == -1이면 해당 텍스트 없음
            if(len(filtered_data) > 10) :
                filtered_data = filtered_data[:10]
            
            if len(filtered_data) > 0 :
                self.showResult(filtered_data)
            print(f"{text} 검색결과 : {filtered_data}")
            # widget.setParent(None)
        else :
            self.clearResult()
    
    def clearResult(self) :
        gridLen = self.resultLayout.count()
        if gridLen > 0 :
            for i in range(gridLen):
                item = self.resultLayout.itemAt(i)
                if item is not None:
                    widget = item.widget()
                    widget.deleteLater()
        self.resultRow = 0
        self.resultCol = 0
        
    def typingTimeout(self): #타이머가 멈출때 enter키를 누른것과 동일한 효과가 발생한다.
        self.timer.stop()  # Stop the timer
        
    def showResult(self, data):
        self.step = 1
        self.clearResult()
        #self.resultLayout에 검색결과를 "새롭게" 붙여야 한다.
        if len(data) > 0:
            for idx, object in enumerate(data):
                stockName = object['name']
                btn = QPushButton(stockName)
                btn.clicked.connect(self.stockChoice)
                self.resultLayout.addWidget(btn, self.resultRow, self.resultCol)
                self.resultCol = self.resultCol + 1
                if self.resultCol >= 5 :
                    self.resultCol = 0
                    self.resultRow = self.resultRow + 1
            
    # step2 종목선택
    def stockChoice(self):
        self.step = 2
        self.lineShow = True
        
        chooseItem = self.sender().text()
        filtered_data = [item for item in data if item["name"] == chooseItem] # string.find(txt) == -1이면 해당 텍스트 없음
        code = filtered_data[0]['code']
        self.orderCondition["stockCd"] = code
        self.orderCondition["stockNm"] = chooseItem
        self.inputbox.hide()
        self.goToNext()
        self.clearResult() #출력한 검색결과 제거
    
    # step3 가격조건 ~
    def goToNext(self):
        print(f"now step: {self.step} {self.steps[self.step]}")
        if self.step >= 3:
            self.setCondition()
        self.step = self.step + 1
        self.layoutShowHide("hide")
        # self.setCondition()
        
        self.showLayout()
        
    def goToPrev(self):
        self.layoutShowHide("hide")
        # self.setCondition()
        self.step = self.step - 1
        print(f"now step: {self.step}")
        self.showLayout()
        if self.step <= 2:
            self.inputbox.show()
    
    def setDateMonth(self):
        # self.dateCombo.removeItem(i)
        date = self.dateCombo.currentText()
        self.orderCondition['date'] = date
        
    def showLayout(self, btnTxt = ""):
        idx = self.step - 3
        item = self.stepLayout.itemAt(idx)
        daysTags = ["월", "화", "수", "목", "금"]
        if item is not None:
            if isinstance(item, QHBoxLayout) or isinstance(item, QVBoxLayout) or isinstance(item, QGridLayout):
                layoutLen = item.count()
                for i in range(layoutLen):
                        widget = item.itemAt(i).widget()
                        widget.show()
                if self.step == 4:
                    toHideRow = [4, 5]
                    for row in toHideRow:
                        for i in range(item.columnCount()):
                            item2 = item.itemAtPosition(row, i)
                            if item2 is not None:
                                item2.widget().hide()
                                # if row == 5:
                                    # print(f"[before] row : {row}, index : {i}, text : {item2.widget().text()}, isShow : {item2.widget().isVisible()}")
                                if btnTxt == "매주" or btnTxt in daysTags or ('day' in self.orderCondition and self.orderCondition['period'] == '매주'):
                                    if row == 4:
                                        item2.widget().show()
                                if btnTxt == "매월" or ('date' in self.orderCondition and self.orderCondition['period'] == '매월'):
                                    if row == 5:
                                        item2.widget().show()
                                # if row == 5:
                                #     print(f"[after] row : {row}, index : {i}, text : {item2.widget().text()}, isShow : {item2.widget().isVisible()}")
                elif self.step == 6:
                    self.step4Table.show()
                    # [종목명(종목코드), 가격조건, 목표기간, 매수주기, 수량, 가격]
                    columns = ['종목명(종목코드)', '가격조건', '목표기간', '매수주기', '수량', '금액']
                    text = {"up" : "이상", "down" : "이하"}
                    tbData = {'stockNm' : f"{self.orderCondition['stockNm']}",
                              'stockCd' : f"{self.orderCondition['stockCd']}",
                              'priceCatg' : f"{self.orderCondition['priceTarget']}",
                              'priceCondition':f"{self.orderCondition['howMuch']}",
                              'priceUpDown':f"{self.orderCondition['updown']}",
                              'subject':f"{self.orderCondition['subject']}",
                              'period' : f"{self.orderCondition['period']}",
                              'periodDetail' : None,
                              'amt':f"{self.orderCondition['amt']}",
                              'price':f"{self.orderCondition['price']}"}
                    
                    if self.orderCondition['period'] == '매주':
                        tbData['periodDetail'] = f"{self.orderCondition['day']}요일"
                    elif self.orderCondition['period'] == '매월':
                        tbData['periodDetail'] = f"{self.orderCondition['date']}일"
                        
                    matchData = {
                                    '종목명(종목코드)': f"{tbData['stockNm']} ({tbData['stockCd']})",
                                    '가격조건' : f"{tbData['priceCondition']}원 {text[tbData['priceUpDown']]}",
                                    '목표기간' : f"{tbData['subject']}",
                                    '매수주기' : f"{tbData['period']} {tbData['periodDetail']}",
                                    '수량' : f"{tbData['amt']}",
                                    '금액' : f"{tbData['price']}"
                                }
                    
                    for row in range(self.step4Table.rowCount()):
                        for col in range(2):
                            label = QLabel(columns[row])
                            value = QLabel(matchData[columns[row]])
                            if col == 0 :
                                #테이블 라벨명 부착
                                self.step4Table.setCellWidget(row, col, label)
                            else :
                                self.step4Table.setCellWidget(row, col, value)
                        print(columns[row])
                        
                                
                    
    def setCondition(self):
        stepKeys = {3 : "howMuch", 5: ["amt","", "price"]}
        idx = self.step -3
        item = self.stepLayout.itemAt(idx)
        for i in range(len(item)):
            target = item.itemAt(i).widget()
            if isinstance(target, QLineEdit) :
                txt = target.text()
                print(f"[test] target text : {txt}")
                if isinstance(stepKeys[self.step], list):
                    thisKey = stepKeys[self.step][i-1]
                elif isinstance(stepKeys[self.step], str):
                    thisKey = stepKeys[self.step]
                self.orderCondition[thisKey] = txt
        
    def layoutShowHide(self, mode = ""):
        if mode == "hide":
            childsCnt = self.stepLayout.count()
            for i in range(childsCnt):
                item = self.stepLayout.itemAt(i)
                if item is not None:
                    if isinstance(item, QHBoxLayout) or isinstance(item, QVBoxLayout) or isinstance(item, QGridLayout):
                        layoutLen = item.count()
                        for i in range(layoutLen):
                            widget = item.itemAt(i).widget()
                            if widget is not None:
                                widget.hide()
        
    def setBtnStyle(self):
        subjectTags = ["1주일", "1개월", "3개월", "6개월", "1년"]
        daysTags = ["월", "화", "수", "목", "금"]
        btn = self.sender()
        btnTxt = self.sender().text()
        thisway = 'subject' if btnTxt in subjectTags else 'period'
        thiswaydetail = btnTxt if btnTxt in daysTags else ''
        
        forCompare = None
        if thiswaydetail == '':
            if self.clickedBtn[thisway] is not None:
                forCompare = self.clickedBtn[thisway]
            self.clickedBtn[thisway] = btn
        else:
            if 'day' not in self.clickedBtn:
               self.clickedBtn['day'] = None 
            if self.clickedBtn['day'] is not None:
                forCompare = self.clickedBtn['day']
            self.clickedBtn['day'] = btn
            
        # period '매일', '매월'일 때 self.orderCondition['day'] 제거. 매월과 매주 x요일을 'periodOpt'라는 이름으로 받는것이 좋을 것으로 보임
        
        
        # if not hasattr(self.orderCondition, thisway) or self.orderCondition[thisway] != btnTxt:
        if thisway not in self.orderCondition or self.orderCondition[thisway] != btnTxt:
            if thiswaydetail == '':
                # if 'day' in self.orderCondition:
                #     del self.orderCondition['day']
                # if 'date' in self.orderCondition:
                #     del self.orderCondition['date']
                if btnTxt == '매월':
                    self.setDateMonth()
                self.orderCondition[thisway] = btnTxt
            else :
                if 'date' in self.orderCondition:
                    del self.orderCondition['date']
                self.orderCondition['day'] = btnTxt
            # periodTags = ["매일", "매주", "매월"]
            if thisway == 'period':
                if btnTxt in daysTags:
                    self.orderCondition['day'] = btnTxt
                self.showLayout(btnTxt)
                
            compareTxt = forCompare.text() if forCompare is not None else ""
            
            btn.setStyleSheet('background-color: rgba(150,150,150,255)')
            # btn.setStyleSheet('border: 2px black; font-weight: bold;')
            if compareTxt != "" and compareTxt != btnTxt:
                forCompare.setStyleSheet('background-color: None')
                # forCompare.setStyleSheet('border: 1px black; font-weight: None;')
    
    def updownChange(self):
        btnTxt = self.updownBtn.text()
        changeTxt = "이하" if btnTxt == "이상" else "이상"
        self.updownBtn.setText(changeTxt)
        self.orderCondition["updown"] = "down" if changeTxt == "이하" else "up"
        
def main():
    app = QApplication(sys.argv)
    example = AutoTrWin()
    example.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()