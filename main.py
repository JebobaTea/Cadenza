import discord
import os
import time
import urllib
import re
import nacl
from discord.utils import get
from discord.ext import commands
from youtube_dl import YoutubeDL
from discord import FFmpegPCMAudio

bot = commands.Bot(command_prefix="ca!", activity=discord.Game(name="ca!help"))
bot.remove_command('help')
YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist': 'True'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
song_queue = []
formatted_song_queue = []


@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Help Menu", description="Cadenza's Help Menu", color=discord.Color.blue())
    embed.add_field(name="ca!ping", value="Returns a 'Pong!' after the command is received", inline=False)
    embed.add_field(name="ca!help", value="Brings up this menu.", inline=False)
    embed.add_field(name="ca!play <string:query>", value="Search and play music", inline=False)
    embed.add_field(name="ca!leave", value="Makes the bot leave your voice channel", inline=False)
    embed.add_field(name="ca!pause", value="Temporarily pauses the music", inline=False)
    embed.add_field(name="ca!resume", value="Resumes the music", inline=False)
    embed.add_field(name="ca!loop", value="Loops the current track", inline=False)
    embed.add_field(name="ca!skip", value="Skips the current track", inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.guild.voice_client.disconnect()
        embed = discord.Embed(title="Success", description="Disconnected", color=discord.Color.blue())
    else:
        embed = discord.Embed(title="Error", description="I'm not in a VC!", color=discord.Color.red())
    await ctx.send(embed=embed)


def play_next(ctx):
    vc = get(bot.voice_clients, guild=ctx.guild)
    if len(song_queue) >= 1:
        vc.play(FFmpegPCMAudio(song_queue[0], **FFMPEG_OPTIONS), after=lambda e: play_next(ctx))
        del song_queue[0]
        del formatted_song_queue[0]


@bot.command()
async def skip(ctx):
    voice = get(bot.voice_clients, guild=ctx.guild)
    if len(song_queue) >= 1:
        voice.stop()
        play_next(ctx)
        embed = discord.Embed(title="Attempting skip", description="Moving to next track in queue", color=discord.Color.blue())
    else:
        embed = discord.Embed(title="Error", description="This is the last track in the queue!", color=discord.Color.red())
    await ctx.send(embed=embed)


@bot.command()
async def play(ctx, *, arg):
    if ctx.message.author.voice == None:
        embed = discord.Embed(title="Error", description="You aren't in a VC!", color=discord.Color.red())
        await ctx.send(embed=embed)
    else:
        channel = ctx.message.author.voice.channel
        voice = discord.utils.get(ctx.guild.voice_channels, name=channel.name)
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if voice_client == None:
            voice_client = await voice.connect()
        else:
            await voice_client.move_to(channel)
        embed = discord.Embed(title="Please wait", description="Searching for the best results based on your query...", color=discord.Color.blue())
        msg = await ctx.send(embed=embed)
        search = arg
        search = search.replace(" ", "+")
        html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + search)
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        voice = get(bot.voice_clients, guild=ctx.guild)
        em = discord.Embed(title="Please wait", description="Downloading audio from URL...", color=discord.Color.blue())
        await msg.edit(embed=em)
        if not voice.is_playing():
            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info("https://www.youtube.com/watch?v=" + video_ids[0], download=False)
            URL = info['url']
            voice.play(FFmpegPCMAudio(URL, **FFMPEG_OPTIONS), after=lambda e: play_next(ctx))
            voice.is_playing()
            embed = discord.Embed(title="Success", description="Now playing "+"https://www.youtube.com/watch?v="+video_ids[0], color=discord.Color.blue())
            await msg.edit(embed=embed)
        else:
            search = arg
            search = search.replace(" ", "+")
            html = urllib.request.urlopen("https://www.youtube.com/results?search_query=" + search)
            video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
            voice = get(bot.voice_clients, guild=ctx.guild)
            with YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info("https://www.youtube.com/watch?v=" + video_ids[0], download=False)
            URL = info['url']
            embed = discord.Embed(title="Adding to queue...", description="https://www.youtube.com/watch?v="+video_ids[0], color=discord.Color.blue())
            song_queue.append(URL)
            formatted_song_queue.append("https://www.youtube.com/watch?v="+video_ids[0])
            await msg.edit(embed=embed)


@bot.command()
async def resume(ctx):
    voice = get(bot.voice_clients, guild=ctx.guild)
    if not voice.is_playing():
        voice.resume()
        embed = discord.Embed(title="Success", description="Resuming", color=discord.Color.blue())
        await ctx.send(embed=embed)


@bot.command()
async def pause(ctx):
    voice = get(bot.voice_clients, guild=ctx.guild)
    if voice.is_playing():
        voice.pause()
        embed = discord.Embed(title="Success", description="Paused", color=discord.Color.blue())
        await ctx.send(embed=embed)


@bot.command()
async def queue(ctx):
    embed = discord.Embed(title="Queue", color=discord.Color.blue())
    for i in formatted_song_queue:
        embed.add_field(name="Queued Song", value=i, inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def ping(ctx):
    start_time = time.time()
    embed = discord.Embed(title="Pinging...", description=f'Please wait', color=discord.Color.blue())
    msg = await ctx.send(embed=embed)
    end_time = time.time()
    new_embed = discord.Embed(title="Pong!", description=f'My websocket latency is: {round(bot.latency * 1000)}ms\nMy API latency is: {round((end_time - start_time) * 1000)}ms', color=discord.Color.blue())
    await msg.edit(embed=new_embed)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.CommandNotFound):
        em = discord.Embed(title="Error", description="Unknown Command", color=discord.Color.red())
        await ctx.send(embed=em)
    else:
        em = discord.Embed(title="An exception occurred.", description="Error: "+str(error), color=discord.Color.red())
        await ctx.send(embed=em)

bot.run('TOKEN')
