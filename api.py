import aiohttp
import asyncio
import uuid

from hypercorn.asyncio import serve
from hypercorn.config import Config
from quart import Quart, abort, jsonify, request
from urllib.parse import parse_qs

from astrbot.api import logger


class PushAPIServer:
    def __init__(self, token: str, in_queue):
        self.app = Quart(__name__)
        self.token = token
        self.in_queue = in_queue
        self._setup_routes()
        self._server_task: asyncio.Task | None = None

    def _setup_routes(self):
        @self.app.errorhandler(400)
        async def bad_request(e):
            return jsonify({"error": "Bad Request", "details": str(e)}), 400

        @self.app.errorhandler(403)
        async def forbidden(e):
            return jsonify({"error": "Forbidden", "details": str(e)}), 403

        @self.app.errorhandler(500)
        async def server_error(e):
            return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

        @self.app.route("/send", methods=["POST"])
        async def send_endpoint():
            auth_header = request.headers.get("Authorization")
            if not auth_header or auth_header != f"Bearer {self.token}":
                logger.warning(f"来自 {request.remote_addr} 的令牌无效")
                abort(403, description="无效令牌")

            data = await request.get_json()
            if not data:
                abort(400, description="无效的 JSON")

            required_fields = {"content", "umo"}
            if missing := required_fields - data.keys():
                abort(400, description=f"缺少字段: {missing}")

            images = []
            if "images" in data:
                images = data["images"].split(",")
                
            image_bytes = []
            for image_url in images:
                if not image_url.startswith("http"):
                    logger.error(f"无效的图片 URL: {image_url}")
                image_byte = await self._get_image_bytes(image_url)
                if not image_byte:
                    logger.error(f"获取图片失败: {image_url}")
                image_bytes.append(image_byte)

            message = {
                "message_id": data.get("message_id", str(uuid.uuid4())),
                "content": data["content"],
                "umo": data["umo"],
                "type": data.get("message_type", "text"),
                "callback_url": data.get("callback_url"),
                "image_bytes": image_bytes,
            }

            self.in_queue.put(message)
            logger.info(f"消息已排队: {message['message_id']}")

            return jsonify(
                {
                    "status": "queued",
                    "message_id": message["message_id"],
                    "queue_size": self.in_queue.qsize(),
                }
            )

        @self.app.route("/send_form", methods=["POST"])
        async def send_form_endpoint():
            auth_header = request.headers.get("Authorization")
            if not auth_header or auth_header != f"Bearer {self.token}":
                logger.warning(f"来自 {request.remote_addr} 的令牌无效")
                abort(403, description="无效令牌")

            params_form = await request.get_data(as_text=True)
            params = parse_qs(params_form)
            data = {k: v[0] for k, v in params.items()}
            if not data:
                abort(400, description="无效的 Form Data")

            required_fields = {"content", "umo"}
            if missing := required_fields - data.keys():
                abort(400, description=f"缺少字段: {missing}")
                
            images = []
            if "images" in data:
                images = data["images"].split(",")
                
            image_bytes = []
            for image_url in images:
                if not image_url.startswith("http"):
                    logger.error(f"无效的图片 URL: {image_url}")
                image_byte = await self._get_image_bytes(image_url)
                if not image_byte:
                    logger.error(f"获取图片失败: {image_url}")
                image_bytes.append(image_byte)

            message = {
                "message_id": data.get("message_id", str(uuid.uuid4())),
                "content": data["content"],
                "umo": data["umo"],
                "type": data.get("message_type", "text"),
                "callback_url": data.get("callback_url"),
                "image_bytes": image_bytes,
            }

            self.in_queue.put(message)
            logger.info(f"消息已排队: {message['message_id']}")

            return jsonify(
                {
                    "status": "queued",
                    "message_id": message["message_id"],
                    "queue_size": self.in_queue.qsize(),
                }
            )

        @self.app.route("/health", methods=["GET"])
        async def health_check():
            return jsonify(
                {
                    "status": "ok",
                    "queue_size": self.in_queue.qsize(),
                }
            )

    async def _get_image_bytes(self, image_url: str) -> bytes:
        """从URL获取图片字节"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status != 200:
                        raise Exception(f"无法获取图片: {resp.status}")
                    return await resp.read()
        except Exception as e:
            logger.error(f"{image_url}, 获取图片失败: {str(e)}")
            return b""

    async def start(self, host: str, port: int):
        """启动HTTP服务"""
        config = Config()
        config.bind = [f"{host}:{port}"]
        self._server_task = asyncio.create_task(serve(self.app, config))
        logger.info(f"PushLite服务已启动于 {host}:{port}")

        try:
            await self._server_task
        except asyncio.CancelledError:
            logger.info("请求关闭服务")
        finally:
            await self.close()

    async def close(self):
        """关闭资源"""
        if self._server_task:
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                pass


def run_server(token: str, host: str, port: int, in_queue):
    """子进程入口"""
    server = PushAPIServer(token, in_queue)
    asyncio.run(server.start(host, port))
