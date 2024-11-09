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
from pytubefix import YouTube
from pytubefix.contrib.playlist import Playlist

LIST_MAX_LENGTH: int = 2000
MUSIC_FOLDER: str = "music/"
client = commands.Bot(command_prefix=">", intents=Intents.all(), activity=Game(name=">help"), status=Status.online)


class GuildPlayingInfo():
    def __init__(self) -> None:
        self.playQueue = []  # list[url]
        self.current = ""  # str
        self.loopSong = False  # bool
        self.loopList = False  # bool
        self.downloadSuccess = False  # bool


guildPlayingInfoDict: dict[int, GuildPlayingInfo] = {}


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

    guildPlayingInfoDict[id] = GuildPlayingInfo()
    await voiceState.channel.connect()


@client.command(help="使機器人離開任何語音頻道")
async def leave(ctx: Context):
    guild: Guild = ctx.guild
    id: int = guild.id
    voiceClient: VoiceClient = get(client.voice_clients, guild=guild)

    if voiceClient == None:
        await ctx.send(content="機器人尚未連線至任何語音頻道")
        return

    guildPlayingInfoDict[id].playQueue = []
    voiceClient.stop()
    guildPlayingInfoDict.pop(id)
    await voiceClient.disconnect()
    filename = MUSIC_FOLDER + str(id) + ".mp4"
    if exists(path=filename):
        remove(path=filename)


def playNext(guild: Guild):
    id: int = guild.id
    filename: str = str(id) + ".mp4"
    filepath: str = MUSIC_FOLDER + filename
    if exists(path=filepath):
        remove(path=filepath)

    if id not in guildPlayingInfoDict:
        return

    info: GuildPlayingInfo = guildPlayingInfoDict[id]
    voiceClient: VoiceClient = get(client.voice_clients, guild=guild)
    if info.loopSong and info.downloadSuccess:
        info.playQueue.insert(0, info.current)
    if info.loopList and info.downloadSuccess:
        info.playQueue.append(info.current)
    if len(info.playQueue) == 0:
        return

    try:
        url = info.playQueue[0]
        del info.playQueue[0]
        YouTube(url=url).streams.get_audio_only().download(output_path=MUSIC_FOLDER, filename=filename)
        info.current = url
        info.downloadSuccess = True
        voiceClient.play(source=FFmpegPCMAudio(source=filepath), after=lambda _: playNext(guild=guild))
    except Exception:
        info.downloadSuccess = False
        playNext(guild=guild)


@client.command(help="播放音樂，請空一格後輸入YouTube連結")
async def play(ctx: Context, url: str = ""):
    guild: Guild = ctx.guild
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
    info: GuildPlayingInfo = guildPlayingInfoDict[guild.id]
    if urlType == "playlist":
        info.playQueue += Playlist(url=url).video_urls
    else:
        info.playQueue.append(url)

    if voiceClient.is_playing() or voiceClient.is_paused():
        return

    playNext(guild=guild)


@client.command(help="插播音樂，請空一格後輸入YouTube連結")
async def intercut(ctx: Context, url: str = ""):
    guild: Guild = ctx.guild
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
    info: GuildPlayingInfo = guildPlayingInfoDict[guild.id]
    if urlType == "playlist":
        info.playQueue = Playlist(url=url).video_urls + info.playQueue
    else:
        info.playQueue.insert(0, url)

    if voiceClient.is_playing() or voiceClient.is_paused():
        return

    playNext(guild=guild)


@client.command(help="顯示當前音樂")
async def show(ctx: Context):
    voiceClient: VoiceClient = get(client.voice_clients, guild=ctx.guild)
    if voiceClient == None:
        await ctx.send(content="機器人尚未連線至任何語音頻道\n請先使用 'join' 指令")
        return
    if not voiceClient.is_playing():
        await ctx.send(content="無播放中音樂")
        return

    info: GuildPlayingInfo = guildPlayingInfoDict[ctx.guild.id]
    loopState = ""
    if info.loopSong:
        loopState = "重播當前音樂中\n"
    if info.loopList:
        loopState = "重播音樂清單中\n"
    await ctx.send(content=loopState+info.current)


