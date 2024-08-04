import discord
from discord.ext import commands
from discord import app_commands
from sparkdesk_web.core import SparkWeb
from sparkdesk_api.core import SparkAPI
from websocket import create_connection, WebSocketConnectionClosedException
import textwrap
import logging
#LOGGING 日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('log/log.log', encoding='utf-8'),  # 日志文件路径
        logging.StreamHandler()  # 同时也输出到控制台
    ]
)
logger = logging.getLogger()
logging.info('\n--------------------\n已重新开始运行 - Restarted\n--------------------')

intents = discord.Intents.default()
intents.message_content = True  # 启用消息内容权限

client = commands.Bot(command_prefix="!", intents=intents)

# 事件: 当机器人准备好时触发
@client.event
async def on_ready():
    print(f'Logged in as {client.user}!')
    logging.info(f'[Sytsem] Bot 账户已设置为 {client.user}。')
    await client.tree.sync()  # 同步命令
    logging.info('[System] 已开始同步指令。')
    logging.info('[System] Bot 已准备就绪。')

# 斜杠命令: /hello
@client.tree.command(name="hello", description="Say hello")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("Hello, world!")

# command: /help
@client.tree.command(name="help", description="查看 Ad_cloesNN's bot 帮助列表")
async def help(interaction: discord.Interaction):
    help_list="""
# Ad_closeNN's bot 的指令帮助
:bell:
1.使用`/help`来查看帮助信息
2.使用`/hello`来测试机器人
3.使用`/ping`来测试延迟
4.使用`/chat`与 SparkAI 讯飞星火大模型进行一次对话（无法连续对话、无记忆）（默认使用@和API模式）
5.使用`/translate`将使用 SparkAI 讯飞星火大模型进行一次翻译（默认翻译为**简体中文（中国大陆）**）

:warning:
1.`/chat`默认使用的是API模式，API模式可能会比Web模式稍微慢一点，但是输出的效果一般会比Web模式好，建议优先选择API模式）
2.`/translate`默认将文本翻译成简体中文（中国大陆）
3.`/ping`计算的是从接收到命令到发出响应的时间差，不能完全代表实际网络延迟，但足够用于简单的延迟检查
    """

    await interaction.response.send_message(help_list)

# 斜杠命令: /chat
@client.tree.command(name="chat", description="Chat with SparkAI!")
@app_commands.describe(
    message="发给 SparkAI 的消息",
    mode="选择使用/chat的时候的模式：api为API模式（速度相对慢，但是文本格式好）；web为模拟网页模式（速度相对快，但是文本格式不好)",
    ping="选择是否在回复/chat的时候开启@提醒(ping)，默认为开启(on)"
)
@app_commands.choices(
    ping=[
        app_commands.Choice(name="on", value="on"),
        app_commands.Choice(name="off", value="off")
    ]
)

@app_commands.choices(
    mode=[
        app_commands.Choice(name="api", value="api"),
        app_commands.Choice(name="web", value="web")
    ]
)

