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

client = commands.Bot(command_prefix=">", intents=Intents.all(), activity=Game(name=">help"), status=Status.online)
playQueues = {}  # dict[guildId, list]


@client.event
async def on_ready():
    print(f"伺服器數量：{len(client.guilds)}")
    for guild in client.guilds:
        print(f"    {guild.name}")


@client.command(help="使機器人加入您當前的語音頻道")
async def join(ctx: Context):
    voiceState: VoiceState = ctx.author.voice
    guild: Guild = ctx.guild

    if voiceState == None:
        await ctx.send(content="您尚未連線至任何語音頻道")
        return
    if get(client.voice_clients, guild=guild) != None:
        await ctx.send(content="機器人已連線至某語音頻道，請先使用 'leave' 指令再重新使用 'join' 指令")
        return

    await voiceState.channel.connect()
    playQueues[guild.id] = []


@client.command(help="使機器人離開任何語音頻道")
async def leave(ctx: Context):
    guild: Guild = ctx.guild
    voiceClient: VoiceClient = get(client.voice_clients, guild=guild)
    id = guild.id

    if voiceClient == None:
        await ctx.send(content="機器人尚未連線至任何語音頻道")
        return

    playQueues[id] = []
    voiceClient.stop()
    playQueues.pop(id)
    await voiceClient.disconnect()
    filename = "music/" + str(id) + ".mp4"
    if exists(path=filename):
        remove(path=filename)


def playNext(guild: Guild):
    id = guild.id
    filename = "music/" + str(id) + ".mp4"
    if exists(path=filename):
        remove(path=filename)

    if id not in playQueues:
        return
    if len(playQueues[id]) == 0:
        return

    url = playQueues[id][0]
    del playQueues[id][0]
    try:
        YouTube(url=url).streams.filter(only_audio=True).first().download(filename=filename)
        voiceClient: VoiceClient = get(client.voice_clients, guild=guild)
        voiceClient.play(source=FFmpegPCMAudio(source=filename), after=lambda _: playNext(guild=guild))
    except Exception:
        playNext(guild=guild)


@client.command(help="播放音樂，請空一格後輸入YouTube連結")
async def play(ctx: Context, url: str):
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

    urlType: str = url.split('?')[0].split('/')[-1]
    if urlType == "watch":
        playQueues[guild.id].append(url)
    elif urlType == "playlist":
        playlist = Playlist(url=url)
        playQueues[guild.id] += playlist.video_urls
    else:
        await ctx.send("非YouTube影片或清單連結")
        return

    if voiceClient.is_playing():
        return

    playNext(guild=guild)


@client.command(help="顯示音樂清單")
async def list(ctx: Context):
    id = ctx.guild.id

    if id not in playQueues:
        await ctx.send(content="無音樂清單")
        return
    if len(playQueues[id]) == 0:
        await ctx.send(content="清單中無音樂")
        return
    if 93 < len(playQueues[id]):
        await ctx.send(content=f"共有{len(playQueues[id])}首音樂，無法列出所有連結")
        return

    result = ""
    for url in playQueues[id]:
        result += url + '\n'
    await ctx.send(content=result)


@client.command(help="清空音樂清單")
async def clear(ctx: Context):
    playQueues[ctx.guild.id] = []


@client.command(help="打亂音樂清單")
async def shuffle(ctx: Context):
    random.shuffle(x=playQueues[ctx.guild.id])


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