@client.command(help=f"顯示音樂清單，最多顯示{LIST_MAX_LENGTH}個連結")
async def list(ctx: Context, nums: str = ""):
    voiceClient: VoiceClient = get(client.voice_clients, guild=ctx.guild)
    if voiceClient == None:
        await ctx.send(content="機器人尚未連線至任何語音頻道\n請先使用 'join' 指令")
        return
    id: int = ctx.guild.id
    if id not in guildPlayingInfoDict:
        await ctx.send(content="無音樂清單")
        return
    playQueueLength: int = len(guildPlayingInfoDict[id].playQueue)
    if playQueueLength == 0 and not voiceClient.is_playing() and not voiceClient.is_paused():
        await ctx.send(content="清單中無音樂")
        return

    result: str = ""

    info: GuildPlayingInfo = guildPlayingInfoDict[ctx.guild.id]

    if info.loopSong:
        result = "正在重複當前曲目\n"
    elif info.loopList:
        result = "正在重複音樂清單\n"
    else:
        result = "尚未設定重複功能\n"

    if voiceClient.is_playing() or voiceClient.is_paused():
        result += '\n當前曲目：' + YouTube(url=guildPlayingInfoDict[ctx.guild.id].current).title + '\n'

    if nums == "":
        for idx, url in enumerate(guildPlayingInfoDict[id].playQueue):
            try:
                title: str = YouTube(url=url).title
                result += '\n' + str(idx + 1) + ". " + title
                if LIST_MAX_LENGTH <= len(result):
                    break
            except Exception:
                result += '\n' + str(idx + 1) + ". " + "無效的YouTube連結"
    else:
        length: int = 0
        try:
            length = int(nums)
        except ValueError:
            await ctx.send(content="請輸入數字")
            return
        if length <= 0:
            await ctx.send(content="請輸入正整數")
            return
        length = min(length, playQueueLength)

        for i in range(length):
            try:
                title: str = YouTube(url=guildPlayingInfoDict[id].playQueue[i]).title
                result += '\n' + str(i + 1) + ". " + title
                if LIST_MAX_LENGTH <= len(result):
                    break
            except Exception:
                result += '\n' + str(i + 1) + ". " + "無效的YouTube連結"

    result = result[:LIST_MAX_LENGTH]

    await ctx.send(content=result)


@client.command(help="清空音樂清單")
async def clear(ctx: Context):
    voiceClient: VoiceClient = get(client.voice_clients, guild=ctx.guild)
    if voiceClient == None:
        await ctx.send(content="機器人尚未連線至任何語音頻道\n請先使用 'join' 指令")
        return
    id: int = ctx.guild.id
    if id not in guildPlayingInfoDict:
        await ctx.send(content="無音樂清單")
        return
    guildPlayingInfoDict[id].playQueue = []


@client.command(help="打亂音樂清單")
async def shuffle(ctx: Context):
    voiceClient: VoiceClient = get(client.voice_clients, guild=ctx.guild)
    if voiceClient == None:
        await ctx.send(content="機器人尚未連線至任何語音頻道\n請先使用 'join' 指令")
        return
    id: int = ctx.guild.id
    if id not in guildPlayingInfoDict:
        await ctx.send(content="無音樂清單")
        return
    random.shuffle(x=guildPlayingInfoDict[id].playQueue)


@client.command(help="重複一首音樂或整個清單，後接\"song\"或\"list\"")
async def loop(ctx: Context, choice: str = ""):
    voiceClient: VoiceClient = get(client.voice_clients, guild=ctx.guild)
    if voiceClient == None:
        await ctx.send(content="機器人尚未連線至任何語音頻道\n請先使用 'join' 指令")
        return
    id: int = ctx.guild.id
    if id not in guildPlayingInfoDict:
        await ctx.send(content="無音樂清單")
        return
    if choice == "":
        await ctx.send(content="請後接\"song\"或\"list\"")
        return

    if choice == "song":
        guildPlayingInfoDict[id].loopSong = True
        guildPlayingInfoDict[id].loopList = False
    elif choice == "list":
        guildPlayingInfoDict[id].loopSong = False
        guildPlayingInfoDict[id].loopList = True
    else:
        await ctx.send(content="請後接\"song\"或\"list\"")


@client.command(help="解除任何重複狀態")
async def unloop(ctx: Context):
    voiceClient: VoiceClient = get(client.voice_clients, guild=ctx.guild)
    if voiceClient == None:
        await ctx.send(content="機器人尚未連線至任何語音頻道\n請先使用 'join' 指令")
        return
    id: int = ctx.guild.id
    if id not in guildPlayingInfoDict:
        await ctx.send(content="無音樂清單")
        return

    guildPlayingInfo: GuildPlayingInfo = guildPlayingInfoDict[id]
    guildPlayingInfo.loopSong = False
    guildPlayingInfo.loopList = False


@client.command(help="暫停播放")
async def pause(ctx: Context):
    voiceClient: VoiceClient = get(client.voice_clients, guild=ctx.guild)
    if voiceClient == None:
        await ctx.send(content="機器人尚未連線至任何語音頻道\n請先使用 'join' 指令")
        return

    voiceClient.pause()


@client.command(help="繼續播放")
async def resume(ctx: Context):
    voiceClient: VoiceClient = get(client.voice_clients, guild=ctx.guild)
    if voiceClient == None:
        await ctx.send(content="機器人尚未連線至任何語音頻道\n請先使用 'join' 指令")
        return

    voiceClient.resume()


@client.command(help="跳過當前曲目")
async def skip(ctx: Context):
    voiceClient: VoiceClient = get(client.voice_clients, guild=ctx.guild)
    if voiceClient == None:
        await ctx.send(content="機器人尚未連線至任何語音頻道\n請先使用 'join' 指令")
        return

    voiceClient.stop()


def main():
    load_dotenv()
    client.run(token=getenv(key="TOKEN"))


if __name__ == "__main__":
    main()
