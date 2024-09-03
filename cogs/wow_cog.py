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
from .utils import rel_path, get_config, Timer, time_until_raid




def mask(name,source):
    try:
        if(name in source):
            return(source[name])
        return name
    except Exception as e:
        print(e)
        return name


def is_uuid(uuid_to_test, version=4):
    try:
        # check for validity of Uuid
        uuid_obj = uuid.UUID(uuid_to_test, version=version)
    except ValueError:
        return False
    return True


class WoW(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.superusers = get_config().superusers
        self.player_messages = {}

        #create player.json
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

        #seed and prepare message log
        random.seed()
        self.messages = []

        #create opts.json
        self.opt_path = rel_path("db/opts.json")
        mode = "r"
        if not os.path.isfile(self.opt_path):
            mode = "x"

        with open(self.opt_path, mode, encoding="utf-8") as db:
            data = None
            try:
                data = json.load(db)["data"]
            except:
                pass
            self.opts = data or {
                "raid_channel_id": "",
                "raid_role_id": "",
                "elv_messages": [],
                "list_of_people": [],
                "mask": []
            }
        with open(self.opt_path, "w", encoding="utf-8") as file:
            json.dump({"data":self.opts}, file, indent=2, ensure_ascii=False)


        #start timer

        self.raid_days = [1,3]
        self.raid_hour = 19
        self.raid_min = 0

        lapse = time_until_raid(self.raid_days,self.raid_hour,self.raid_min)
        self.timer = Timer()
        self.timer.start(lapse, self.raid_message)

    def ensure_message(self,name):
        if(not name in self.player_messages):
            messages = list(filter(lambda x: x["player"] == name, self.data))[0]["data"]
            random.shuffle(messages)
            d = {
                "messages": messages,
                "index": 0,
                "last_message_id": None
            }
            self.player_messages[name] = d

    async def raid_message(self):
        if(not "raid_channel_id" in self.opts):
            print("Error: no raid channel id.")
            return
        channel = self.bot.get_channel(self.opts["raid_channel_id"])
        if(not channel):
            print("Error: incorrect id to channel match.")
            return

        msg = "<a:gachihyper:1267510456571134054>".join(list("You know what day it is? It is RAID DAY".replace(" ","").upper()))

        if(not "raid_role_id" in self.opts):
            print("Error: no role id to tag! Sending message without tag.")
        else:
            msg += f"\n<@&{self.opts["raid_role_id"]}>"
        await channel.send(msg)
        lapse = time_until_raid(self.raid_days,self.raid_hour,self.raid_min)
        self.timer.start(lapse, self.raid_message)


    @commands.command(pass_context=True)
    async def set_raid_channel(self,ctx):
        print(ctx.channel.id)
        self.opts["raid_channel_id"] = ctx.channel.id
        with open(self.opt_path, "w", encoding="utf-8") as file:
            json.dump({"data":self.opts}, file, indent=2, ensure_ascii=False)
        await ctx.send(f"Set raid channel to {ctx.channel} (id {ctx.channel.id})")
        
    @commands.command(pass_context=True)
    async def set_raid_role(self,ctx,*args):
        id = None
        if(args and args[0] and args[0].startswith("<@&")):
            id = args[0][3:-1]
        
        if( not id ):
            await ctx.send(f"Invalid role or call. Use '{get_config().prefix}set_raid_role @role' to enter a role.")
            return
        
        self.opts["raid_role_id"] = id
        with open(self.opt_path, "w", encoding="utf-8") as file:
            json.dump({"data":self.opts}, file, indent=2, ensure_ascii=False)

        await ctx.send("Successfully set role to tag <:pingsock:705824142154268792>.")
        

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
            msg += "TL;DR you need ~1.8% increase in SP or ~1.6% AP to gain 1% dmg. The relative % goes down and the absolute number (ie 35 -> 50) goes up as you gain those stats.\n"
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
        msg += "These values can further be increase by agility main stat allocation, Poleaxe Specialization, Impale, or spell crit damage talent capstones like Shadow Power. "
        msg += "This makes critical strike an output stat, in the same vein as attack power or haste. However, unlike attack power, critical strike chance is also a mechanical stat for specs like Hot Hands, Low Tide or Primordial Fury.\n"
        msg += "If you're interested in calculating how much damage you will have or gain given a certain amount of critical chance and/or critical damage modifiers, use ,crit_calc [oldChance%] [newChance%] [%coldCritDmg] [%newCritDmg].\n"
        msg += "Since only the first 1% critical gives 1% damage at 200% critical strike damage, this means taking 1% damage talents almost always wins - even at 350% critical damage, you 'only' need 60% crit for 1% damage to become equal to a further 1%.\n"

        if(not verbose):
            msg += "TL;DR the 0->1% crit is 1% damage and the 99%->100% is 0.5% (or 0.75%/0.43% for non-modded spells). Unless you play Hot Hands or another spec that needs to crit for its rotation, don't stack crit ever.\n"
            msg += "Not deep enough? Add v or verbose after ,power to get a further explanation."

        msg += "```"
        await ctx.send(msg)
        if(not verbose):
            return

        if(verbose):
            msg = "```There are exceptions to this rule though - the most common one being Hot Hands or similar specs:\n"
            msg += "Critically striking is not only 280-430% damage, but also is 50% of making your next spell essentially do double damage and cast twice as fast, while reducing cooldown of Combustion - "
            msg += "even going from 99% to 100% is, although hard to accurately model, somewhere around 1.88% damage, which also show why critical strike is so valuable for the spec.\n"
            msg += "For an even more obscene example, Primordial Fury adds around 10k damage to every critical strike, meaning a Flame Shock that would normally do an initial crit for 4k now effectively critically strikes for 18k, or "
            msg += "effectively 900% damage (!).\n"
            msg += "The same is also true for healing - despite most heals, such as Healing Wave, only critically striking for 150% healing, the utility of triggering Ancestral Awakening probably outweighs 1% healing is a majority of cases, "
            msg += "not to mention that Low Tide and Transcendental Embrace benefits from critically healing.\n"
            msg += "There's also talents like Flurry or Nature's Grace, which do not scale linearly with critical strike chance but benefit from it at some level. Furthermore, rage generation is affected by damage done, which means rage gen "
            msg += "output follows roughly the same rules as damage output does."
            msg += "```"
            await ctx.send(msg)

            # msg = "```The astute among you might have noticed the lack of Ascension's wonderful hybrid scaling in the formulas. There's two parts to that - the first is that for non-hybrids, where your lesser power remains more or less static, "
            # msg += "```"
            # await ctx.send(msg)

    @commands.command(pass_context=True)
    async def add(self,ctx, *args):
        if(not str(ctx.message.author.id) in self.superusers):
            await ctx.send("Not allowed :no_entry:")
            return
        
        player_to_add = None
        try:
            player_to_add = str(args[0]).lower()
            player_to_add = mask(player_to_add,self.opts["mask"])
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


            self.ensure_message(player_to_add)
            messages = list(filter(lambda x: x["player"] == player_to_add, self.data))[0]["data"]
            random.shuffle(messages)
            self.player_messages[player_to_add]["messages"] = messages

            await ctx.send(f"Added {"file" if attachment else message} for {player_to_add}")
            return
        await ctx.send("Weird error?")

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

            self.ensure_message(player_to_remove)
            messages = list(filter(lambda x: x["player"] == player_to_remove, self.data))[0]["data"]
            random.shuffle(messages)
            self.player_messages[player_to_remove]["messages"] = messages



    @commands.command(pass_context=True)
    async def player(self, ctx, arg = None):
        if not arg or not isinstance(arg, str):
            await ctx.send("You didn't provide a player name you absolute donkey (or it's not implemented yet <:kekw:677506629910134815>)")
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
            name = mask(arg.lower(),self.opts["mask"])
            self.ensure_message(name)
            if(self.player_messages[name]["index"] >= len(self.player_messages[name]["messages"]) and len(self.player_messages[name]["messages"]) > 0):
                random.shuffle(self.player_messages[name]["messages"])
                while self.player_messages[name]["last_message_id"] == self.player_messages[name]["messages"][0]["id"]:
                    random.shuffle(self.player_messages[name]["messages"])
                self.player_messages[name]["index"] = 0

            res = self.player_messages[name]["messages"][self.player_messages[name]["index"]]
            self.player_messages[name]["index"] += 1
        except Exception as e:
            print(e)
            pass
        if(res):
            self.player_messages[name]["last_message_id"] = res["id"]
            await self.send(ctx,res)
            return
        
        await ctx.send("You didn't provide a player name you absolute donkey (or it's not implemented yet <:kekw:677506629910134815>)")
        return

    @commands.command(pass_context=True)
    async def peperain(self, ctx):
        # TODO - allow adding to peperain
        self.opts["list_of_people"].sort()
        await ctx.send("<a:PepeRain:1260290816874909797>".join(self.opts["list_of_people"]) + "<a:PepeRain:1260290816874909797>")

    @commands.command(pass_context=True)
    async def elvui(self, ctx):
        await ctx.send(random.choice(self.opts["elv_messages"]))

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
    await bot.add_cog(WoW(bot))
