import yaml
import os
import requests
import conf.configLoader as configLoader

from threading import Thread
from flask import Flask, request, jsonify, Response
from utils.recordlogs import logs
class MockServer:
    """
    基于flask实现的mock server,根据yaml进行模拟信息配置，
    """
    def __init__(self, config_path="mock/mock.yaml", host=configLoader.MOCK_HOST, port=configLoader.MOCK_PORT):
        self.config_path = config_path

        #本地启用的mock服务器的入口
        self.host = host
        self.port = port

        self.app = Flask(__name__)                  # 创建flask app实例
        self.mock_routes = self.load_mock_config()  # 加载mock配置
        self.setup_routes()                         # 设置URL路由

    def load_mock_config(self):
        """
        加载mock配置
        """
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def match_request(self, mock, req):
        """
        单个mock匹配规则,可以根据实际需求精细化匹配
        """
        if mock["method"].upper() != (req.method).upper():
            return False
        if mock["url"] != req.path:
            return False

        return True

    def setup_routes(self):
        """
        通过@app.route注册路由规则
        """
        @self.app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
        def catch_all(path):
            for mock in self.mock_routes:
                #进行内容匹配
                if self.match_request(mock, request):
                    return (
                        jsonify(mock["response"]["body"]),
                        mock["response"].get("status_code", 200)
                    )
                
            # 没匹配到，代理转发请求到真实服务器
            url = f"{configLoader.API_HOST}/{path}"
            method = request.method

            # 根据请求方法，转发请求并拿到响应
            try:
                resp = requests.request(
                    method=method,
                    url=url,
                    headers={key: value for key, value in request.headers if key != 'Host'},  # 避免Host冲突
                    params=request.args,
                    data=request.get_data(),
                    cookies=request.cookies,
                    allow_redirects=False,
                )
                
                # 构造Flask响应才可以返回给客户端，否则flask无法解析返回内容
                excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
                headers = [(name, value) for name, value in resp.raw.headers.items()
                        if name.lower() not in excluded_headers]
                
                response = Response(resp.content, resp.status_code, headers)
                return response
            
            except Exception as e:
                return jsonify({"error": f"代理请求失败: {e}"}), 502
            

        # 查看所有 mock 配置
        @self.app.route("/mock/configs", methods=["GET"])
        def show_configs():
            return jsonify(self.mock_routes)

    def server_run(self):
        logs.info(f"MockServer running at http://{self.host}:{self.port}")
        self.app.run(host=self.host, port=self.port)

    def thread_run(self):
        """
        启动mock server的线程
        """
        thread = Thread(target=self.server_run, daemon=True)
        thread.start()
        return thread

