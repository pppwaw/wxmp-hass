import werobot,json,aip,re
from hassbridge import HASS
class wxrobot:
    def __init__(self,hass,config:dict,regex:dict):
        self.hass=hass
        self.robot = werobot.WeRoBot()
        for k,v in config.items():
            self.robot.config[k]=v
        self.regex=regex
        self.robot.config['HOST'] = '0.0.0.0'
        self.robot.add_handler(self.recv,"text")
        self.robot.add_handler(self.recv, "voice")
    def run(self):
        self.robot.run()
    def recv(self,message):
        if message.type == "voice":
            text = message.recognition
        else:
            text=message.content
        return self.zhinengjiaju(text)
    def zhinengjiaju(self,text):
        for r in self.regex["find"]:
            find=re.findall(r,text)
            if find:
                rtn=self.hass.getstate(list(self.hass.states.keys())[list(self.hass.states.values()).index(find[0][0])])
                if rtn:
                    try:
                        if find[1] == "状态":
                            status=rtn["state"]
                            if status=="off":
                                status="关闭"
                            elif status=="on":
                                status="开启"
                            elif status=="cool":
                                status="制冷"
                            elif status=="heat":
                                status="制热"
                            return find[0]+"当前状态："+status
                        elif find[1]=="温度":
                            return find[0]+"当前为 {} 度".format(rtn["attributes"]["temperature"])
                    except:
                        return "查询失败！"
                return "查询失败！"
        for r in self.regex["on"]:
            find=re.findall(r,text)
            if find:
                rtn=self.hass.turn_on(list(self.hass.states.keys())[list(self.hass.states.values()).index(find[0])])
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
    with open("config.json",encoding='UTF-8') as f:
        config = json.loads(f.read())
    hass=HASS(config["hass"])
    robot=wxrobot(hass,config["wx"],config["regex"])
    robot.run()