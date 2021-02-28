from dingtalkchatbot.chatbot import DingtalkChatbot
from django.conf import settings


def send(message, at_mobiles=None):
    if at_mobiles is None:
        at_mobiles = []
    webhook = settings.DINGTALK_WEB_HOOK

    # 初始化机器人小丁
    # 方法一：普通初始化
    xiaoding = DingtalkChatbot(webhook)

    # 方法二：勾选“加签”选项时使用（1.5以上新功能）
    # xiaoding = DingtalkChatbot(webhook, secret=secret)

    # Text 消息 @所有人
    xiaoding.send_text(msg=('面试通知：%s' % message), at_mobiles=at_mobiles)
