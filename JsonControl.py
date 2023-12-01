import json
import os

ROOT_PATH = "./data"
def writeJson(fileNm, data):
    """_summary_
    Args:
        fileNm (_type_): 희망 파일명을 입력한다.
        data (_type_): 
        
        << example >>
        
        data_to_write = {
            "name": "John",
            "age": 30,
            "city": "New York"
        }
        
    """
    # 작성
    file = f"{ROOT_PATH}/{fileNm}.json"
    try:
        with open(file, 'w') as json_file:
            json.dump(data, json_file)
            print(f"json file has been writen as new")
    except FileNotFoundError:
        folderChk(ROOT_PATH)
        writeJson(fileNm, data)
        data = {}
        
def readJson(fileNm):
    file = f"{ROOT_PATH}/{fileNm}.json"
    #호출
    try:
        with open(file, "r") as json_file:
            data = json.load(json_file)
            return data
    except FileNotFoundError:
        folderChk(ROOT_PATH)
        print(f"{file}을 찾을 수 없습니다.")
            
        
def delJson(fileNm):
    file = f"{ROOT_PATH}/{fileNm}.json"
    #삭제
    if os.path.exists(file):
        os.remove(file)
        print("File deleted")
    else:
        print("File not found")

def folderChk(path):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"The folder '{ROOT_PATH}' has been created.")
    else:
        print(f"The folder '{ROOT_PATH}' already exists.")

