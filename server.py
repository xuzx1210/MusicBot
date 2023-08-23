import os
import random

import discord
import discord.ext.commands as commands
from dotenv import load_dotenv
from pytube import YouTube

client = commands.Bot(command_prefix=">", intents=discord.Intents.all(), activity=discord.Game(name=">help"), status=discord.Status.online)
playingLists = {}  # dict[guildId, list]


@client.event
async def on_ready():
    print(f"伺服器數量：{len(client.guilds)}")
    for guild in client.guilds:
        print(f"    {guild.name}")


@client.command(help="使機器人加入您當前的語音頻道")
async def join(ctx: commands.context.Context):
    authorVoice: discord.member.VoiceState = ctx.author.voice
    if authorVoice == None:
        await ctx.send(content="您尚未連線至任何語音頻道")
        return
    guild: discord.Guild = ctx.guild
    if discord.utils.get(client.voice_clients, guild=guild) != None:
        await ctx.send(content="機器人已連線至某語音頻道，請先使用 'leave' 指令再重新使用 'join' 指令")
        return
    await authorVoice.channel.connect()
    playingLists[guild.id] = []


@client.command(help="使機器人離開任何語音頻道")
async def leave(ctx: commands.context.Context):
    guild: discord.Guild = ctx.guild
    id = guild.id
    clientVoice: discord.voice_client.VoiceClient = discord.utils.get(client.voice_clients, guild=guild)
    if clientVoice == None:
        await ctx.send(content="機器人尚未連線至任何語音頻道")
        return
    playingLists[id] = []
    clientVoice.stop()
    playingLists.pop(id)
    await clientVoice.disconnect()
    filename = str(id)+".mp4"
    if os.path.exists(path=filename):
        os.remove(path=filename)


def playNext(guild: discord.Guild):
    id = guild.id
    filename = str(id)+".mp4"
    if os.path.exists(path=filename):
        os.remove(path=filename)
    if id not in playingLists:
        return
    if len(playingLists[id]) == 0:
        return
    # delete first song in list
    url = playingLists[id][0]
    del playingLists[id][0]
    try:
        YouTube(url=url).streams.filter(only_audio=True).first().download(filename=filename)
        discord.utils.get(client.voice_clients, guild=guild).play(discord.FFmpegPCMAudio(executable="ffmpeg", source=filename), after=lambda x: playNext(guild=guild))
    except Exception:
        playNext(guild=guild)


@client.command(help="播放音樂，請空一格後輸入YouTube連結")
async def play(ctx: commands.context.Context, url: str):
    # information
    guild: discord.Guild = ctx.guild
    clientVoice: discord.voice_client.VoiceClient = discord.utils.get(client.voice_clients, guild=guild)
    authorVoice: discord.member.VoiceState = ctx.author.voice
    # bad situation
    if authorVoice == None:
        await ctx.send(content="您尚未連線至任何語音頻道")
        return
    if clientVoice == None:
        await ctx.send(content="機器人尚未連線至任何語音頻道\n請先使用 'join' 指令")
        return
    if clientVoice.channel != authorVoice.channel:
        await ctx.send(content="您與機器人處於不同語音頻道\n請先使用 'leave' 指令再使用 'join' 指令\n或移動至機器人所在之語音頻道")
    # add link to list
    playingLists[guild.id].append(url)
    # return if is playing
    if clientVoice.is_playing():
        return
    playNext(guild=guild)


@client.command(help="暫停播放")
async def pause(ctx: commands.context.Context):
    discord.utils.get(client.voice_clients, guild=ctx.guild).pause()


@client.command(help="繼續播放")
async def resume(ctx: commands.context.Context):
    discord.utils.get(client.voice_clients, guild=ctx.guild).resume()


@client.command(help="跳過當前曲目")
async def skip(ctx: commands.context.Context):
    discord.utils.get(client.voice_clients, guild=ctx.guild).stop()


@client.command(help="顯示音樂清單")
async def list(ctx: commands.context.Context):
    id = ctx.guild.id
    if id not in playingLists:
        await ctx.send(content="無音樂清單")
        return
    if len(playingLists[id]) == 0:
        await ctx.send(content="清單中無音樂")
        return
    result = ""
    for url in playingLists[id]:
        result += url + '\n'
    await ctx.send(content=result)


@client.command(help="隨機播放")
async def shuffle(ctx: commands.context.Context):
    random.shuffle(x=playingLists[ctx.guild.id])


@client.command(help="清空音樂清單")
async def clear(ctx: commands.context.Context):
    playingLists[ctx.guild.id] = []


def main():
    load_dotenv()
    client.run(token=os.getenv(key="TOKEN"))


if __name__ == "__main__":
    main()
