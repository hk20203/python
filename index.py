import yaml
from login.wiseLoginService import wiseLoginService
from actions.autoSign import AutoSign
from actions.collection import Collection
from actions.workLog import workLog
from actions.sleepCheck import sleepCheck
from actions.pushKit import pushKit
from datetime import datetime, timedelta, timezone
import sys


def getYmlConfig(yaml_file='config.yml'):
    file = open(yaml_file, 'r', encoding="utf-8")
    file_data = file.read()
    file.close()
    config = yaml.load(file_data, Loader=yaml.FullLoader)
    return dict(config)


def getTimeStr():
    utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
    bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
    return bj_dt.strftime("%Y-%m-%d %H:%M:%S")


def log(content):
    print(getTimeStr() + " V%s %s" % (getYmlConfig()['Version'], content))
    sys.stdout.flush()


def main():
    log("自动化任务开始执行")
    config = getYmlConfig()
    push = pushKit(config['notifyOption'])
    for user in config['users']:
        if config['debug']:
            msg = working(user)
        else:
            try:
                msg = working(user)
                ret = True
            except Exception as e:
                msg = str(e)
                ret = False
            ntm = getTimeStr()
            if ret == True:
                #此处需要注意就算提示成功也不一定是真的成功，以实际为准
                log(msg)
                if 'SUCCESS' in msg:
                    msg = push.sendMsg(
                        '今日校园签到成功通知',
                        '服务器(V%s)于%s尝试签到成功!' % (config['Version'], ntm),
                        user['user'])
                else:
                    msg = push.sendMsg(
                        '今日校园签到异常通知', '服务器(V%s)于%s尝试签到异常!\n异常信息:%s' %
                        (config['Version'], ntm, msg), user['user'])
            else:
                log("Error:" + msg)
                msg = push.sendMsg(
                    '今日校园签到失败通知', '服务器(V%s)于%s尝试签到失败!\n错误信息:%s' %
                    (config['Version'], ntm, msg), user['user'])
            log(msg)
    log("自动化任务执行完毕")


def working(user):
    wise = wiseLoginService(user['user'])
    wise.login()
    # 登陆成功，通过type判断当前属于 信息收集、签到、查寝
    # 信息收集
    if user['user']['type'] == 0:
        # 以下代码是信息收集的代码
        collection = Collection(wise, user['user'])
        collection.queryForm()
        collection.fillForm()
        msg = collection.submitForm()
        return msg
    elif user['user']['type'] == 1:
        # 以下代码是签到的代码
        sign = AutoSign(wise, user['user'])
        sign.getUnSignTask()
        sign.getDetailTask()
        sign.fillForm()
        msg = sign.submitForm()
        return msg
    elif user['user']['type'] == 2:
        # 以下代码是查寝的代码
        check = sleepCheck(wise, user['user'])
        check.getUnSignedTasks()
        check.getDetailTask()
        check.fillForm()
        msg = check.submitForm()
        return msg
    elif user['user']['type'] == 3:
        # 以下代码是工作日志的代码
        work = workLog(wise, user['user'])
        work.checkHasLog()
        work.getFormsByWids()
        work.fillForms()
        msg = work.submitForms()
        return msg


# 阿里云的入口函数
def handler(event, context):
    main()


# 腾讯云的入口函数
def main_handler(event, context):
    main()
    return 'Finished'


if __name__ == '__main__':
    main()
