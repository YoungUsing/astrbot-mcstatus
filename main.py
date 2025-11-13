from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from mcstatus import JavaServer
from mcstatus.pinger import PingResponse
import re

@register(
    "mcserver_status", 
    "YoungUsing", 
    "查询Minecraft Java服务器状态插件", 
    "1.0.0", 
    "https://github.com/YoungUsing/astrbot-mcstatus/"
)
class MCServerStatusPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        # 端口正则表达式，用于从地址中提取端口
        self.port_pattern = re.compile(r":(\d+)$")

    @filter.command("mcs")
    async def mcserver_status(self, event: AstrMessageEvent):
        """查询Minecraft Java服务器状态
        使用方法: /mcs <服务器地址>
        示例: /mcs mc.hypixel.net
             /mcs localhost:25566"""
        try:
            # 解析用户输入的参数
            message_parts = event.message_str.strip().split()
            if len(message_parts) < 2:
                yield event.plain_result("❌ 参数不足，请使用: /mcs <服务器地址>")
                return

            server_addr = message_parts[1]
            
            # 从地址中提取端口（如果有）
            port_match = self.port_pattern.search(server_addr)
            host = server_addr
            port = None
            
            if port_match:
                port = int(port_match.group(1))
                host = server_addr[:port_match.start()]

            # 只处理Java版服务器
            server = JavaServer.lookup(f"{host}:{port}" if port else host)
            status: PingResponse = await server.async_status()
            result = self._format_java_status(host, port or 25565, status)

            yield event.plain_result(result)
            
        except Exception as e:
            logger.error(f"查询Minecraft服务器状态失败: {str(e)}")
            yield event.plain_result(f"❌ 查询失败: {str(e)}")

    def _format_java_status(self, host: str, port: int, status: PingResponse) -> str:
        """格式化Java版服务器状态信息"""
        players = status.players
        version = status.version
        
        return (
            f"🎮 Minecraft Java服务器状态\n"
            f"地址: {host}:{port}\n"
            f"版本: {version.name}\n"
            f"在线人数: {players.online}/{players.max}\n"
            f"延迟: {status.latency:.2f}ms\n"
            f"描述: {status.description}"
        )

    async def terminate(self):
        """插件卸载时的清理工作"""
        logger.info("MC Java服务器状态查询插件已卸载")