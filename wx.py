version='1.0.0'
import werobot,json,re,requests
from hassbridge import HASS
def gnuversion(version1,version2):
    v1 = version1.split(".")
    v2 = version2.split(".")
    if v2[0]>v1[0]:return 2
    elif v2[0]==v1[0]:
        if v2[1]>v1[1]:return 2
        elif v2[1]==v1[1]:
            if v2[2]>v1[2]:return 2
            elif v2[2]==v1[2]:return 0
            else:return 1
        else:return 1
    else:return 1
class wxrobot:
    def __init__(self,hass,config:dict,users:dict,regex:dict):
        self.hass=hass
        self.robot = werobot.WeRoBot()
        for k,v in config.items():
            self.robot.config[k]=v
        self.users=users
        self.regex=regex
        self.robot.config['HOST'] = '0.0.0.0'
        self.robot.add_handler(self.subscribe, "subscribe_event")
        self.robot.add_handler(self.recv,"text")
        self.robot.add_handler(self.recv, "voice")
    def run(self):
        self.robot.run()
    def subscribe(self,message,session):
        if "user" not in session:
            if "block" not in session:
                session["test"]=0
                return "请用文字发送你的名字！"
            else:
                return "您已被封禁！"
        else:
            return "您已认证！"
    def recv(self,message,session):
        if "block" not in session:
            if "user" in session:
                if message.type == "voice":
                    text = message.recognition
                else:
                    text=message.content
                return self.zhinengjiaju(text)
            else:
                try:text = message.content
                except:return "请使用文字！"
                if text in self.users:
                    session["user"]=text
                    return "认证成功！"
                else:
                    if session["test"] == 10:
                        session["block"]=True
                        return "您的错误次数达到十次，已被封禁！如需解封请联系管理员！"
                    else:
                        session["test"]+=1
                        return "认证错误！"
        else:
            return "您已被封禁！"
    def zhinengjiaju(self,text):
        for r in self.regex["find"]:
            find=re.findall(r,text)
            if find:
                rtn=self.hass.getstate(list(self.hass.states.keys())[list(self.hass.states.values()).index(find[0][0].replace("的",""))])
                domain=rtn["entity_id"].split(".")[0]
                if rtn:
                    if domain == "climate":
                        if find[0][1] == "状态":
                            status=rtn["state"]
                            if status=="off":
                                status="关闭"
                            elif status=="on":
                                status="开启"
                            elif status=="cool":
                                status="制冷"
                            elif status=="heat":
                                status="制热"
                            return find[0][0]+"当前状态："+status
                        elif find[0][1]=="温度":
                            return find[0][0]+"当前为 {} 度".format(rtn["attributes"]["temperature"])
                        elif find[0][1]=="模式":
                            mode=rtn["attributes"]["fan_mode"]
                            if mode=="auto":
                                mode="自动"
                            elif mode=="powerful":
                                mode="强劲"
                            elif mode=="sleep":
                                mode="静音"
                            return find[0][0]+"当前模式： "+mode
                        else:
                            print(rtn)
                            return "暂未支持！请将服务端的打印信息在github上发布issue！"
                    elif domain == "switch":
                        if find[0][1] == "状态":
                            status = rtn["state"]
                            if status == "off":
                                status = "关闭"
                            elif status == "on":
                                status = "开启"
                            return find[0][0] + "当前状态：" + status
                        else:
                            print(rtn)
                            return "暂未支持！请将服务端的打印信息在github上发布issue！"
                    elif domain == "light":
                        if find[0][1] == "状态":
                            status = rtn["state"]
                            if status == "off":
                                status = "关闭"
                            elif status == "on":
                                status = "开启"
                            return find[0][0] + "当前状态：" + status
                        elif find[0][1] == "亮度":
                            light=rtn['attributes']['brightness']
                            light=int(light/255)*100
                            return find[0][0] + "当前亮度：" + str(light) + "%"
                        else:
                            print(rtn)
                            return "暂未支持！请将服务端的打印信息在github上发布issue！"
                    else:
                        print(rtn)
                        return "暂未支持！请将服务端的打印信息在github上发布issue！"
                return "查询失败！"
        for r in self.regex["on"]:
            find=re.findall(r,text)
            if find:
                rtn=self.hass.turn_on(list(self.hass.states.keys())[list(self.hass.states.values()).index(find[0].replace("的",""))])
                print(rtn)
                if rtn:
                    return "打开成功！"
                return "打开失败！"
        for r in self.regex["off"]:
            find = re.findall(r, text)
            if find:
                rtn=self.hass.turn_off(list(self.hass.states.keys())[list(self.hass.states.values()).index(find[0].replace("的",""))])
                print(rtn)
                if rtn:
                    return "关闭成功！"
                return "关闭失败"
        for r in self.regex["set"]:
            find=re.findall(r,text)
            if find:
                find=find[0]
                entity_id=list(self.hass.states.keys())[list(self.hass.states.values()).index(find[0])]
                state=self.hass.getstate(entity_id)
                data = {"entity_id": entity_id}
                try:
                    if find[0].split("的")[-1] == "空调":
                        domain = "climate"
                        if find[1]=="温度":
                            service="set_temperature"
                            data["temperature"]=re.findall("\d{2}",find[2])[0]
                        elif find[1]=="状态":
                            service="set_hvac_mode"
                            mode=re.findall("(制冷|制热|关闭|自动)",find[2])[0]
                            if mode == "制冷":
                                data["hvac_mode"]="cool"
                            elif mode == "制热":
                                data["hvac_mode"]="heat"
                            elif mode=="关闭":
                                data["hvac_mode"]="off"
                            else:
                                data["hvac_mode"]="auto"
                        elif find[1] == "模式":
                            service = "set_fan_mode"
                            mode = re.findall("(静音|强力|自动)", find[2])[0]
                            if mode == "静音":
                                data["fan_mode"]="sleep"
                            elif mode == "强力":
                                data["fan_mode"]="powerful"
                            else:
                                data["fan_mode"]="auto"
                except Exception as e:print(e);return "调整失败！"
                rtn=self.hass.setstate(domain,service,data)
                print(rtn)
                if rtn:
                    return "调整成功！"
                return "调整失败！"
        return "未知命令！"
if __name__ == "__main__":
    try:
        a = requests.get("https://raw.githubusercontent.com/pppwaw/wxmp-hass/master/wx.py").text.splitlines()[0].split("=")[1]
        if gnuversion(version,a) == 2:
            print("有更新！最新版本："+a)
    finally:
        with open("configcopy.json",encoding='UTF-8') as f:
            config = json.loads(f.read())
        hass=HASS(config["hass"])
        robot=wxrobot(hass,config["wx"],config["users"],config["regex"])
        robot.run()