import discord
import datetime
import pdf2image
import os
import re
from dotenv import load_dotenv
from os.path import join, dirname
import pyocr

from discord.ext import commands
from  discord import app_commands

# discordpy の機能で一部イベントの受け取り・スルーを制御できる=>通信量の削減
intents = discord.Intents.all()  # デフォルトのIntentsオブジェクトを生成
intents.typing = False  # typingを受け取らないように
intents.message_content = True  # メッセージコンテントの有効化
client = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    case_insensitive=True,
    intents=intents
)
# discordクライアントの準備、コマンドプレフィックス(先頭につける文字)を!に指定とメンションでも反応、上記3行のインテンツの読み込み
# 起動確認
# TOKEN = os.getenv('DISCORD_TOKEN')
dotenv_path = join(dirname(__name__), '.env')
load_dotenv(verbose=True, dotenv_path=dotenv_path)

print(intents.members)


@client.event
async def on_ready():
    # 起動後PC側にメッセージ送信
    print(datetime.datetime.now().time(),
          "on_ready/discordVer", discord.__version__)
    await client.change_presence(activity=discord.Activity(name="!pdfでPDFをjpgに", type=discord.ActivityType.playing))


@client.command()
async def pdf(ctx, *args):
    # "/"コマンドなので可変長の確保ができない=*prmなどの使用ができない、引数以外が入るとエラーを起こす->
    # BOTの除外
    # スレッドIDの取得ができない -> parentのオブジェクトがあるかどうかで判断
    try:
        checkId = ctx.message.channel.parent.id
        threadId = ctx.message.channel.id
        thFlug = 1
    except:
        thFlug = 0

    if ctx.author.bot:
        return

    # url添付の場合とメッセージが書き込まれていた際の文字列分け処理
    # tempにargsの可変長引数を\\\\で結合して1つの文字列に
    temp = "\\\\".join(args)
    # paramsに\\\\で区切った文字列を配列として代入
    params = temp.split("\\\\")
    # paramsの要素を1つずつ確認
    for i in params:
        # Disocrd内で使用しているurlの抽出
        urlGet = re.search('(https://discord.com/channels/)+[/\d+]+', i)
        # 他の文字列等でNone(NULL)が帰ってきたときを除いてオブジェクトからstringのみurlに代入
        # 複数のURL対応ならここを配列とappendにしておく
        if urlGet is not None:
            url = urlGet.string

       # urlを/で分割してIDの抽出をする
    try:
        UrlCheck = url.split('/')
    except:
        UrlCheck = []

    # ファイル添付の場合の処理
    # 送信されたメッセージに添付ファイルがあることを確認
    if ctx.message.attachments != []:
        # スレッドで呼び出されたらそのスレッド内で完結するようにする、呼ばれてないなら
        # スレッド作ってそこに送信
        if thFlug == 0:
            thread = await ctx.message.create_thread(
                name=(f"{datetime.datetime.now().strftime('%Y%m%d%H%M')}conversion image"),
                auto_archive_duration=10080,
                slowmode_delay=0
            )
        elif thFlug == 1:
            thread = client.get_channel(threadId)

        # 以下の処理でmessageはmessageオブジェクトを指しているので
        message = ctx.message
        for attachment in message.attachments:
            # pdf以外を除外
            if attachment.content_type != "application/pdf":
                continue
            #   処理関数の実行
            await conv_pdf(attachment, message, thread)
            
    # url添付の場合の処理
    elif (len(UrlCheck) != 0):
        channelId = int(UrlCheck[5])
        messageId = int(UrlCheck[6])

        channel = client.get_channel(channelId)
        message = await channel.fetch_message(messageId)

        if thFlug == 0:
            thread = await ctx.message.create_thread(
                name=(f"{ctx.message.id} conversion image"),
                auto_archive_duration=10080,
                slowmode_delay=0
            )
        elif thFlug == 1:
            thread = client.get_channel(threadId)

        for attachment in message.attachments:
            # pdf以外を除外
            if attachment.content_type != "application/pdf":
                continue
            # 処理関数の実行
            await conv_pdf(attachment, message, thread)

    # 返信の場合
    elif ctx.message.type.name == 'reply':
        channel = client.get_channel(ctx.channel.id)
        message = await channel.fetch_message(ctx.message.reference.message_id)
        if message.attachments != []:
            if thFlug == 0:
                thread = await ctx.message.create_thread(
                    name=(f"{datetime.datetime.now().strftime('%Y%m%d%H%M')} conversion image"),
                    auto_archive_duration=10080,
                    slowmode_delay=0
                )
            elif thFlug == 1:
                thread = client.get_channel(threadId)

            for attachment in message.attachments:
                # pdf以外を除外
                if attachment.content_type != "application/pdf":
                    continue
                # 処理関数の実行
                await conv_pdf(attachment, message, thread)
    # エラー処理
    else:
        await ctx.reply("ファイルもリンクも無いから変換できないンゴ")    
   
