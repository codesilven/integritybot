#!/usr/bin/env python3

from concurrent.futures import ProcessPoolExecutor
import copy
import json
import random
from discord.ext import commands
import discord
import asyncio
import os
import mimetypes
import requests
from .utils import download_soundloud, download_yt_video, sanitize_filename, search_youtube, song_stats, music_path, get_local_audio, parse_list, top_play, Timer, is_compiled, rel_path, get_config, yt_playlist


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_channel = None
        self.queue = []
        self.playing = False
        self.ctx = None
        self.current = None
        self.timer = Timer()
        self.yt_blame = True
        os.makedirs(get_config().directory,exist_ok=True)
        if is_compiled() and not os.path.exists(rel_path('cache')):
            os.makedirs(rel_path('cache'))

        os.makedirs(rel_path("db"),exist_ok=True)
        if not os.path.isfile(rel_path(f"db{os.sep}music_stats.json")):
            with open(rel_path(f"db{os.sep}music_stats.json"), "x", encoding="utf-8") as file:
                json.dump({"data":[]}, file, indent=2, ensure_ascii=False)


    async def run_sc_download(self, url):
        loop = asyncio.get_running_loop()
        with ProcessPoolExecutor() as pool:
            songs = await loop.run_in_executor(pool, download_soundloud, url)
        return songs
    
    async def run_yt_playlist(self, url):
        loop = asyncio.get_running_loop()
        with ProcessPoolExecutor() as pool:
            title, urls = await loop.run_in_executor(pool, yt_playlist, url)
        return title, urls
    
    async def run_yt_download(self, url):
        loop = asyncio.get_running_loop()
        with ProcessPoolExecutor() as pool:
            vid = await loop.run_in_executor(pool, download_yt_video, url)
        return vid

    async def run_search_yt(self, term):
        loop = asyncio.get_running_loop()
        with ProcessPoolExecutor as pool:
            url = await loop.run_in_executor(pool, search_youtube, term)
        return url

    @commands.command(pass_context = True)
    async def play(self, ctx, *args):
        can_play = await self.ensure_voice(ctx)
        if(not can_play):
            return

        has_attachment = False
        try:
            has_attachment = True if len(ctx.message.attachments) > 0 else False
        except Exception as e:
            print(e)
            pass
        if(len(args) == 0 and not has_attachment):
            await ctx.send("Link <a:a52updates:1122163070815449160>")
            return
        
        res = []
        # handle toplist
        if(has_attachment):
            attach = ctx.message.attachments[0]
            if(not attach.filename.endswith(".mp3")):
                await ctx.send("Only .mp3 files accepted.")
                return
            #file = await attach.read()
            file_type, _ = mimetypes.guess_type(attach.filename)
            if file_type != "audio/mpeg":
                await ctx.send("Only .mp3 audio files accepted.")
                return
            
            name = sanitize_filename(attach.filename)
            res = requests.get(attach.url, stream=True)
            if(res.status_code == 200):
                with open(music_path(name)+".mp3","wb") as d_file:
                    for chunk in res.iter_content(8192):
                        if chunk:
                            d_file.write(chunk)

            self.queue.append(name)
            await ctx.send(f'Queued {name}')
            self.ctx = ctx
            if(not self.playing):
                self.playing = True
                await self.play_song(ctx)  
            return

        if(args[0] == "toplist"):
            count = 50
            try:
                count = int(args[1])
                assert count > 0
            except:
                pass
            pl = top_play(count)
            random.shuffle(pl)
            res = pl

        # check if file is downloaded
        if(len(res) == 0):
            res = get_local_audio(" ".join(args))

        # check if yt, soundcloud, yt playlist, or search term
        if(len(res) == 0):
            term = " ".join(args)
            if "soundcloud.com" in term:
                res = await self.run_sc_download(term)
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

            elif "youtube.com" in term or "youtu.be" in term:
                if(self.yt_blame):
                    self.yt_blame = False
                    await ctx.send("Youtube links take a few minutes to parse. Blame YouTube, not me.")
                urls = []
                if("&list" in term):
                    #title, urls = await self.run_yt_playlist_info(term)
                    #await ctx.send(f"Processed playlist {title}. Downloading songs...")
                    await ctx.send(f"Processing playlist...")
                    title, urls = await self.run_yt_playlist(term)
                    await ctx.send(f"Downloading playlist '{title}'")
                else:
                    urls = [term]
                print(urls)
                for url in urls:
                    vid = await self.run_yt_download(url)
                    await ctx.send(f"Downloaded {vid}.")
                    self.queue.append(vid)
                    await ctx.send(f'Queued {vid}.')
                    self.ctx = ctx
                    if(not self.playing):
                        self.playing = True
                        await self.play_song(ctx)
            else:
                await ctx.send("yt search terms not implemented yet. Stay tuned.")

                #run_search_yt

                # search
                pass
        else:
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



    async def play_song(self,ctx):
        song = ""
        if(len(self.queue) > 0):
            song = self.queue[0]
            can_play = await self.ensure_voice(ctx)
            if(not can_play):
                return
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


    def clear_songs(self,passed_ctx):
        # ctx = passed_ctx or self.ctx
        if(self.voice_channel):
            self.voice_channel.stop()
        self.current = None
        self.queue = []
        self.ctx = None
        self.playing = False


    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                self.voice_channel = await ctx.author.voice.channel.connect()
                self.clear_songs(ctx)
            else:
                await ctx.send("You are not in a voice channel! <:madge:1009748173717250098>")
                self.clear_songs(ctx)
                return False
                #raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            pass
        return True

    async def leave(self, ctx):
        # if await self.user_is_connected(ctx) and self.voice_channel.is_connected():
        try:
            await ctx.send("<a:kekbye:1264754885182754998> I'm outta this joint")
            self.clear_songs(ctx)
            await self.voice_channel.disconnect()
            self.voice_channel = None
            self.yt_blame = False
        except:
            print("error leaving kekl")
            pass

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
        if(self.current != None):
            cloned.insert(0,self.current)
        for i in range(0, count-1):
            skipped = self.queue.pop(0)
            song_stats(skipped + ".mp3","skipped")

        if await self.user_is_connected(ctx) and self.voice_channel and self.voice_channel.is_connected() and self.playing:
            msg = f'Skipped {", ".join(cloned[0:count])}'
            msg += "\nYou better not have skipped gachi <:fatmald:677160470875996171>"
            await ctx.send(msg)
            song_stats(self.current + ".mp3","skipped")
            self.voice_channel.stop()
        else:
            print("No skip?")
            print(self.current)
            print(self.queue)
            print(self.playing)
            print(await self.user_is_connected(ctx))
            if(self.voice_channel):
                print(self.voice_channel.is_connected())
            await ctx.send("Unable to skip <:admiralb:888877774964682772>")

    
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
        top = parse_list(args, key="skipped")
        for chunk in top:
            await ctx.send(f'```{chunk}```')
     
        


async def setup(bot):
    await bot.add_cog(Music(bot))

