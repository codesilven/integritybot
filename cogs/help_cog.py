#!/usr/bin/env python3

from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def help(self, ctx):
        message = ("```List of commands:\n"
                   "\n"
                   ",player [name] - Insults, quotes or both about a player.\n"
                   ",arpen_calc [old] [new] [percent=0] [flat=0] - Shows the efficacy of armor penetration going from old to new with percent reduction applied and a flat amount, for example 'arpen_calc 10 20 20 200'\n"
                   ",crit_calc [old] [new] [old_multiplier=200] [new_multiplier=200] - Show the efficacy of critical strike going from old to new value with optional critical strike mods, for example 'crit_calc 25 30 200 220'\n"
                   ",power - Explains how much value AP/SP has for specs. Use v or verbose for extended information, omit it for TL;DR.\n"
                   ",crit - Explains why crit stacking isn't what you think. Use v or verbose for extended information, omit it for TL;DR.\n"
                   ",play [link or title] - Plays a song. Accepts YouTube links/playlists and SoundCloud links/playlists. If a link is not provided, it will search YouTube. If the argument 'toplist' is passed, play top 50 songs in random order.\n"
                   ",skip [nothing or count] - Skips n songs, defaults to 1.\n"
                   ",queue - Shows the current queue.\n"
                   ",shuffle - Shuffles the queue.\n"
                   ",toplist - Lists tops songs played by us.\n"
                   ",stinkers - Lists the most skipped songs.\n"
                   ",help - List the available commands.\n```")
        await ctx.send(message)
    
async def setup(bot):
    await bot.add_cog(Help(bot))