async def chat(interaction: discord.Interaction, message: str, mode: str = 'api', ping: str = 'on'):
    username = interaction.user.name
    global offical_api
    if mode == "web":
        chat_mode = "Web"
    if mode == "api":
        chat_mode = "API"
 # single chat
    if not message:
        await interaction.response.send_message("你需要提供一个信息！", ephemeral=False)
        logging.warning(f'[/chat] @{username}：你需要提供一个信息！')
        return
    # 发送临时响应
    ping_mention = interaction.user.mention if ping == 'on' else ''
    logging.info(f"[/chat] @{username} 刚刚请求了 SparkAI 进行一次对话。")
    await interaction.response.send_message(f"{ping_mention}你的提问是 ：**{message}**\n正在等待 SparkAI 的响应...", ephemeral=False)

    try:
        def offical_api():
            global SPARKAI_DOMAIN
            SPARKAI_URL = 'wss://spark-api.xf-yun.com/v4.0/chat'
            SPARKAI_APP_ID = '1d8e76d1'
            SPARKAI_API_SECRET = 'NGE1N2QyZDA2YmY5YzJlNTU5Y2JmZjIz'
            SPARKAI_API_KEY = 'aa5d3a7cf53af8be1ffabdb110ea6bb7'
            SPARKAI_DOMAIN = '4.0Ultra'

            from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
            from sparkai.core.messages import ChatMessage
            try:
                from dotenv import load_dotenv
            except ImportError:
                raise RuntimeError('Python environment for SPARK AI is not completely set up: required package "python-dotenv" is missing.') from None

            load_dotenv()

            from sparkai.core.callbacks import StdOutCallbackHandler
            spark = ChatSparkLLM(
            spark_api_url=SPARKAI_URL,
            spark_app_id=SPARKAI_APP_ID,
            spark_api_key=SPARKAI_API_KEY,
            spark_api_secret=SPARKAI_API_SECRET,
            spark_llm_domain=SPARKAI_DOMAIN,
            streaming=False,
            )
            messages = [ChatMessage(
            role="user",
            content=message
            )]
            handler = ChunkPrintHandler()
            a = spark.generate([messages], callbacks=[handler])
            global new_response
            global response
            origin_response_api = (a.generations[0][0].text)
            global need_warp
            if len(origin_response_api) > 1000:
                new_response = textwrap.wrap(origin_response_api, width=1000)
                need_warp = "yes"
            if len(origin_response_api) <= 1000:
                response = origin_response_api
                need_warp = "no"

        def unoffical_web():
            global response
            global new_response
            global need_warp
            #codes from HildaM/sparkdesk-api (https://github.com/HildaM/sparkdesk-api)
            sparkWeb = SparkWeb(
            cookie="di_c_mti=dd583113-d969-63b9-8b90-0bc6877aa7fc; d_d_app_ver=1.4.0; daas_st={%22sdk_ver%22:%221.3.9%22%2C%22status%22:%220%22}; appid=150b4dfebe; account_id=17846903585; ui=17846903585; d_d_ci=30e20928-9987-6ed6-a8df-a39f55292b25; ssoSessionId=e1bf9c6d-0260-498b-b5c7-9f38602815ea; gt_local_id=bjOpkCiDqsYezgOlN/Ee3ViWs7KTD2sXa0gwFyWxDOvd2a1UuNMIwA==",
            fd=703157,
            GtToken="RzAwAGMpZQ0iYtBre/0acZtltqRunU+uDOQeBu48AplaMnu8TtqeMIhP9WmR0pfdN4jpBCu5NWBsz5x3ZVuDenvZbhFPm2OJ5YdhMTlBmld8LVODVQVxMtp82Kt1C4deK6+CyiXIdjRidKzVTaJ0dIMrJxmodUmbbotepnQi/on02mJuMuNBXnMsQEWIlkoHCk+u9JZwPKWmmTI/ULJYvOOA2V2JD8/DchdZkpOYxSdJv/oCnxguedy59s93hEub1/82Z5fH5QNyTGn5CZUQENfAo/vBW5f9dBLsGEe17tY7d/HQfuJR4Eo3SQ5tyftb4upm2fmEBZOLfvAMZSOzbrR6yEe75ZwUt8M6oBej/Y4zovqwTr7mxxMPphZCsGHNhbEllGxZK88kq03fCHvKzEjMWE80OzuaF8lz4YzIZOPix/1kes1HSM9a/R6Jxzj9YPNGGCC0GwpFp5ERVCRW+sh9wH05Uz+fDvFUbj/indm0V6LNlhce2c8brdDV109D3bH2p3COkpiamfxHn2MYmHgIruSUVyEjcxy/ydSy450PUTVBNa6FJaDCOSSfzrB4K9LYZlD6x0H0BddqIj4Wp6Zch1bMh4umMipyFiGgcnXJ+Cdx1CVBGUS7YrLzlIT9ZMlvr07JzG10nM2MbDl0KNAHUWSyj2/vWHgRnS/HVWUe6cV/XYVJP1mC4JFpu2fnSIVbWprodPaJBgMJbZDQXmG0cxncjZr8MA+rFEjq81Gx8+WQZIZuajuvdX2p4chufkHBIUo5A1zzYdv+nRIq/cyi3byxB3C7YHIrKuViH+3Sr4eCd3dd9IEC9INx+8/17du4pdYkz2nB0aTZHjm/YCHe1KLCVIJKUz1Mn3Ltg+rsjxkjUqKHGY9sGKgiMyNxluo/Gv+pb2dMCXkZixQRFcGXazBDSjWSJDPxWbGIWzowNcv50mxcVkYJbZHvzLcsO2r4XzCC8NMwKEn/g8+bBcACJ6qXv6fTAOh2zyhTdD8ADQFa75jc3xGl2iXn7cUfguxQUg8btVo/5hd7dNaJ7XKBdTgqcfEWSZque2N5s1PmNCVX3Jwy7ivKsUsqC9x2+jCw/o+PfeSjPJVka22QTPQYwoqDWLqpjzaqqun4/sNfJq49Hr9UDhrQGWavtOJFVf7/zu1fjyknz+6TKM120wo9gLAExFMoHrpguM7R5cwZ1mLJzhp8k0vYahtPCn2aNnBXW0TRp7LDhu9kRbCdLNEd/4OE+cVUzzNLQVXuLzGygO8WwaAoUnrr7INJHBkdf9z/WxnwNTKSQxdnLtfObNYIoSGZnFEyU1K/cs3lWPyXB8kdh2Me4r3MbosP5QXgcQFmxyAQ3rQMYQj/eOZzlcxV+Guzs/XJSeDD9PquqtPY4pJpxl4IsASfpACRFDanQW/h8J+QLvTBUS0OK9wNUiYSaiWe/ZZVNS0r8WSJR0p7JfYoOV4bdCNP6iX3Dmto5i18mqk2tuvIC0Yki9OgyeHCSmR1dJlDQQ2F2hIn2Bg051hdACAMeOKEtDenMOyattExQojPcOyAQV/GpHxm5JqNBtVftBSudsSbDYtcbjXDqXAkMPRv7kLE+ZJ3pc/Xs2Q0N+DPAd8s0TumDsIm2tP2rjhULKyb28NoufRCDKDNV9HK5rDEI+v6BNQBWNQHWIAvki/7CyRJIWFlahuXD8/T8rJyTtwmpa8JHE8CPqs82j1jBaUnqu195a05AACgPbxjHgJMiS7tLT8nRmaPJSrFtPxUkJKNbZyS5mCqUvxZopVB9R0Do8B6D2TSXRsA6XoigPl3+R/RmBdjXGAeSRV9gbbEN5m1pKiGws0Y675rEV4Qwt2NeDo93CRQt+3VbNC41twRYNO2Z4Aa4nqA2dKf/+B3mLZgITtTAkjRtilSxvStp8J3daHABuB+hJqSuWDopj41zAVak8XCVNnsbldAV0TOeUjf6TnBF2J7KGZcGR5cOBe+d92dcxsaX0ynnUEwk0PHbKSDWRJsBNAdJQsY2Bf1yu7DcEpITH5yJ1RDZcgCsgmALP2Q85Sp9/ViGz6/BCkeYQqTwKIKUEMXjwGThUh+jPfhTh9mwdL826R/hN6axgY/BiFYmyCjPLtNht4yT7jRIUmPLJVmOgi+lCqqfaP7p4/74OCSWPEuBoehD7XE7g4PjPnZWeESh2lZx7iPggnAt/mituylQzGOHWMurFk3V/bQKGxLPwAZcpApoHFw8Z/ifUM7QpvRBgrA1PaOLQgeVSLGKKdyIeZsVcgGZvUD53EqFdw0m8ho5WPKfLg27kNGJFcv50GBbp8XCDhsRw4="
            )
            origin_response_web = sparkWeb.chat(message)
            if len(origin_response_web) > 1000:
                new_response = textwrap.wrap(origin_response_web, width=1000)
                need_warp = "yes"
            if len(origin_response_web) <= 1000:
                response = origin_response_web
                need_warp = "no"
        if mode == 'web': #判断是否为web模式，如果是则执行web方式，如果不是则使用web模式
            unoffical_web()
            END_SPARKAI_DOMAIN = "3.5"
        if mode == 'api':
            offical_api()
            END_SPARKAI_DOMAIN = "4.0Ultra"
        username = interaction.user.name
        print(f"@{username} just used a token with {chat_mode} mode.")
        # 更新之前的响应
        if need_warp == "yes":
            for part in new_response:
                await interaction.channel.send(content=f"你的提问是 ：**{message}**\n**--------------------**\n**长文本，请注意**\n{ping_mention}\n**结果 **(**Model:** `SparkAI {END_SPARKAI_DOMAIN}` **{chat_mode}模式**): \n**--------------------**\n"+part)
        if need_warp == "no":
            await interaction.edit_original_response(content=f"{ping_mention}你的提问是 ：**{message}**\n**--------------------**\n**结果 **(**Model:** `SparkAI {END_SPARKAI_DOMAIN}` **{chat_mode}模式**): \n**--------------------**\n{response}")
    except Exception as e:
        print(f"An error occurred: {e}")
        await interaction.edit_original_response(content=f"{ping_mention}机器人似乎遇到问题，请重试。请及时@管理员或者服务器Owner。错误代码：\nAn error occurred: {e}")
        logging.error(f"[/chat] 遇到错误。错误代码: {e}。")
