#!/usr/bin/env python3

import copy
import json
import random
from discord.ext import commands
import discord
import asyncio
import os
from .utils import song_stats, music_path, get_audio, parse_list, top_play, Timer, is_compiled, rel_path

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_channel = None
        self.queue = []
        self.playing = False
        self.ctx = None
        self.current = None
        self.timer = Timer()
        os.makedirs(rel_path("db"),exist_ok=True)
        if not os.path.isfile(rel_path(f"db{os.sep}music_stats.json")):
            with open(rel_path(f"db{os.sep}music_stats.json"), "x", encoding="utf-8") as file:
                json.dump({"data":[]}, file, indent=2, ensure_ascii=False)
        
    async def play_song(self,ctx):
        song = ""
        if(len(self.queue) > 0):
            song = self.queue[0]
            await self.ensure_voice(ctx)
        else:
            await ctx.send("No more music <:sadge:703608678649167882>")
            self.ctx = None
            self.current = None
            self.playing = False
            self.timer.start(300,self.leave,ctx)
            return

        file = music_path(song) + ".mp3"
        await ctx.send("Playing "+song)
        print(file)

        if(is_compiled()):
            opus = rel_path("opus.dll")
            print(opus)
            discord.opus.load_opus(opus)
            if not discord.opus.is_loaded():
                print("Opus not loaded! Provide opus.dll (DO NOT download this file from a sketchy site).\nMusic will not play without it.")

        source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(file, options="-b:a 128k"),
        )
        ctx.voice_client.play(
            source,
            after=self.dispatch_play_song
        )
        
        song_stats(song + ".mp3")

        self.current = self.queue.pop(0)
        self.playing = True
        self.ctx = ctx
        self.timer.cancel()

    def dispatch_play_song(self, e):
        if e is not None:
            print("Error: ", end="")
            print(e)
            return
        print("dispatched")
        coro = self.play_song(self.ctx)
        fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
        try:
            print("fut.result")
            fut.result()
        except:
            print("fail")
            pass

    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                self.voice_channel = await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not in a voice channel! <:madge:1009748173717250098>")
                return False
                #raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            pass
        return True

    async def leave(self, ctx):
        # if await self.user_is_connected(ctx) and self.voice_channel.is_connected():
        try:
            await ctx.send("<a:kekbye:1264754885182754998> I'm outta this joint")
            self.queue = []
            self.current = None
            self.voice_channel.stop()
            await self.voice_channel.disconnect()
            self.voice_channel = None
        except:
            print("error leaving kekl")
            pass


    @commands.command(pass_context=True)
    async def join(self,ctx):
        # Check if the author is in a voice channel
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            self.voice_channel = await channel.connect()
            await ctx.send(f'Joined {channel} <:gachihyper:717874121429614653>')
        else:
            await ctx.send("You are not in a voice channel! <:madge:1009748173717250098>")

    def add_result(self,song_list):
        if(len(song_list) > 0):
            for s in song_list:
                print(f'added {s} async')
                self.queue.append(s)

    @commands.command(pass_context=True)
    async def play(self,ctx,*args):
        can_play = await self.ensure_voice(ctx)
        if(not can_play):
            return

        if(len(args) == 0):
            await ctx.send("Link <a:a52updates:1122163070815449160>")
            return
        res = []

        if(args[0] == "toplist"):
            #play toplist
            pl = top_play()
            random.shuffle(pl)
            for song in pl:
                try:
                    res = get_audio(song,self.add_result,self.bot.loop)
                    for s in res:
                        if(not s in self.queue):
                            self.queue.append(s)
                except:
                    print("Skipped "+song)
            await ctx.send(f'Queued top 50 songs in random order <:kekpipe:1009720099692888114>')
            self.ctx = ctx
            if(not self.playing):
                self.playing = True
                await self.play_song(ctx)  
            return

        try:
            res = get_audio(" ".join(args),self.add_result,self.bot.loop)
        except:
            print("error")
            res = []
        if(not res):
            await ctx.send("Something went wrong, probably a regex/throttling issue <:admiralb:888877774964682772> ")
            return
        if(len(res) == 0):
            await ctx.send("Link <a:a52updates:1122163070815449160>")
            return

        for s in res:
            self.queue.append(s)
        if(len(res) > 1):
            await ctx.send(f'Queued {len(res)} songs')
        else:
            await ctx.send(f'Queued {res[0]}')
        
        self.ctx = ctx
        if(not self.playing):
            self.playing = True
            await self.play_song(ctx)       

    async def user_is_connected(self,ctx):
        if ctx.author.voice is None:
            return False
        else:
            return True

    @commands.command(pass_context=True)
    async def skip(self, ctx, *args):
        count = 1
        if(len(args) > 0):
            if(args[0] and args[0].isnumeric()):
                try:
                    count = int(args[0])
                except:
                    pass
        if(count < 1):
            count = 1
        if(count > len(self.queue)):
            count = len(self.queue) + 1

        cloned = copy.deepcopy(self.queue)
        cloned.insert(0,self.current)
        for i in range(0, count-1):
            skipped = self.queue.pop(0)
            song_stats(skipped + ".mp3","skipped")

        if await self.user_is_connected(ctx) and self.voice_channel.is_connected() and self.playing:
            msg = f'Skipped {", ".join(cloned[0:count])}'
            msg += "\nYou better not have skipped gachi <:fatmald:677160470875996171>"
            await ctx.send(msg)
            song_stats(self.current + ".mp3","skipped")
            self.voice_channel.stop()

    
    @commands.command(pass_context=True)
    async def pop(self, ctx, *args):
        count = 1
        if(len(args) > 0):
            if(args[0] and args[0].isnumeric()):
                try:
                    count = int(args[0])
                except:
                    pass
        if(count < 1):
            count = 1
        if(count > len(self.queue)):
            count = len(self.queue) + 1

        skipped = None
        # if count is 1, we pop current
        # if count is 2 (n+1) we remove index 0 (n-2)
        if(count == 1):
            msg = "You better not have popped gachi <:fatmald:677160470875996171>"
            await ctx.send(msg)
            self.voice_channel.stop()
            song_stats(self.current + ".mp3","skipped")
            return

        try:
            skipped = self.queue.pop(count-2)
        except:
            await ctx.send("Failed to pop index "+str(count))

        if(skipped == None):
            return
        song_stats(skipped + ".mp3","skipped")
        msg = "You better not have popped gachi <:fatmald:677160470875996171>"
        await ctx.send(msg)


    @commands.command(pass_context=True)
    async def queue(self, ctx, *args):
        cloned = copy.deepcopy(self.queue)

        if(self.current):
            cloned.insert(0,self.current)
        msg = ""
        count = 1

        for song in cloned:
            msg += f'{count}. {song}'
            if(count <= len(cloned)):
                msg += "\n"
            count += 1
        if(len(msg) > 0):
            await ctx.send(f'```{msg}```')
        else:
            await ctx.send("No songs queued!")

    @commands.command(pass_context=True)
    async def toplist(self, ctx, *args):
        top = parse_list(args)
        for chunk in top:
            await ctx.send(f'```{chunk}```')

    @commands.command(pass_context=True)
    async def shuffle(self, ctx, *args):
        random.shuffle(self.queue)
        await ctx.send(f'```Shuffled queue! <:game_die:>```')

    @commands.command(pass_context=True)
    async def stinkers(self, ctx, *args):
        await ctx.send(f'```{parse_list(args, key="skipped")}```')        
        


async def setup(bot):
    await bot.add_cog(Music(bot))

