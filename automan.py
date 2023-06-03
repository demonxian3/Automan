import os
from PIL.Image import Image
import pyautogui
import time
import re
import pyperclip
import pprint
import urllib.parse
import sys

class AutoMan:
    def __init__(self, baseDir='./'):
        self.defaultRetry = 3                           # 默认重试
        self.defaultRepeat = 1                          # 默认重复
        self.commandFile = 'cmd.txt'                    # 任务单文件名
        self.baseDir = baseDir                          # 执行任务存放的目录
        self.clockRate = 0.5                            # 执行时钟频率，每clockRate秒执行一条指令
        self.mouseDuration = 0.9                        # 鼠标移动时间
        self.keyboardInterval = 0.25                    # 键盘打字速度
        self.tagMap = {}                                # 记录标记位置行号
        self.commandsMap = {                            # 当前支持的指令
            '点击': {"label": "点击", "repeat":self.defaultRepeat, "retry":self.defaultRetry, "type": "click", "udlr": 'left', 'times': 1, 'coordinate': {}, 'ext' :{'duration': 0.9}},
            '移动': {"label": "移动", "repeat":self.defaultRepeat, "retry":self.defaultRetry, "type": "click", "udlr": 'left', 'times': 0, 'coordinate': {}, 'ext' :{'duration': 0.9}},
            '单击': {"label": "单击", "repeat":self.defaultRepeat, "retry":self.defaultRetry, "type": "click", "udlr": 'left', 'times': 1, 'coordinate': {}, 'ext' :{'duration': 0.9}},
            '三击': {"label": "三击", "repeat":self.defaultRepeat, "retry":self.defaultRetry, "type": "click", "udlr": 'left', 'times': 3, 'coordinate': {}, 'ext' :{'duration': 0.9}},
            '双击': {"label": "双击", "repeat":self.defaultRepeat, "retry":self.defaultRetry, "type": "click", "udlr": 'left', 'times': 2, 'coordinate': {}, 'ext' :{'duration': 0.9}},
            '打开': {"label": "打开", "repeat":self.defaultRepeat, "retry":self.defaultRetry, "type": "click", "udlr": 'left', 'times': 2, 'coordinate': {}, 'ext' :{'duration': 0.9}},
            '输入': {"label": "输入", "repeat":self.defaultRepeat, "retry":self.defaultRetry, "type": "input", "value": "", },
            '上滚': {"label": "上滚", "repeat":self.defaultRepeat, "retry":self.defaultRetry, "type": "scroll", "step": 150, },
            '下滚': {"label": "下滚", "repeat":self.defaultRepeat, "retry":self.defaultRetry, "type": "scroll", "step": -150, },
            '按键': {"label": "按键", "repeat":self.defaultRepeat, "retry":self.defaultRetry, "type": "hotkey", "value":"" },
            '等待': {"label": "等待", "repeat":self.defaultRepeat, "retry":self.defaultRetry, "type": "wait", "value":""},
            '时钟': {"label": "时钟", "repeat":self.defaultRepeat, "retry":self.defaultRetry, "type": "clock", "value":""},
            "标记": {"label": "标记", "repeat":self.defaultRepeat, "retry":self.defaultRetry, "type": "tag", "value":""},
            "回到": {"label": "回到", "repeat":self.defaultRepeat, "retry":self.defaultRetry, "type": "goto", "value":""},
            "跳转": {"label": "跳转", "repeat":self.defaultRepeat, "retry":self.defaultRetry, "type": "goto", "value":""},
            "文本": {"label": "文本", "repeat":self.defaultRepeat, "retry":self.defaultRetry, "type": "text", "value":"", "ext":{"interval": 0.25}}
        }
        self.commandPath = "./%s/%s" % (baseDir, self.commandFile )

    def showError(self, msg):
        print(msg)
        exit()

    def mouseClickLocation(self, clickTimes, udlr, location):
        pyautogui.click(location['x'],location['y'],clicks=clickTimes,interval=0.2,duration=self.mouseDuration,button=udlr)

    def mouseClickImage(self, clickTimes, udlr, images,retry):
        if not images:
            self.showError('请传递图片')

        print("【扫描】 %s" % " 和 ".join(images))

        def clickToImage():
            maxRetryTimes = 2   # 多张图片时，每张图的等待次数
            for img in images:
                currentTimes = 0

                while True:
                    location=pyautogui.locateCenterOnScreen(img,confidence=0.9)
                    if location is not None:
                        pyautogui.click(location.x,location.y,clicks=clickTimes,interval=0.2,duration=self.mouseDuration,button=udlr)
                        return True
                    if currentTimes >= maxRetryTimes:
                        break
                    currentTimes += 1
            return False

        retry = int(retry)
        # 无限重试，直到成功为止
        while retry == 0 and not clickToImage():
            time.sleep(self.clockRate)
        
        # 成功时直接退出，失败时计数减一，直到重试的次数为0
        while retry > 0 and not clickToImage():
            retry -= 1
            time.sleep(self.clockRate)

    def mouseScroll(self, step, repeat):
        step = int(step)
        repeat = int(repeat)
        while repeat > -1:
            repeat -= 1
            pyautogui.scroll(int(step))
            time.sleep(0.5)

    # 解析指令
    def parseCommand(self):
        content = ''
        with open(self.commandPath, encoding='utf-8') as fp :
            content = fp.read()

        num = 0
        lines = content.split('\n')
        taskQueue = []
        for line in lines:
            if not line:
                continue

            if line[0] == '#':
                continue

            words = re.split(r"\s+", line)
            action = words[0]
            value = words[1]
            wlen = len(words)

            if action not in self.commandsMap:
                self.showError("第%i行输入有误"%(num))

            if wlen < 2:
                self.showError("第%i行格式有误"%(num))

            task = self.commandsMap[action].copy()

            if task['type'] != 'input':
                # pprint.pprint(words)
                (retry, repeat) = words[2].split(',') if wlen > 2 and words[2]  else [5,1]
                if not retry or retry == '_':
                    retry = self.defaultRetry

                if not repeat or repeat == '_':
                    repeat = self.defaultRepeat

                ext = urllib.parse.parse_qs(words[3]) if wlen > 3 and words[3] else {}

                for i in ext:
                    ext[i] = ext[i][0]

                task['retry'] = retry
                task['repeat'] = repeat
                task['ext'] = ext
            
            
            task['desc'] = line
            if task['type'] == 'click':
                tryMatch = re.match(r"\((\d+),(\d+)\)", value)
                if tryMatch and tryMatch.group(1) and tryMatch.group(2):
                    task['coordinate'] = {'x': int(tryMatch.group(1)), 'y': int(tryMatch.group(2))}
                else:
                    names = value.split(',')
                    images = []
                    for name in names:
                        image = self.fetchImage(name)
                        if not image:
                            self.showError("找不到图片，请确保【%s】图片存在"% image)
                        images.append(image)
                    task['value'] = images
            
            elif task['type'] == 'hotkey':
                task['value'] = [key.lower() for key in value.split('+')]

            elif task['type'] == 'input':
                task['value'] = " ".join(words[1:])
                task['retry'] = 1
                task['repeat'] = 1
                task['ext'] = {}

            elif task['type'] == 'text':
                task['value'] = self.fetchText(words[1])

            elif task['type'] == 'tag':
                tag = words[1]
                self.tagMap[tag] = len(taskQueue)
            else:
                task['value'] = value

            taskQueue.append(task)
        return taskQueue

    def is_chinese(self, string):
        for ch in string:
            if u'\u4e00' <= ch <= u'\u9fff':
                return True

    # 执行指令
    def executeCommand(self,tasks):
        self.line = 0
        while self.line < len(tasks):
            task = tasks[self.line]
            def doTask():
                print('【执行】 %s' %  task['desc'])

                if task['type'] == 'click':
                    if 'duration' in task['ext'] and task['ext']['duration']:
                        self.mouseDuration = float(task['ext']['duration'])
                    if task['coordinate']:
                        # print(task['coordinate'])
                        self.mouseClickLocation(task['times'], task['udlr'], task['coordinate'])
                    else:
                        self.mouseClickImage(task['times'], task['udlr'], task['value'], task['retry'])

                elif task['type'] == 'scroll':
                    self.mouseScroll(task['step'], task['value'])

                elif task['type'] == 'wait':
                    time.sleep(float(task['value']))

                elif task['type'] == 'hotkey':
                    pyautogui.hotkey(*task['value'])
                    time.sleep(self.clockRate)

                elif task['type'] == 'input':
                    if self.is_chinese(task['value']):
                        oldclip = pyperclip.paste()
                        pyperclip.copy(task['value'])
                        time.sleep(0.2)
                        pyautogui.hotkey('ctrl', 'v')
                        time.sleep(0.2)
                        pyperclip.copy(oldclip)
                    else:
                        pyautogui.typewrite(task['value'])
                    time.sleep(self.clockRate)

                elif task['type'] == 'text':
                    if 'interval' in task['ext'] and task['ext']['interval']:
                        self.keyboardInterval = float(task['ext']['interval'])
                    pyautogui.write(task['value'], self.keyboardInterval)

                elif task['type'] == 'clock':
                    self.clockRate = float(task['value'])

                elif task['type'] == 'goto':
                    tag = task['value']
                    if tag in self.tagMap:
                        self.line = self.tagMap[tag]
                    else:
                        self.showError('第%i行跳转的位置输入有误'%(self.line+1) )
                
            repeat = str(task['repeat'])
            if str.isdigit(repeat):
                repeat = int(repeat)
                # 一直重复执行
                while repeat == 0:
                    doTask()

                # 执行指定次数
                while repeat > 0:
                    repeat -= 1
                    doTask()
            
            # 一直重复直到某个图片(显示/消失)
            else:
                repeatParams = urllib.parse.parse_qs(repeat)
                if not repeatParams:
                    self.showError('第%i行参数有误，ifno没图重复，ifhas有图重复'%(self.line+1))

                ifno = ifhas = None
                if 'ifno' in repeatParams:
                    ifno = self.fetchImage(repeatParams['ifno'][0])
                    if not ifno:
                        self.showError("找不到图片，请确保【%s】图片存在"% ifno)

                if 'ifhas' in repeatParams:
                    ifhas = self.fetchImage(repeatParams['ifhas'][0])
                    if not ifhas:
                        self.showError("找不到图片，请确保【%s】图片存在"% ifhas)

                while True:
                    ifnoBreak = ifhasBreak = True

                    if ifno:
                        ifnoBreak = bool(pyautogui.locateOnScreen(ifno, confidence=0.9))
                    
                    if ifhas:
                        ifhasBreak = not bool(pyautogui.locateOnScreen(ifhas, confidence=0.9))

                    if ifnoBreak and ifhasBreak:
                        break
                    doTask()

            self.line += 1

    def fetchImage(self, name):
        if '.' in name and os.path.exists(self.baseDir + '/'  + name):
            return self.baseDir + '/'  + name

        exts = ['.png', '.jpg', '.gif', '.svg', '.jpeg']
        for ext in exts:
            path = self.baseDir + '/'  + name + ext
            if os.path.exists(path):
                return path
        
        return None

        

    def fetchText(self, name):
        filename = ''
        if '.' in name and os.path.exists(self.baseDir + '/'  + name):
            filename = self.baseDir + '/'  + name

        else:
            filename = self.baseDir + '/'  + name + '.txt'
            if not os.path.exists(filename):
                self.showError("找不到文本文件，请确保【%s】文件存在"% filename)

        with open(filename, 'r', encoding='utf-8') as fp:
            text = fp.read()
        return text

    # 开始自动化操作
    def run(self, step):
        taskQueue = self.parseCommand()
        
        # pprint.pprint(taskQueue);exit()
        
        if step > 0 and step <= len(taskQueue):
            step-=1
            taskQueue = taskQueue[step:]
        self.executeCommand(taskQueue)
        
        if not os.path.exists(self.commandPath):
            self.showError('指定的目录缺失%s文件' % self.commandPath)