# 斜杠命令: /translate
@client.tree.command(name="translate", description="Chat with SparkAI!")
@app_commands.describe(
    origin="需要翻译的消息",
    language="选择翻译后的语言",
    ping="选择是否在回复/chat的时候开启@提醒(ping)，默认为开启(on)",
)

@app_commands.choices(
    ping=[
        app_commands.Choice(name="开启", value="on"),
        app_commands.Choice(name="关闭", value="off")
    ]
)

@app_commands.choices(
    language=[
        app_commands.Choice(name="中文（简体）", value="zh-cn"),
        app_commands.Choice(name="中文（繁体）", value="zh-tw"),
        app_commands.Choice(name="英语（美国）", value="en-us"),
        app_commands.Choice(name="英语（英国）", value="en-gb"),
        app_commands.Choice(name="西班牙语（西班牙）", value="es-es"),
        app_commands.Choice(name="法语", value="fr-fr"),
        app_commands.Choice(name="德语", value="de-de"),
        app_commands.Choice(name="日语", value="ja-jp"),
        app_commands.Choice(name="韩语", value="ko-kr"),
        app_commands.Choice(name="俄语", value="ru-ru"),
        app_commands.Choice(name="意大利语", value="it-it"),
        app_commands.Choice(name="葡萄牙语（葡萄牙）", value="pt-pt"),
        app_commands.Choice(name="葡萄牙语（巴西）", value="pt-br"),
        app_commands.Choice(name="阿拉伯语（现代标准）", value="ar-sa"),
        app_commands.Choice(name="土耳其语", value="tr-tr"),
        app_commands.Choice(name="荷兰语", value="nl-nl"),
        app_commands.Choice(name="瑞典语", value="sv-se"),
        app_commands.Choice(name="丹麦语", value="da-dk"),
        app_commands.Choice(name="芬兰语", value="fi-fi"),
        app_commands.Choice(name="挪威语", value="no-no"),
        app_commands.Choice(name="波兰语", value="pl-pl"),
        app_commands.Choice(name="捷克语", value="cs-cz"),
        app_commands.Choice(name="匈牙利语", value="hu-hu"),
        app_commands.Choice(name="希腊语", value="el-gr"),
        app_commands.Choice(name="希伯来语", value="he-il"),
    ]
)

