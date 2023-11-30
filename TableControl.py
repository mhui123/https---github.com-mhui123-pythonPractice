
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QVariant, QEvent

def setTbStyle(target):
    if isinstance(target, QTableWidget):
        target.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        target.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        target.verticalHeader().setVisible(False)
        target.horizontalHeader().setVisible(False)
        target.setEditTriggers(QTableWidget.NoEditTriggers) #테이블 직접수정 불가
        target.setStyleSheet("""QTableWidget { border : none; gridline-color: white; border-top:10px}
                                QTableWidget::item:selected { background-color: transparent; color:black}
                                    """) #테두리제거
    elif isinstance(target, QWidget) or isinstance(target, QMainWindow):
        target.setStyleSheet("background-color:white") #테두리제거
        
def setTbHeader(target, headers = []):
    """_summary_

    Args:
        target (_type_): QTableWidget
        headers (list, optional): 설정할 칼럼명들을 담은 list. Defaults to [].
    """
    if isinstance(target, QTableWidget) and len(headers) > 0 :
        target.insertRow(0)
        for i in range(len(headers)):
            item = QTableWidgetItem(headers[i])
            item.setTextAlignment(int(Qt.AlignRight|Qt.AlignVCenter))
            target.setItem(0, i, item)
    

