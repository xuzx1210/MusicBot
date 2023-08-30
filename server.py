import random
from os import getenv, remove
from os.path import exists

import discord.ext.commands as commands
from discord import FFmpegPCMAudio, Game, Guild, Intents, Status
from discord.ext.commands.context import Context
from discord.member import VoiceState
from discord.utils import get
from discord.voice_client import VoiceClient
from dotenv import load_dotenv
from pytube import YouTube
from pytube.contrib.playlist import Playlist

LIST_MAX_LENGTH: int = 90
client = commands.Bot(command_prefix=">", intents=Intents.all(), activity=Game(name=">help"), status=Status.online)


class PlayingInfo():
    def __init__(self) -> None:
        self.playQueue: list[str] = []  # list[url]
        self.current: str = ""  # str
        self.loopSong = False  # bool
        self.loopList = False  # bool


guildsInfo: dict[int, PlayingInfo] = {}


@client.event
async def on_ready():
    print(f"伺服器數量：{len(client.guilds)}")
    for guild in client.guilds:
        print(f"    {guild.name}")


@client.command(help="使機器人加入您當前的語音頻道")
async def join(ctx: Context):
    voiceState: VoiceState = ctx.author.voice
    guild: Guild = ctx.guild
    id: int = guild.id

    if voiceState == None:
        await ctx.send(content="您尚未連線至任何語音頻道")
        return
    if get(client.voice_clients, guild=guild) != None:
        await ctx.send(content="機器人已連線至某語音頻道，請先使用 'leave' 指令再重新使用 'join' 指令")
        return

    await voiceState.channel.connect()
    guildsInfo[id] = PlayingInfo()


@client.command(help="使機器人離開任何語音頻道")
async def leave(ctx: Context):
    guild: Guild = ctx.guild
    voiceClient: VoiceClient = get(client.voice_clients, guild=guild)
    id: int = guild.id

    if voiceClient == None:
        await ctx.send(content="機器人尚未連線至任何語音頻道")
        return

    guildsInfo[id].playQueue = []
    voiceClient.stop()
    guildsInfo.pop(id)
    await voiceClient.disconnect()
    filename = "music/" + str(id) + ".mp4"
    if exists(path=filename):
        remove(path=filename)


def playNext(guild: Guild):
    id: int = guild.id
    filename: str = "music/" + str(id) + ".mp4"
    if exists(path=filename):
        remove(path=filename)

    if id not in guildsInfo:
        return
    if len(guildsInfo[id].playQueue) == 0:
        return

    url = ""
    if guildsInfo[id].loopSong and guildsInfo[id].current != "":
        url = guildsInfo[id].current
    else:
        url = guildsInfo[id].playQueue[0]
        del guildsInfo[id].playQueue[0]
    if guildsInfo[id].loopList and guildsInfo[id].current != "":
        guildsInfo[id].playQueue.append(guildsInfo[id].current)
    try:
        YouTube(url=url).streams.filter(only_audio=True).first().download(filename=filename)
        voiceClient: VoiceClient = get(client.voice_clients, guild=guild)
        guildsInfo[id].current = url
        voiceClient.play(source=FFmpegPCMAudio(source=filename), after=lambda _: playNext(guild=guild))
    except Exception:
        playNext(guild=guild)


@client.command(help="播放音樂，請空一格後輸入YouTube連結")
async def play(ctx: Context, url: str = ""):
    guild: Guild = ctx.guild
    id: int = guild.id
    voiceClient: VoiceClient = get(client.voice_clients, guild=guild)
    voiceState: VoiceState = ctx.author.voice

    if voiceState == None:
        await ctx.send(content="您尚未連線至任何語音頻道")
        return
    if voiceClient == None:
        await ctx.send(content="機器人尚未連線至任何語音頻道\n請先使用 'join' 指令")
        return
    if voiceClient.channel != voiceState.channel:
        await ctx.send(content="您與機器人處於不同語音頻道\n請先使用 'leave' 指令再使用 'join' 指令\n或移動至機器人所在之語音頻道")
        return
    if url == "":
        await ctx.send(content="請輸入YouTube連結")
        return

    urlType = url.split('?')[0].split('/')[-1]
    if urlType == "watch":
        guildsInfo[id].playQueue.append(url)
    elif urlType == "playlist":
        guildsInfo[id].playQueue += Playlist(url=url).video_urls
    else:
        await ctx.send(content="非YouTube影片或清單連結")
        return

    if voiceClient.is_playing() or voiceClient.is_paused():
        return

    playNext(guild=guild)