async def translate(interaction: discord.Interaction, origin: str, language: str = 'zh-cn', ping: str = 'on'):
        username = interaction.user.name
        ping_mention = interaction.user.mention if ping == 'on' else ''
        logging.info(f"[/translate] @{username} 刚刚请求了 SparkAI 进行一次翻译。")
        await interaction.response.send_message(f"{ping_mention}正在**翻译**...请**稍等**...", ephemeral=False)
        try:
            def translate_offical_api():
                global SPARKAI_DOMAIN
                SPARKAI_URL = 'wss://spark-api.xf-yun.com/v4.0/chat'
                SPARKAI_APP_ID = '1d8e76d1'
                SPARKAI_API_SECRET = 'NGE1N2QyZDA2YmY5YzJlNTU5Y2JmZjIz'
                SPARKAI_API_KEY = 'aa5d3a7cf53af8be1ffabdb110ea6bb7'
                SPARKAI_DOMAIN = '4.0Ultra'

                from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
                from sparkai.core.messages import ChatMessage
                try:
                    from dotenv import load_dotenv
                except ImportError:
                    raise RuntimeError('Python environment for SPARK AI is not completely set up: required package "python-dotenv" is missing.') from None

                load_dotenv()

                from sparkai.core.callbacks import StdOutCallbackHandler
                spark = ChatSparkLLM(
                spark_api_url=SPARKAI_URL,
                spark_app_id=SPARKAI_APP_ID,
                spark_api_key=SPARKAI_API_KEY,
                spark_api_secret=SPARKAI_API_SECRET,
                spark_llm_domain=SPARKAI_DOMAIN,
                streaming=False,
                )
                messages = [ChatMessage(
                role="user",
                content=f"请直接翻译下面的话，翻译成{language}。你只需回答翻译后的内容，不用说比如“好的”这类词语。下面是要翻译成{language}的话：\n{origin}"
                )]
                handler = ChunkPrintHandler()
                a = spark.generate([messages], callbacks=[handler])
                global new_response
                global response
                origin_response_api = (a.generations[0][0].text)
                global need_warp
                if len(origin_response_api) > 1000:
                    new_response = textwrap.wrap(origin_response_api, width=1000)
                    need_warp = "yes"
                if len(origin_response_api) <= 1000:
                    response = origin_response_api
                    need_warp = "no"
            translate_offical_api()
            username = interaction.user.name
            logging.info(f"[/translate] @{username} 刚刚使用了一次 Translate 的 Token。")
            if need_warp == "yes":
                for part in new_response:
                    await interaction.channel.send(content=f"{ping_mention}翻译完毕。翻译后语言：{language}。\n**--------------------**\n{part}")
            if need_warp == "no":
                await interaction.edit_original_response(content=f"{ping_mention}翻译完毕。翻译后语言：{language}。\n**--------------------**\n{response}")
        except Exception as e:
            print(f"An error occurred: {e}")
            await interaction.edit_original_response(content=f"{ping_mention}机器人似乎遇到问题，请重试。如果需要，请及时@管理员或者服务器Owner。错误代码：\nAn error occurred: {e}")
            logging.error(f"[/translate] 遇到错误。错误代码: {e}。")

@client.tree.command(name="ping", description="检查机器人与请求人之间的延迟")
async def ping(interaction: discord.Interaction):
    username = interaction.user.name
    import time
    # 记录命令触发时的时间戳
    start_time = time.time()
    # 发送临时响应，确保消息被发送
    logging.info(f'[/ping] @{username}请求与bot进行ping测试。')
    await interaction.response.send_message("正在计算你的延迟...", ephemeral=True)
    # 计算延迟
    latency = (time.time() - start_time) * 1000  # 转换为毫秒
    # 更新响应消息
    await interaction.edit_original_response(content=f":ping_pong: Pong! 你的延迟为 {latency:.2f} 毫秒。")
    logging.info(f'[/ping] 测试结束，@{username}的ping值为{latency:.2f}毫秒(ms)')
# 启动机器人
import os
secret_key = os.getenv('bot_key')
client.run(secret_key)