#!/usr/bin/env python3

import json
from discord.ext import commands
from discord import File
import random
import os
import uuid
import requests
from .arpen import compare 
from .crit import compare_crit
from .utils import rel_path, get_config

list_of_people = ["Aurose","Apophysis","Zobimaru","Maeglin","Zouzou","Jimhoten","Giffels","Why","Hairguy","Dvagorine","Syrene","Narsu","Dienstranum",
                  "Fingerbone","Fireqz","Whirlyshots","Stallion","Goggins","Phones","Vasiria","Cruked","Khartoba","Zakm","Ladiev","Lavjuu","Tristen",
                  "Tsufi","Criex","Furre","Leonor","Shiift","Snooz","Peeqz","Tlacaelel","Temptress","Senjougahara","Guanshiyin","Phibbe","Manaaddict",
                  "Izzyfizzy","Tubbie","Hashkandiqt","Zimber","Yunir"]
elv_messages = [
    "A great tip for ElvUI users is to uninstall ElvUI.","If you like ElvUI, may I recommed: Nickelback, Bud Light, Crocs, Internet Explorer",
    "90% of the bottom 1% worst players all use ElvUI.","The 'E' in ElvUI stand for 'extraneous', a word no ElvUI user has ever managed to spell.",
    "Here's a joke: 'ElvUI'", "You know why do ElvUI users always carry a manual? Because half the time they need a guide just to open their inventory.",
    "ElvUI: the face of r/wowuigore","Use ElvUI, the UI most war criminals use.","ElvUI more like BadUI amirite","Roses are red, violets are blue, your gf said goodbye, because you use ElvUI",
    "ElvUI is a lot like math - I hate math","My gf said she upgraded her UI to ElvUI. I said I upgraded to a new gf."
]




def mask(name):
    if name == "surely":
        return "sorely"
    if name == "raelvion":
        return "rael"
    if name == "fujoshi":
        return "aramis"
    return name