if __name__ == '__main__':
    if len(sys.argv) > 2 and sys.argv[1] == '-c' and int(sys.argv[2]):
        print('开启坐标显示器, 按Ctrl+C结束')
        while True:
            (x, y) = pyautogui.position()
            print("(%i,%i)" % (x, y))
            time.sleep(int(sys.argv[2]))

    taskDirs = []
    print("当前位置有以下文件夹，每个文件夹对应一个任务，请确保文件夹里有包含cmd.txt");

    i = 0
    for f in os.listdir('.'):
        if os.path.isdir(f):
            i += 1
            taskDirs.append(f)
            print("【%i】 %s" %(i, f))

    x = input("请输入序号: ")

    if not str.isdigit(x):
        print('请输入数字')
        exit()

    if int(x) < 1 or int(x) > len(taskDirs):
        print('请输入列举的有效数字')
        exit()

    # s = input("请输入从第几行开始执行: ")
    # if not str.isdigit(s):
    #     s = 0
    s=0
    print("本次要执行的任务是: %s" % taskDirs[int(x)-1])
    AutoMan(taskDirs[int(x)-1]).run(int(s))


    # commands = parseContent(content)
    # # pprint.pprint(commands);exit();
    # executeCommand(commands);exit()
    # mouseClickImage(0, 'left', ['4.png'], 3)
