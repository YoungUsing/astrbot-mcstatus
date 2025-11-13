from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from mcstatus import JavaServer, BedrockServer
from mcstatus.pinger import PingResponse
from mcstatus.status_response import BedrockStatusResponse
import asyncio

@register("astrbot_plugin_mcstatus", "YoungUsing", "查询Minecraft服务器状态插件", "1.0.0", "https://github.com/YoungUsing/astrbot-mcstatus/")
class MCStatusPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        logger.info("MCStatus插件已初始化")

    @filter.command("mcstatus", alias={"mc状态", "我的世界状态"})
    async def query_mc_status(self, event: AstrMessageEvent, address: str, port: int = None):
        """查询Minecraft服务器状态
        Args:
            address: 服务器地址或IP
            port: 服务器端口(可选，Java版默认25565，基岩版默认19132)
        """
        try:
            # 尝试Java版服务器查询
            java_result = await self._query_java_server(address, port or 25565)
            if java_result:
                yield event.plain_result(java_result)
                return
            
            # 尝试基岩版服务器查询
            bedrock_result = await self._query_bedrock_server(address, port or 19132)
            if bedrock_result:
                yield event.plain_result(bedrock_result)
                return
                
            yield event.plain_result(f"无法连接到服务器 {address}:{port or '默认端口'}，请检查地址和端口是否正确")
            
        except Exception as e:
            logger.error(f"查询Minecraft服务器状态时出错: {str(e)}")
            yield event.plain_result(f"查询失败: {str(e)}")

    async def _query_java_server(self, address: str, port: int) -> str:
        """查询Java版Minecraft服务器状态"""
        try:
            server = JavaServer(address, port)
            status: PingResponse = await asyncio.wait_for(server.async_status(), timeout=5)
            
            result = [
                f"🎮 Minecraft Java版服务器状态 ({address}:{port})",
                f"状态: 在线",
                f"版本: {status.version.name}",
                f"在线玩家: {status.players.online}/{status.players.max}",
                f"延迟: {status.latency:.2f}ms"
            ]
            
            if status.players.sample:
                result.append(f"玩家列表: {', '.join([p.name for p in status.players.sample])}")
                
            if status.description:
                desc = str(status.description).strip()
                if desc:
                    result.append(f"描述: {desc}")
                    
            return "\n".join(result)
            
        except Exception as e:
            logger.debug(f"Java版服务器查询失败: {str(e)}")
            return None

    async def _query_bedrock_server(self, address: str, port: int) -> str:
        """查询基岩版Minecraft服务器状态"""
        try:
            server = BedrockServer(address, port)
            status: BedrockStatusResponse = await asyncio.wait_for(server.async_status(), timeout=5)
            
            result = [
                f"🎮 Minecraft 基岩版服务器状态 ({address}:{port})",
                f"状态: 在线",
                f"版本: {status.version.name} (协议: {status.version.protocol})",
                f"在线玩家: {status.players.online}/{status.players.max}",
                f"延迟: {status.latency:.2f}ms",
                f"服务器名称: {status.server_name}"
            ]
            
            return "\n".join(result)
            
        except Exception as e:
            logger.debug(f"基岩版服务器查询失败: {str(e)}")
            return None

    async def terminate(self):
        """插件卸载时调用"""
        logger.info("MCStatus插件已卸载")