@client.command()
async def txt(ctx, *args):
    try:
        checkId = ctx.message.channel.parent.id
        threadId = ctx.message.channel.id
        thFlug = 1
    except:
        thFlug = 0

    if ctx.author.bot:
        return


    temp = "\\\\".join(args)
    # paramsに\\\\で区切った文字列を配列として代入
    params = temp.split("\\\\")
    # paramsの要素を1つずつ確認
    for i in params:
        # Disocrd内で使用しているurlの抽出
        urlGet = re.search('(https://discord.com/channels/)+[/\d+]+', i)
        # 他の文字列等でNone(NULL)が帰ってきたときを除いてオブジェクトからstringのみurlに代入
        # 複数のURL対応ならここを配列とappendにしておく
        if urlGet is not None:
            url = urlGet.string

       # urlを/で分割してIDの抽出をする
    try:
        UrlCheck = url.split('/')
    except:
        UrlCheck = []
        
    # ファイル添付の場合の処理
    # 送信されたメッセージに添付ファイルがあることを確認
    if ctx.message.attachments != []:
        # スレッドで呼び出されたらそのスレッド内で完結するようにする、呼ばれてないなら
        # スレッド作ってそこに送信
        if thFlug == 0:
            thread = await ctx.message.create_thread(
                name=(f"{datetime.datetime.now().strftime('%Y%m%d%H%M')}conversion text"),
                auto_archive_duration=10080,
                slowmode_delay=0
            )
        elif thFlug == 1:
            thread = client.get_channel(threadId)

        # 以下の処理でmessageはmessageオブジェクトを指しているので
        message = ctx.message
        for attachment in message.attachments:
            # pdf以外を除外 ->画像もいいかも
            if attachment.content_type != "application/pdf":
                continue
            #   処理関数の実行
            tools = pyocr.get_available_tools()
            if len(tools) == 0:
                await ctx.reply("OCRが起動してません。管理者に問い合わせてください")    
            
            tool = tools[0]
            await attachment.save(f"{message.id}.pdf")
            images = pdf2image.convert_from_path(f"./{message.id}.pdf")
            #lang = 'eng'
            lang = 'jpn'
            text = ""
            # 画像オブジェクトからテキストに
            for image in images:
                tmp = ""
                tmp = tool.image_to_string(
                   image,
                   lang=lang,
                   builder=pyocr.builders.TextBuilder()
               )
                text = text + tmp
            
            print(text)
            await thread.send("aaa")
            #ここまでは動いている
            
            #切り上げをすることで+1回=あまり部分の送信
            for i in range(-(len(text)//-1900)):
                await thread.send(text[:1900])
                text = text[1900:]
                
            os.remove(f"{message.id}.pdf")
                
            
            
            
    
async def conv_pdf(attachment, message, thread):
    # ファイルの保存
    await attachment.save(f"{message.id}.pdf")
    images = pdf2image.convert_from_path(f"./{message.id}.pdf")
    for index, image in enumerate(images):
        # 画像変換
        image.save(f"{message.id}-{str(index+1)}.jpg")
        # 画像送信
        await thread.send(file=discord.File(f"{message.id}-{str(index+1)}.jpg"))
        # 画像削除
        os.remove(f"{message.id}-{str(index+1)}.jpg")
    # pdfの削除
    os.remove(f"{message.id}.pdf")

client.run(os.getenv('DISCORD_TOKEN'))
