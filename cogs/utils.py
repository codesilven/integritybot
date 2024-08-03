import json
import os
import re
from youtubesearchpython import VideosSearch
from fuzzywuzzy import fuzz
from pytubefix import YouTube
from pytubefix import Playlist
from pytubefix.cli import on_progress
import os.path
from sclib import SoundcloudAPI, Track, Playlist as SCPlaylist
import validators
import asyncio


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
    with open(os.path.join(os.path.dirname(__file__),"db/music_stats.json"), encoding="utf-8") as db:
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
    with open(os.path.join(os.path.dirname(__file__),"db/music_stats.json"), "w", encoding="utf-8") as file:
        json.dump({"data":data}, file, indent=2, ensure_ascii=False)   
        pass

def music_path(song=""):
    return "E:\\ig_music\\" + song
    # E:\ig_music





async def async_download(videos,func):
    results = []
    for video in videos:
        if not os.path.isfile(music_path(video.title) + ".mp3"):
            ys = video.streams.get_audio_only()
            ys.download(mp3=True,output_path=music_path()) # pass the parameter mp3=True to save in .mp3
        print(f"async downloaded {video.title}")
        results.append(video.title)
    #await asyncio.sleep(1)
    func(results)

def download(url, func=None, loop=None):
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
                        ys.download(mp3=True,output_path=music_path()) # pass the parameter mp3=True to save in .mp3
                    results.append(video.title)
                else:
                    vids.append(video)
                inc += 1

            if(func != None and loop!= None and len(vids) > 0):
                print(f"running async on {len(vids)} videos")

                loop.create_task(async_download(vids,func))
                #asyncio.run(async_download(vids,func))
                # coro = async_test(vids,func)
                # fut = asyncio.run_coroutine_threadsafe(coro, loop)
                # try:
                #     print("fut.result")
                #     fut.result(10)
                # except:
                #     print("fail")
                #     pass
        else:
            yt = YouTube(url, on_progress_callback = on_progress, use_oauth=True, allow_oauth_cache=True)
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
                ys.download(mp3=True,output_path=music_path()) # pass the parameter mp3=True to save in .mp3
            results.append(yt.title)
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
        new_res = download(link,func,loop)
        return new_res
    return results

def get_audio(term, func=None, loop=None):
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
    return download(term,func,loop)




def top_list(key="plays",count=10):
    with open(os.path.join(os.path.dirname(__file__),"db/music_stats.json"), encoding="utf-8") as db:
        data = json.load(db)["data"]
        relevant_song = list(sorted(data, key=lambda x: x[key],reverse=True))
        try:
            return relevant_song[:count]
        except:
            print("lmao error")
            return []
        
def top_play():
    res = top_list(key="plays",count=50)
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
        if asyncio.iscoroutinefunction(callback):
            await callback(*args, **kwargs)
        else:
            callback(*args, **kwargs)

    def start(self, delay, callback, *args, **kwargs):
        if self.task is not None:
            self.task.cancel()
        self.task = asyncio.create_task(self._run(delay, callback, *args, **kwargs))

    def cancel(self):
        if self.task is not None:
            self.task.cancel()
            self.task = None