@client.command(help="顯示當前音樂")
async def show(ctx: Context):
    voiceClient: VoiceClient = get(client.voice_clients, guild=ctx.guild)
    if not voiceClient.is_playing():
        await ctx.send(content="無播放中音樂")
        return
    id: int = ctx.guild.id
    loopState = ""
    if guildsInfo[id].loopSong:
        loopState = "重播當前音樂中\n"
    if guildsInfo[id].loopList:
        loopState = "重播音樂清單中\n"
    await ctx.send(content=loopState+guildsInfo[id].current)


@client.command(help=f"顯示音樂清單，最多顯示{LIST_MAX_LENGTH}個連結")
async def list(ctx: Context, nums: str = ""):
    id: int = ctx.guild.id

    if id not in guildsInfo:
        await ctx.send(content="無音樂清單")
        return
    playQueueLength: int = len(guildsInfo[id].playQueue)
    if playQueueLength == 0:
        await ctx.send(content="清單中無音樂")
        return

    if nums == "":
        if LIST_MAX_LENGTH < playQueueLength:
            await ctx.send(content=f"清單中有{playQueueLength}首音樂，無法列出所有連結")
        else:
            result = ""
            for url in guildsInfo[id].playQueue:
                result += url + '\n'
            await ctx.send(content=result)
        return

    length: int = 0
    try:
        length = int(nums)
    except ValueError:
        await ctx.send(content="請輸入數字")
        return
    if length <= 0:
        await ctx.send(content="請輸入正整數")
        return
    length = min(length, LIST_MAX_LENGTH, playQueueLength)

    result: str = ""
    for i in range(length):
        result += guildsInfo[id].playQueue[i] + '\n'
    await ctx.send(content=result)


@client.command(help="清空音樂清單")
async def clear(ctx: Context):
    guildsInfo[ctx.guild.id].playQueue = []


@client.command(help="打亂音樂清單")
async def shuffle(ctx: Context):
    random.shuffle(x=guildsInfo[ctx.guild.id].playQueue)


@client.command(help="重複一首音樂或整個清單，後接\"song\"或\"list\"")
async def loop(ctx: Context, choice: str = ""):
    if choice == "":
        await ctx.send(content="請後接\"song\"或\"list\"")
        return

    voiceClient: VoiceClient = get(client.voice_clients, guild=ctx.guild)
    if voiceClient == None:
        await ctx.send(content="機器人尚未連線至任何語音頻道\n請先使用 'join' 指令")
        return

    id: int = ctx.guild.id
    if choice == "song":
        guildsInfo[id].loopSong = True
        guildsInfo[id].loopList = False
    elif choice == "list":
        guildsInfo[id].loopSong = False
        guildsInfo[id].loopList = True
    else:
        await ctx.send(content="請後接\"song\"或\"list\"")


@client.command(help="解除任何重複狀態")
async def unloop(ctx: Context):
    voiceClient: VoiceClient = get(client.voice_clients, guild=ctx.guild)
    if voiceClient == None:
        await ctx.send(content="機器人尚未連線至任何語音頻道\n請先使用 'join' 指令")
        return

    id: int = ctx.guild.id
    guildsInfo[id].loopSong = False
    guildsInfo[id].loopList = False


@client.command(help="暫停播放")
async def pause(ctx: Context):
    voiceClient: VoiceClient = get(client.voice_clients, guild=ctx.guild)
    voiceClient.pause()


@client.command(help="繼續播放")
async def resume(ctx: Context):
    voiceClient: VoiceClient = get(client.voice_clients, guild=ctx.guild)
    voiceClient.resume()


@client.command(help="跳過當前曲目")
async def skip(ctx: Context):
    voiceClient: VoiceClient = get(client.voice_clients, guild=ctx.guild)
    voiceClient.stop()


def main():
    load_dotenv()
    client.run(token=getenv(key="TOKEN"))


if __name__ == "__main__":
    main()
