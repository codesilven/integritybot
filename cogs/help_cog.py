#!/usr/bin/env python3

import random
from discord.ext import commands
from .utils import get_config

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def help(self, ctx):
        cfg = get_config()
        pfx = cfg.prefix
        music = cfg.music_cog
        wow = cfg.wow_cog

        message = "```List of commands:\n\n"
        if(wow):
            message +=(f"{pfx}player [name] - Insults, quotes or both about a player.\n"
                   f"{pfx}arpen_calc [old] [new] [percent=0] [flat=0] - Shows the efficacy of armor penetration going from old to new with percent reduction applied and a flat amount, for example 'arpen_calc 10 20 20 200'\n"
                   f"{pfx}crit_calc [old] [new] [old_multiplier=200] [new_multiplier=200] - Show the efficacy of critical strike going from old to new value with optional critical strike mods, for example 'crit_calc 25 30 200 220'\n"
                   f"{pfx}power - Explains how much value AP/SP has for specs. Use v or verbose for extended information, omit it for TL;DR.\n"
                   f"{pfx}crit - Explains why crit stacking isn't what you think. Use v or verbose for extended information, omit it for TL;DR.\n")
        if(music):
            message += (f"{pfx}play [link or title] - Plays a song. Accepts YouTube links/playlists and SoundCloud links/playlists. If a link is not provided, it will search YouTube. If the argument 'toplist' is passed, play top 50 songs in random order.\n"
                   f"{pfx}skip [nothing or count] - Skips n songs, defaults to 1.\n"
                   f"{pfx}queue - Shows the current queue.\n"
                   f"{pfx}shuffle - Shuffles the queue.\n"
                   f"{pfx}toplist - Lists tops songs played by us.\n"
                   f"{pfx}stinkers - Lists the most skipped songs.\n")

        message += f"{pfx}help - List the available commands.\n```"
        
        await ctx.send(message)


async def setup(bot):
    await bot.add_cog(Help(bot))
