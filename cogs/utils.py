import configparser
import json
import os
import re
import sys
from fuzzywuzzy import fuzz
from pytubefix import YouTube, Playlist, Search
from pytubefix.exceptions import VideoUnavailable
from http.client import IncompleteRead
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
    use_auth = get_config().auth
    videos_search = Search(term, use_oauth=use_auth, allow_oauth_cache=use_auth,token_file=rel_path(f"cache{os.sep}tokens.json") if (is_compiled() and use_auth) else None)
    match = None
    max_ratio = 0
    if len(videos_search > 0):
        for res in videos_search:
            t_term = re.sub(r'[^a-zA-Z0-9]', '', term).lower()
            t_title = re.sub(r'[^a-zA-Z0-9]', '', res.title).lower()
            ratio = fuzz.ratio(t_term,t_title)
            if(ratio > max_ratio):
                match = res
                max_ratio = ratio

        video_url = match.watch_url
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



def download_soundloud(url):
    results = []
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
    return results


def yt_playlist(url):
    pl = Playlist(url)
    return pl.title, [video.watch_url for video in pl.videos]

def test_progress (stream, chunk, bytes_remaining, message_update):
    filesize = stream.filesize
    bytes_received = filesize - bytes_remaining
    percent = round(100.0 * bytes_received / float(filesize), 1)
    message_update(percent)
    on_progress(stream, chunk, bytes_remaining)

def download_yt_video(url):
    use_auth = get_config().auth
    yt = YouTube(url, on_progress_callback = on_progress, use_oauth=use_auth, allow_oauth_cache=use_auth, token_file=rel_path(f"cache{os.sep}tokens.json") if (is_compiled() and use_auth) else None)
    fn = sanitize_filename(yt.title)
    retry = True
    retry_count = 10

    if not os.path.isfile(music_path(fn) + ".mp3"):
        while retry:
            retry = False
            ys = None
            try:
                ys = yt.streams.get_audio_only()
            except VideoUnavailable:
                print("Video unvailable, retrying")
                retry = True
                pass
            except Exception as e:
                print("error?")
                print(e)
                pass
            if(ys):
                try:
                    ys.download(output_path=music_path(), filename=fn +".mp3") # pass the parameter mp3=True to save in .mp3
                except IncompleteRead:
                    print("Incomplete read, retrying")
                    retry = True
                    pass

            if(retry and retry_count == 0):
                retry = False
            else:
                retry_count -= 1
    return fn

def get_local_audio(term):
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
    return []
    #return download(term,func,loop,callback)


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
        print(weekday, raid_days)
        if(weekday >= raid_days[-1] or weekday < raid_days[0]):
            next_day = raid_days[0]
        day_diff = next_day-weekday
        if(day_diff <= 0):
            day_diff = 7+day_diff
        print("day_diff: ",day_diff)

        t = d.total_seconds() + day_diff * 24 * 3600
        print(f"2 raid messaging in {t}")
        return t