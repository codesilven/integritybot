import configparser
import json
import os
import re
import sys
from youtubesearchpython import VideosSearch
from fuzzywuzzy import fuzz
from pytubefix import YouTube
from pytubefix import Playlist
from pytubefix.cli import on_progress
import os.path
from sclib import SoundcloudAPI
import validators
import asyncio
from datetime import datetime, time


GLOBAL_CONFIG = None

class Config:
    def __init__(self, path = ""):
        raw_dict = None
        config_object = configparser.ConfigParser()
        try:
            with open(path,"r") as file:
                config_object.read_file(file)
                output_dict={s:dict(config_object.items(s)) for s in config_object.sections()}
                raw_dict = output_dict
        except Exception as e:
            print(e)
            if not os.path.isfile(path):
                with open(path,"x") as file:
                    std = "[admin]\n"
                    std += "# get bot token from the developer console\n"
                    std += "token =\n"
                    std += "# what to prefix commands with. Leave empty for ',' (a comma)\n"
                    std += "prefix =\n"
                    std += "# if YouTube authentication should be attempted. 1 for yes, 0 for no. Refer to readme for more information\n"
                    std += "auth = 1\n"
                    std += "# where music files should be stored. Leave empty for '/music' relative to the install\n"
                    std += "directory =\n"
                    std += "# comma delimited ids from discord users who can add data\n"
                    std += "superusers =\n"
                    std += "[cogs]\n"
                    std += "help = 1\n"
                    std += "music = 1\n"
                    std += "wow = 0\n"
                    file.write(std)
                with open(path,"r") as file:
                    config_object.read_file(file)
                    output_dict={s:dict(config_object.items(s)) for s in config_object.sections()}
                    raw_dict = output_dict         
        admin = raw_dict["admin"] 
        self.token = admin["token"].strip()
        self.prefix = ","
        self.auth = False
        try:
            self.auth = (admin["auth"].strip() == "1")
        except:
            pass

        self.directory = clean_path(admin["directory"] or f"music")
        if(not os.path.isabs(self.directory)):
            self.directory = top_path() + os.sep + self.directory

        try:
            pfx = admin["prefix"].strip()
            assert len(pfx) > 0
            self.prefix = pfx
        except:
            pass
        self.superusers = admin["superusers"].split(",")

        cogs = raw_dict["cogs"]
        self.help_cog = False
        self.music_cog = False
        self.wow_cog = False

        for cog in ["help","music","wow"]:
            try:
                value = int(cogs[cog].strip())
                setattr(self,cog+"_cog", int(cogs[cog].strip()) == 1)
            except Exception as e:
                print(f"Cog setting '{cog}' of value '{cogs[cog]}' invalid")
                print("Exception was ",e)


def set_config(path = ""):
    global GLOBAL_CONFIG
    GLOBAL_CONFIG = Config(path)

def get_config():
    global GLOBAL_CONFIG
    return GLOBAL_CONFIG


def is_compiled():
    return not "python.exe" in sys.executable
def clean_path(path):
    normalized_path = os.path.normpath(path)
    cleaned_path = normalized_path.strip(os.path.sep)
    
    return cleaned_path

def top_path():
    if (is_compiled()):
        return os.sep.join(sys.executable.split("\\")[:-1])
    else:
        return os.path.dirname(__file__)

def rel_path(p = ""):
    return top_path() + os.sep + p



api = SoundcloudAPI()


def search_youtube(term):
    videos_search = VideosSearch(term, limit=100, language="en",region="US")
    results = videos_search.result()
    match = None
    max_ratio = 0
    if results['result']:
        for res in results["result"]:
            t_term = re.sub(r'[^a-zA-Z0-9]', '', term).lower()
            t_title = re.sub(r'[^a-zA-Z0-9]', '', res["accessibility"]["title"]).lower()
            ratio = fuzz.ratio(t_term,t_title)
            if(ratio > max_ratio):
                match = res
                max_ratio = ratio

        video_url = match['link']
        return video_url
    else:
        return None

def song_stats(song, key = "plays"):
    print(song,key)
    data = None
    with open(rel_path(f"db{os.sep}music_stats.json"), encoding="utf-8") as db:
        data = json.load(db)["data"]
        relevant_song = list(filter(lambda x: x["song"] == song, data))
        if(len(relevant_song) > 0):
            relevant_song[0][key]+= 1
        elif(len(relevant_song) == 0):
            new_song = {
                "song": song,
                "plays": 1,
                "skipped": 0,
                "info": {}
                }
            data.append(new_song)
    with open(rel_path(f"db{os.sep}music_stats.json"), "w", encoding="utf-8") as file:
        json.dump({"data":data}, file, indent=2, ensure_ascii=False)   
        pass

def music_path(song=""):
    path = get_config().directory
    return path + os.sep + song

def sanitize_filename(filename):
    # Replace invalid characters with an underscore
    return re.sub(r'[<>:"/\\|?*]', '_', filename)



async def async_download(videos,func,callback):
    results = []
    for video in videos:
        if not os.path.isfile(music_path(video.title) + ".mp3"):
            ys = video.streams.get_audio_only()
            ys.download(mp3=True,output_path=music_path(), filename=sanitize_filename(video.title)) # pass the parameter mp3=True to save in .mp3
        if(callback and callable(callback)):
            if asyncio.iscoroutinefunction(callback):
                await callback(video.title)
            else:
                callback(video.title)
        print(f"async downloaded {video.title}")
        results.append(sanitize_filename(video.title))
    #await asyncio.sleep(1)
    func(results)