def is_uuid(uuid_to_test, version=4):
    try:
        # check for validity of Uuid
        uuid_obj = uuid.UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return True


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.superusers = get_config().superusers
        
        self.db_path = rel_path("db/player.json")
        os.makedirs(rel_path("db"),exist_ok=True)
        mode = "r"
        if not os.path.isfile(self.db_path):
            mode = "x"

        with open(self.db_path, mode, encoding="utf-8") as db:
            data = None
            try:
                data = json.load(db)["data"]
            except:
                pass

            if(data):
                for player in data:
                    p_name = player["player"]
                    for msg in player["data"]:
                        if(not "id" in msg):
                            msg["id"] = str(uuid.uuid4())
                        if(not "type" in msg or not "value" in msg):
                            player["data"].remove(msg)
            
            self.data = data or []
        with open(self.db_path, "w", encoding="utf-8") as file:
            json.dump({"data":self.data}, file, indent=2, ensure_ascii=False)   
        random.seed()
        self.messages = []

        
    
    def msg_by_id(self,id):
        all_msg = list(map(lambda x: x["data"], self.data))
        msg = list(filter(lambda x: x["id"] == id, [item for sub_list in all_msg for item in sub_list]))
        if(len(msg) > 0):
            return msg[0]
        return False
    
    async def send(self,ctx,res):
        if(res["type"] == "file"):
            with open(rel_path(res["value"]),"rb") as f:
                pic = File(f)
                await ctx.send(file=pic)
        elif(res["type"] == "text"):
            await ctx.send(res["value"])
        self.messages.insert(0,res)


    @commands.command(pass_context=True)
    async def last_message(self,ctx, *args):
        if(not str(ctx.message.author.id) in self.superusers):
            await ctx.send("Not allowed :no_entry:")
            return
        if(len(self.messages) == 0):
            await ctx.send("No messages sent so far!")
            return
        index = 0
        if(len(args) > 0):
            if(args[0] and args[0].isnumeric()):
                try:
                    index = int(args[0])
                    self.messages[index]
                except:
                    pass
        await ctx.send(f'ID: {self.messages[index]["id"]}\nValue: {self.messages[index]["value"]}')

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
    
    @commands.command(pass_context=True)
    async def power(self,ctx,*args):
        verbose = False
        if(len(args) > 0):
            if(args[0] == "v" or args[0] == "verbose" or args[0] == "-v"):
                verbose = True
        
        msg = "```Attack power and spell power are not convertible to %dmg or other scalar mods like critical strike or haste.\nWhoever tries to explain it this way is wrong and they should reconsider their approach.\n"
        msg += "All abilities have a base damage 'B', a coefficient 'c', and the attack/spell power 'P'. Therefore ability damage can be expressed as B + P*c.\n"
        msg += "We will only ever calculate after the effect of things like Deadliness, Trueshot Aura, Demonic Pact or Intellect main stat.\n"
        msg += "1% damage can be expressed as (B + P*c)*1.01, or B*1.01 + P*c*1.01.\n"
        msg += "1% power can be expressed as B + P*c*1.01, from which we can deduce that gaining 1% total power is ALWAYS worse than gaining 1% dmg.\n"

        msg += "Therefore, unless your total power is increased by more than 1% (for example from 3000 spell power to 3045), it will NEVER be better than 1% dmg.\n"
        if(not verbose):
            msg += "TL;DR you need ~1.8% increase in SP or ~1.6% AP to gain 1% dmg. The relative % goes down and the absolute number (ie 35 -> 50) goes up as you gain those stats."
            msg += "Not deep enough? Add v or verbose after ,power to get a further explanation."

        msg += "```"
        await ctx.send(msg)
        if(not verbose):
            return

        if(verbose):
            msg = "```The exact percentage of power increase needed depends on which ability in question. So let's provide examples:\n"
            msg += "#1. Frostbolt (rank 14) has average base damage 1509 and 0.58 spell power coefficient. With 3000 spell power, the Frostbolt will deal 1509 + 0.58 * 3000 = 3249 damage.\n"
            msg += "Since 1% of 3249 is 32.5, you would need 1/0.58 * 32.5 = ~55 spell power to deal that 32.5 extra damage. In this case, a 1.8% spell power increase is needed to hit 1% damage.\n\n"
            msg += "#2. Bloodthirst has no base damage and scales with 55% of attack power. Therefore, 1% AP and 1% dmg are equal in scaling Bloodthirst.\n\n"
            msg += "#3. Overpower does 120% normalized weapon damage. This means it does base weapon damage (the value shown when hovering the item) plus AP/14 * 3.3. Add them together and multiply by 1.2 for final result.\n\n"
            msg += "Reaver of the Infinites M30 has 504 average weapon damage. With 3000 AP, that adds 3000/14 * 3.3 = 707.14 damage.\n"
            msg += "Since 1% of 1211 is 12, we would need 1/0.2357 * 12 = 51 attack power to deal that 12 extra damage. In this case, a 1.7% attack power increase is needed to hit 1% damage.\n\n```"
            await ctx.send(msg)

            msg = "```The astute among you might have noticed the lack of Ascension's wonderful hybrid scaling in the formulas. There's two parts to that - the first is that for non-hybrids, where your lesser power remains more or less static, "
            msg += "it is essentially additional base damage which further tilts the ratio, making your primary power even less effective compare to %dmg.\n"
            msg += "The second is the case of actual hybrids, in which case your powers are more evenly distributed. In this case, the previous example's magnitude is amplified to insanity, making hybrid builds EVEN WORSE at utilizing talents"
            msg += " like Deadliness.\nA common misconception beyond this is that the coefficient in question matters. It really doesn't, as it only changes the initial ratio of base damage to power - the ratio between 1% power and 1% dmg remains.\n"
            msg += "Finally this leads us to the last step - power has diminshing returns compared to % dmg. If 100 SP grants 10 dps, next 100 SP will also add 10 dps, but that 10 dps is now a lower percentage of overall damage. Therefore the "
            msg += "'stacking spell power' strategy is almost always a dps loss compared to taking scalar talents. Going back to the Frostbolt example, with 6000 SP instead, you would need 86 SP rather than 55 to gain 1% dmg. Notice that this means the "
            msg += "percentage of spell power needed actually DECREASES from 1.8% to 1.4%, but absolute number increases - this is because the base damage becomes less relevant as its share decreases, in essence trending towards Bloodthirst."
            msg += "```"
            await ctx.send(msg)

    @commands.command(pass_context=True)
    async def crit(self,ctx,*args):
        verbose = False
        if(len(args) > 0):
            if(args[0] == "v" or args[0] == "verbose" or args[0] == "-v"):
                verbose = True
        
        msg = "```Critical strike chance gives a chance to do 200% damage with melee and ranged abilities or 175% damage with spells.\n"
        msg += "These values can further be increase by agility main stat allocation, Poleaxe Specialization, Impale, or spell crit damage talent capstones like Shadow Power."
        msg += "This makes critical strike an output stat, in the same vein as attack power or haste. However, unlike attack power, critical strike damage is also a mechnical stat for specs like Hot Hands."
        msg += "All abilities have a base damage 'B', a coefficient 'c', and the attack/spell power 'P'. Therefore ability damage can be expressed as B + P*c.\n"

        if(not verbose):
            msg += "TL;DR the 0->1% crit is 1% damage and the 99%->100% is  ."
            msg += "Not deep enough? Add v or verbose after ,power to get a further explanation."

        msg += "```"
        await ctx.send(msg)
        if(not verbose):
            return

        if(verbose):
            msg = "```The exact percentage of power increase needed depends on which ability in question. So let's provide examples:\n"
            msg += "```"
            await ctx.send(msg)

            msg = "```The astute among you might have noticed the lack of Ascension's wonderful hybrid scaling in the formulas. There's two parts to that - the first is that for non-hybrids, where your lesser power remains more or less static, "
            msg += "```"
            await ctx.send(msg)

    @commands.command(pass_context=True)
    async def add(self,ctx, *args):
        if(not str(ctx.message.author.id) in self.superusers):
            await ctx.send("Not allowed :no_entry:")
            return
        
        player_to_add = None
        try:
            player_to_add = str(args[0]).lower()
        except:
            pass

        attachment = None
        if(player_to_add and ctx.message.attachments):
            attach = ctx.message.attachments[0]
            res = requests.get(attach.url, stream=True)
            # create folder if not existing
            os.makedirs(rel_path("assets"),exist_ok=True)

            if(res.status_code == 200):
                with open(rel_path("assets" + os.sep + attach.filename),"wb") as file:
                    for chunk in res.iter_content(8192):
                        if chunk:
                            file.write(chunk)
                attachment = "assets" + os.sep + attach.filename

        message = None
        try:
            message = (" ".join(args[1:]))
        except:
            pass

        if(player_to_add and (message or attachment)):
            with open(self.db_path, encoding="utf-8") as db:
                data = json.load(db)["data"]
                relevant_player = list(filter(lambda x: x["player"] == player_to_add, data))
                if(len(relevant_player) > 0):
                    relevant_player[0]["data"].append({
                        "type": "file" if attachment else "text",
                        "value": attachment if attachment else message,
                        "id": str(uuid.uuid4())
                    })
                elif(len(relevant_player) == 0):
                    player = {
                        "player": player_to_add,
                        "data": [{
                            "type": "file" if attachment else "text",
                            "value": attachment if attachment else message,
                            "id":str(uuid.uuid4())
                        }]
                    }
                    data.append(player)

                self.data = data
            with open(self.db_path, "w", encoding="utf-8") as file:
                json.dump({"data":self.data}, file, indent=2, ensure_ascii=False)       

    @commands.command(pass_context=True)
    async def delete(self,ctx,*args):
        if(not str(ctx.message.author.id) in self.superusers):
            await ctx.send("Not allowed :no_entry:")
            return
        # first is name
        player_to_remove = None
        id = None
        try:
            player_to_remove = str(args[0]).lower()
            id = args[1]
        except:
            pass

        if(player_to_remove and id and is_uuid(id)):
            with open(self.db_path, encoding="utf-8") as db:
                data = json.load(db)["data"]
                relevant_player = list(filter(lambda x: x["player"] == player_to_remove, data))
                if(relevant_player and len(relevant_player) > 0):
                    relevant_player[0]["data"] = list(filter(lambda x: x["id"] != id, relevant_player[0]["data"]))
                    self.data = data
            with open(self.db_path, "w", encoding="utf-8") as file:
                json.dump({"data":self.data}, file, indent=2, ensure_ascii=False) 



    @commands.command(pass_context=True)
    async def player(self, ctx, arg = None):
        if not arg or not isinstance(arg, str):
            await ctx.send("You didn't provide a player name you absolute donkey (or Aramis didn't implement it yet <:kekw:677506629910134815>)")
            return
        
        if(is_uuid(arg)):
            id_msg = self.msg_by_id(arg)
            if(id_msg):
                await self.send(ctx,id_msg)
                return 
            else:
                await ctx.send("You provided a UUID, but the UUID doesn't correspond to any message <:admiralb:888877774964682772>")
                return

            
        res = None
        try:
            name = mask(arg.lower())
            res = random.choice(list(filter(lambda x: x["player"] == name, self.data))[0]["data"])
        except:
            pass

        if(res):
            await self.send(ctx,res)
            return
        
        await ctx.send("You didn't provide a player name you absolute donkey (or Aramis didn't implement it yet <:kekw:677506629910134815>)")
        return

    @commands.command(pass_context=True)
    async def peperain(self, ctx):
        list_of_people.sort()
        await ctx.send("<a:PepeRain:1260290816874909797>".join(list_of_people) + "<a:PepeRain:1260290816874909797>")

    @commands.command(pass_context=True)
    async def elvui(self, ctx):
        await ctx.send(random.choice(elv_messages))

    @commands.command(pass_context=True)
    async def arpen_calc(self, ctx, *args):
        # args is old, new, %pen, -flat
        go_ahead = False
        (old,new,pen,flat) = 0,0,0,0
        try:
            (old,new) = args
            old = float(old)
            new = float(new)
            go_ahead = True
        except ValueError:
            pass

        try:
            (old,new,pen) = args
            old = float(old)
            new = float(new)
            pen = float(pen)
            go_ahead = True
        except ValueError:
            pass
        try:
            (old,new,pen,flat) = args
            old = float(old)
            new = float(new)
            pen = float(pen)
            flat = int(flat)
            go_ahead = True
        except ValueError:
            pass

        if(not go_ahead):
            await ctx.send("Invalid syntax - first two arguments must be integer or float, representing armor pen before/after comparison, such as ,arpen_calc 10 20 for 10% and 20%.\nStop pretending. <:weirdchamp:677517236692320256>")
            return
        await ctx.send(compare(old,new,pen,flat))    


    @commands.command(pass_context=True)
    async def crit_calc(self, ctx, *args):
        # args is old, new, %pen, -flat
        go_ahead = False
        (old,new,old_mult,new_mult) = 0,0,200,200
        try:
            (old,new) = args
            old = float(old)
            new = float(new)
            go_ahead = True
        except ValueError:
            pass

        try:
            (old,new,old_mult) = args
            old = float(old)
            new = float(new)
            old_mult = float(old_mult)
            go_ahead = True
        except ValueError:
            pass
        try:
            (old,new,old_mult,new_mult) = args
            old = float(old)
            new = float(new)
            old_mult = float(old_mult)
            new_mult = int(new_mult)
            go_ahead = True
        except ValueError:
            pass

        if(not go_ahead):
            await ctx.send("Invalid syntax - first two arguments must be integer or float, representing crit chance before/after comparison, such as ,crit_calc 10 20 for 10% and 20%.\nStop pretending. <:weirdchamp:677517236692320256>")
            return
        await ctx.send(compare_crit(old,new,old_mult,new_mult))    


async def setup(bot):
    await bot.add_cog(Help(bot))
