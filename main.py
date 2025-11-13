from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
import astrbot.api.message_components as Comp

# 导入mcstatus库
from mcstatus import JavaServer, BedrockServer
import asyncio

@register(
    "astrbot_plugin_mcstatus", 
    "YoungUsing", 
    "Minecraft服务器状态查询插件", 
    "1.0.0", 
    "https://github.com/YoungUsing/astrbot-mcstatus/"
)
class MCStatusPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        logger.info("MCStatus插件已加载")

    @filter.command("mcstatus", alias={"mc状态", "我的世界状态"})
    async def mcstatus_command(self, event: AstrMessageEvent, address: str, bedrock: bool = False):
        '''查询Minecraft服务器状态
        用法: /mcstatus <服务器地址> [--bedrock]
        示例: /mcstatus mc.hypixel.net
        示例: /mcstatus 192.168.1.1:19132 --bedrock
        '''
        try:
            # 发送"查询中..."提示
            await event.send(event.plain_result("正在查询服务器状态，请稍候..."))
            
            # 根据是否为Bedrock版选择不同的服务器类
            if bedrock:
                server = BedrockServer.lookup(address)
                status = await asyncio.wait_for(server.async_status(), timeout=10)
                result = self.format_bedrock_status(address, status)
            else:
                server = JavaServer.lookup(address)
                # 并行获取状态和延迟
                status_task = asyncio.create_task(server.async_status())
                ping_task = asyncio.create_task(server.async_ping())
                
                status, latency = await asyncio.gather(status_task, ping_task)
                result = self.format_java_status(address, status, latency)
                
            yield event.chain_result(result)
            
        #except ServerNotFound:
            #yield event.plain_result(f"错误：未找到服务器 {address}")
        #except ConnectionRefused:
            #yield event.plain_result(f"错误：连接被拒绝 {address}")
        #except TimeoutError:
            #yield event.plain_result(f"错误：连接超时 {address}")
        #except Exception as e:
            #logger.error(f"查询服务器状态时发生错误: {str(e)}")
            #yield event.plain_result(f"查询失败：{str(e)}")

    def format_java_status(self, address, status, latency):
        """格式化Java版服务器状态信息"""
        chain = [
            Comp.Plain(f"📌 Minecraft Java服务器状态: {address}\n"),
            Comp.Plain(f"✅ 在线状态: 在线\n"),
            Comp.Plain(f"🔄 版本: {status.version.name} (协议 {status.version.protocol})\n"),
            Comp.Plain(f"👥 玩家: {status.players.online}/{status.players.max}\n"),
        ]
        
        # 如果有玩家列表，添加玩家信息
        if status.players.sample:
            players = ", ".join([p.name for p in status.players.sample])
            chain.append(Comp.Plain(f"🎮 在线玩家: {players}\n"))
        
        chain.append(Comp.Plain(f"📶 延迟: {latency:.2f} ms\n"))
        chain.append(Comp.Plain(f"📝 MOTD: {status.motd.to_plain()}\n"))
        
        return chain

    def format_bedrock_status(self, address, status):
        """格式化Bedrock版服务器状态信息"""
        return [
            Comp.Plain(f"📌 Minecraft Bedrock服务器状态: {address}\n"),
            Comp.Plain(f"✅ 在线状态: 在线\n"),
            Comp.Plain(f"🔄 版本: {status.version.name} (协议 {status.version.protocol})\n"),
            Comp.Plain(f"👥 玩家: {status.players.online}/{status.players.max}\n"),
            Comp.Plain(f"📶 延迟: {status.latency:.2f} ms\n"),
            Comp.Plain(f"📝 MOTD: {status.motd.to_plain()}\n"),
            Comp.Plain(f"🗺️ 地图: {status.map}\n"),
            Comp.Plain(f"🎮 游戏模式: {status.gamemode}\n"),
        ]

    @filter.command("mcquery", alias={"mc详细查询"})
    async def mcquery_command(self, event: AstrMessageEvent, address: str):
        '''查询Minecraft Java服务器详细信息（需要服务器开启query功能）
        用法: /mcquery <服务器地址>
        示例: /mcquery mc.hypixel.net
        '''
        try:
            await event.send(event.plain_result("正在查询服务器详细信息，请稍候..."))
            
            server = JavaServer.lookup(address)
            query = await asyncio.wait_for(server.async_query(), timeout=10)
            
            chain = [
                Comp.Plain(f"📌 Minecraft服务器详细信息: {address}\n"),
                Comp.Plain(f"🌐 地址: {query.raw['hostip']}:{query.raw['hostport']}\n"),
                Comp.Plain(f"🔄 版本: {query.software.version} {query.software.brand}\n"),
                Comp.Plain(f"📝 MOTD: {query.motd.to_plain()}\n"),
                Comp.Plain(f"🗺️ 地图: {query.map_name}\n"),
                Comp.Plain(f"👥 玩家: {query.players.online}/{query.players.max}\n"),
            ]
            
            # 插件信息
            if query.software.plugins:
                chain.append(Comp.Plain(f"🔌 插件: {', '.join(query.software.plugins)}\n"))
            else:
                chain.append(Comp.Plain(f"🔌 插件: 无\n"))
                
            # 玩家列表
            if query.players.list:
                chain.append(Comp.Plain(f"🎮 在线玩家: {', '.join(query.players.list)}\n"))
            
            yield event.chain_result(chain)
            
        except Exception as e:
            logger.error(f"查询服务器详细信息时发生错误: {str(e)}")
            yield event.plain_result(
                f"查询失败：{str(e)}\n"
                "注意：详细查询需要服务器在server.properties中启用enable-query"
            )

    async def terminate(self):
        logger.info("MCStatus插件已卸载")