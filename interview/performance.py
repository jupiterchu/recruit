import logging
import time
import traceback

from django.http import HttpResponse

from interview import dingtalk

logger = logging.getLogger(__name__)


def performance_logger_middleware(get_response):
    # 接受一个 get_response 参数的函数，是 Django 中用来处理视图的函数，处理视图的响应，或者是另外一个中间件的处理它的结构的一个函数处理得到了中间件的处理结果之后鬼内容
    def middleware(request):
        # 对请求的 request 做处理，之后返回出去
        start_time = time.time()
        response = get_response(request)
        duration = time.time() - start_time
        response["X-Page-Duration-ms"] = int(duration * 1000)  # 在响应头中加入响应时间
        logger.info("%s %s %s", duration, request.path, request.GET.dict())  # 获取 url 参数加载到 log 中
        return response

    return middleware


class PerformanceAndExceptionLoggerMiddleware:
    def __init__(self, get_response):
        # 第一次，配置和初始化
        self.get_response = get_response

    def __call__(self, request, *args, **kwargs):
        # 在调用视图（以及后来的中间件）之前，为每个请求执行的代码。
        response = self.get_response(request)
        start_time = time.time()
        duration = time.time() - start_time
        response["X-Page-Duration-ms"] = int(duration * 1000)  # 在响应头中加入响应时间
        logger.info("%s %s %s", duration, request.path, request.GET.dict())  # 获取 url 参数加载到 log 中

        # if duration >300: # 将慢响应发送到 sentry 服务器，普通消息
            # capture_message("slow request for url:%s with duration:%s" % (request.build_absolute_uri(), duration))

        # 调用视图后对每个请求 / 响应执行的代码。
        return response

    def process_exception(self, request, exception):
        """对所有异常的处理逻辑"""
        if exception:
            message = "url:{url} ** msg:{error} ````{tb}````".format(
                url = request.build_absolute_uri(),
                error = repr(exception),
                tb = traceback.format_exc()
            )

            logger.warning(message)

            # 发送钉钉信息
            dingtalk.send(message)

            # 捕获异常到 sentry
            # capture_exception(exception)

        return HttpResponse("Error processing the request, please contact the system administrator.", status=500)