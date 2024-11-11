import enum
import random
from os import getenv, remove
from os.path import exists

import discord.ext.commands as commands
from discord import FFmpegPCMAudio, Game, Guild, Intents, Status
from discord.ext import commands
from discord.ext.commands.context import Context
from discord.member import VoiceState
from discord.utils import get
from discord.voice_client import VoiceClient
from dotenv import load_dotenv
from pytubefix import YouTube
from pytubefix.contrib.playlist import Playlist
from pytubefix.contrib.search import Filter, Search

LIST_MAX_LENGTH: int = 90
MUSIC_FOLDER: str = "music/"
client = commands.Bot(command_prefix=">", intents=Intents.all(), activity=Game(name=">help"), status=Status.online)


class GuildPlayingInfo():
    def __init__(self) -> None:
        self.playQueue = []  # list[url]
        self.history = []  # list[title]
        self.current = ""  # str
        self.loopSong = False  # bool
        self.loopList = False  # bool
        self.autoplay = False  # bool


guildPlayingInfoDict: dict[int, GuildPlayingInfo] = {}


@client.event
async def on_ready():
    print(f"伺服器數量：{len(client.guilds)}")
    for guild in client.guilds:
        print(f"    {guild.name}")


@client.event
async def on_message(message):
    channel_id = 1303878058566090784
    if message.author == client.user:
        return

    if message.channel.id == channel_id and "mygo" in message.content.lower():
        ctx = await client.get_context(message)
        await ctx.invoke(client.get_command('play'), url="https://www.youtube.com/playlist?list=PLnFV3UOvtJxtyw7bBh1dvz4o75TPoA1Eb")

        guild: Guild = message.guild
        info: GuildPlayingInfo = guildPlayingInfoDict[guild.id]
        if info:
            random.shuffle(info.playQueue[1:])

    await client.process_commands(message)


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
    guildPlayingInfoDict[id].history = []
    voiceClient.stop()
    guildPlayingInfoDict.pop(id)
    await voiceClient.disconnect()
    filename = MUSIC_FOLDER + str(id) + ".mp4"
    if exists(path=filename):
        remove(path=filename)


def get_recommend():
    # Define a list of genres or keywords for music types
    genres = ['jpop music', 'cpop music', 'kpop music', 'indie music', 'pop music', 'rock music', '獨立樂團']

    def get_keyword_video(keyword: str):
        f = {'type': Filter.get_type("Video"), 'sort_by': Filter.get_sort_by(random.choice(["Relevance", "View count"])),
             'duration': Filter.get_duration(random.choice(["Under 4 minutes", "4 - 20 minutes"]))}
        results = Search(keyword, filters=f)
        videos = []
        for i, video in enumerate(results.videos):
            if i >= 2:  # Limit to 5 videos per search result
                break
            videos.append(video.watch_url)
        return videos

    # Fetch videos for all genres and combine the results
    all_videos = []
    for genre in genres:
        genre_videos = get_keyword_video(genre)
        all_videos.extend(genre_videos)

    # If no videos are found, return a message
    if not all_videos:
        return

    # Shuffle the combined list to randomize the selection
    random.shuffle(all_videos)

    # Select a single random video from the list
    random_video = all_videos[0]
    return random_video


def remove_played_song(ctx: Context, guild: Guild):
    info = guildPlayingInfoDict.get(guild.id)
    if info:
        if info.loopList and len(info.playQueue) > 0:
            info.playQueue.append(info.playQueue[0])
        if not info.loopSong and len(info.playQueue) > 0:
            yt = YouTube(info.playQueue[0])
            info.history.append(yt.title)
            if (len(info.history) > 5):
                del info.history[0]
            del info.playQueue[0]

    playNext(ctx=ctx, guild=guild)


def playNext(ctx: Context, guild: Guild):
    id: int = guild.id
    filename: str = str(id) + ".mp4"
    filepath: str = MUSIC_FOLDER + filename
    if exists(path=filepath):
        remove(path=filepath)

    if id not in guildPlayingInfoDict:
        return
    info: GuildPlayingInfo = guildPlayingInfoDict[id]
    if len(info.playQueue) == 0:
        if info.current and not info.autoplay:
            recommended_url = get_recommend()
            if recommended_url:
                info.playQueue.append(recommended_url)
            else:
                return

    try:
        url = info.playQueue[0]
        yt = YouTube(url=url)
        yt.streams.get_audio_only().download(output_path=MUSIC_FOLDER, filename=filename)
        voiceClient: VoiceClient = get(client.voice_clients, guild=guild)
        info.current = url
        voiceClient.play(source=FFmpegPCMAudio(source=filepath), after=lambda _: remove_played_song(ctx=ctx, guild=guild))
    except Exception:
        playNext(ctx=ctx, guild=guild)


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

    playNext(ctx=ctx, guild=guild)


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
        info.playQueue.insert(1, url)

    if voiceClient.is_playing() or voiceClient.is_paused():
        return

    playNext(guild=guild)


@client.command(help="搜尋並播放音樂，請空一格後輸入關鍵字")
async def search(ctx: Context, *, keyword: str):
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

    def get_keyword_video(keyword: str):
        f = {'type': Filter.get_type("Video"), 'sort_by': Filter.get_sort_by("Relevance")}
        results = Search(keyword, filters=f)
        videos = []
        for i, video in enumerate(results.videos):
            if i >= 5:
                break
            videos.append({'title': video.title, 'url': video.watch_url})
        return videos

    # Send initial message
    search_results = get_keyword_video(keyword)
    result_str = "\n".join([f"{i+1}. {video['title']} " for i, video in enumerate(search_results)])
    message = await ctx.send(content=f"搜尋結果：\n{result_str}\n請輸入編號 (1-5) 以選取要播放的影片")

    def check(m):
        return m.author == ctx.author and m.content.isdigit() and 1 <= int(m.content) <= 5

    try:
        # Wait for user selection
        selection = await client.wait_for('message', check=check, timeout=30)
        selected_video = search_results[int(selection.content) - 1]['url']
        await play(ctx, url=selected_video)
    except Exception as e:
        await ctx.send(content="發生錯誤，請再試一次。")


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


@client.command(help=f"顯示歷史播放最多5首歌")
async def history(ctx: Context):
    voiceClient: VoiceClient = get(client.voice_clients, guild=ctx.guild)
    if voiceClient == None:
        await ctx.send(content="機器人尚未連線至任何語音頻道\n請先使用 'join' 指令")
        return
    id: int = ctx.guild.id
    playQueueLength: int = len(guildPlayingInfoDict[id].history)
    if playQueueLength == 0:
        await ctx.send(content="無歷史清單")
        return
    result: str = ""
    for i, song in enumerate(guildPlayingInfoDict[id].history):
        result += f'{i+1}' + '. ' + song + '\n'
    await ctx.send(content=result)


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
    if playQueueLength == 0:
        await ctx.send(content="清單中無音樂")
        return

    if nums == "":
        if LIST_MAX_LENGTH < playQueueLength:
            await ctx.send(content=f"清單中有{playQueueLength}首音樂，無法列出所有連結")
        else:
            result = ""
            for i, url in enumerate(guildPlayingInfoDict[id].playQueue):
                if len(result) < 1930:
                    yt = YouTube(url=url)
                    result += f'{i+1}' + '. ' + yt.title + '\n'
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
    for i, url in enumerate(guildPlayingInfoDict[id].playQueue):
        if i >= length:
            break
        else:
            yt = YouTube(url=url)
            if len(result) < 1930:
                result += f'{i+1}' + '. ' + yt.title + '\n'
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