def download(url, func=None, loop=None, callback=None):
    results = []
    if("youtube.com" in url or "youtu.be" in url):
        if("&list" in url):
            pl = Playlist(url)
            vids = []
            inc = 0
            for video in pl.videos:
                if(inc == 0):
                    if not os.path.isfile(music_path(video.title) + ".mp3"):
                        print("download " +video.title)
                        ys = None
                        try:
                            ys = video.streams.get_audio_only()
                        except:
                            print("no download?")
                            pass
                        if(not ys):
                            return []
                        ys.download(mp3=True,output_path=music_path(),filename=sanitize_filename(video.title)) # pass the parameter mp3=True to save in .mp3
                    results.append(sanitize_filename(video.title))
                else:
                    vids.append(video)
                inc += 1

            if(func != None and loop!= None and len(vids) > 0):
                print(f"running async on {len(vids)} videos")
                loop.create_task(async_download(vids,func,callback))
        else:
            if is_compiled() and not os.path.exists(rel_path('cache')):
                os.makedirs(rel_path('cache'))
            use_auth = get_config().auth
            yt = YouTube(url, on_progress_callback = on_progress, use_oauth=use_auth, allow_oauth_cache=use_auth, token_file=rel_path(f"cache{os.sep}tokens.json") if (is_compiled() and use_auth) else None)
            print(yt.title)
            if not os.path.isfile(music_path(yt.title) + ".mp3"):
                ys = None
                try:
                    ys = yt.streams.get_audio_only()
                except Exception as e:
                    print("error?")
                    print(e)
                    pass
                if(not ys):
                    return []
                ys.download(mp3=True,output_path=music_path(), filename=sanitize_filename(yt.title)) # pass the parameter mp3=True to save in .mp3
            results.append(sanitize_filename(yt.title))
    elif("soundcloud.com" in url):
        if("/sets/" in url):
            playlist = api.resolve(url)
            for track in playlist.tracks:
                filename = music_path(track.title)+".mp3"
                with open(filename, 'wb+') as file:
                    track.write_mp3_to(file)
                results.append(track.title)
        else:
            track = api.resolve(url)
            filename = music_path(track.title)+".mp3"
            with open(filename, 'wb+') as file:
                track.write_mp3_to(file)
            results.append(track.title)
    else:
        link = search_youtube(url)
        new_res = download(link,func,loop,callback)
        return new_res
    return results

def get_audio(term, func=None, loop=None, callback=None):
    match = None
    max_ratio = 0
    if(not validators.url(term)):
        for filename in os.listdir(music_path()):
            f = os.path.join(music_path(), filename)
            if os.path.isfile(f):
                title = None
                try:
                    title = f[len(music_path()):-4]
                except:
                    pass
                if(title):
                    t_term = re.sub(r'[^a-zA-Z0-9]', '', term).lower()
                    t_title = re.sub(r'[^a-zA-Z0-9]', '', title).lower()
                    if(t_term in t_title):
                        ratio = 100
                        match = title
                    else:
                        ratio = fuzz.ratio(t_term,t_title)
                    if(ratio > max_ratio):
                        max_ratio = ratio
                        match = title
        print(f'{max_ratio}% on {term}, found {match}')
        if(max_ratio >= 75):
            return [match]
    return download(term,func,loop,callback)




def top_list(key="plays",count=10):
    with open(rel_path(f"db{os.sep}music_stats.json"), encoding="utf-8") as db:
        data = json.load(db)["data"]
        relevant_song = list(sorted(data, key=lambda x: x[key] - (x["skipped"] if key=="plays" else 0),reverse=True))
        try:
            return relevant_song[:count]
        except:
            print("lmao error")
            return []
        
def top_play(song_count=50):
    res = top_list(key="plays",count=song_count)
    tl = [x["song"][:-4] for x in res]
    return tl

def parse_list(args, key="plays"):
    count = 10
    if(len(args) > 0):
        if(args[0] and args[0].isnumeric()):
            try:
                count = int(args[0])
            except:
                pass
    if(count < 1):
        count = 10
    res = top_list(key=key,count=count)
    #msg = ""
    count = 0

    chunks = [""]
    chunk_index = 0

    for song in res:
        msg = f'{count+1}. {song["song"][:-4]} ({song[key]})'
        if(count < len(res)-1):
            # print(count)
            # print(len(res))
            msg += "\n"
        if(len(chunks[chunk_index]) + len(msg) >= 2000):
            chunk_index +=1
            chunks.append("")
        chunks[chunk_index] += msg
    
        count += 1
    
    return chunks

class Timer:
    def __init__(self):
        self.task = None

    async def _run(self, delay, callback, *args, **kwargs):
        await asyncio.sleep(delay)
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
        except Exception as e:
            print(f"Timer exception: {e}")



    def start(self, delay, callback, *args, **kwargs):
        if self.task is not None:
            self.task.cancel()
        self.task = asyncio.create_task(self._run(delay, callback, *args, **kwargs))

    def cancel(self):
        if self.task is not None:
            self.task.cancel()
            self.task = None






def time_until_raid(raid_days,raid_time,raid_min = 0):
    now = datetime.now()
    weekday = now.weekday()
    clock = now.time()
    before_raid = clock <= time(raid_time,raid_min)

    d = datetime.combine(now,time(raid_time,raid_min))-datetime.combine(now,clock)

    if(weekday in raid_days and before_raid):
        #it's tue/thurs, check time
        print(f"1 raid messaging in {d.total_seconds()}")
        return d.total_seconds()
    else:
        # if it's not, check which is closest
        next_day = raid_days[1]
        if(weekday > raid_days[-1] or weekday < raid_days[0]):
            next_day = raid_days[0]
        day_diff = next_day-weekday

        t = d.total_seconds() + day_diff * 24 * 3600
        print(f"2 raid messaging in {t}")
        return t