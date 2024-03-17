#!/usr/bin/python3

import discord
from discord.ext import commands
import asyncio
from asyncio import run_coroutine_threadsafe
from urllib import parse, request
import re
import json
import os
import datetime
from youtube_dl import YoutubeDL
import random
from music_messages import leave_message, join_message

async def setup(bot):
    await bot.add_cog(music_cog(bot))


class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cwd = os.getcwd()
        self.names = {}

        self.is_playing = {}
        self.is_paused = {}
        self.musicQueue = {}
        self.queueIndex = {}
        self.sound_playing = {}

        self.YTDL_OPTIONS = {
            'format': 'bestaudio/best',
            'nonplaylist': 'True',
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

        self.embedBlue = 0x2c76dd
        self.embedRed = 0xdf1141
        self.embedGreen = 0x0eaa51
        self.embedDarkPink = 0x7d3243

        self.vc = {}

        self.sounds = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            id = int(guild.id)
            self.musicQueue[id] = []
            self.queueIndex[id] = 0
            self.vc[id] = None
            self.is_paused[id] = self.is_playing[id] = False

            botMember = await guild.fetch_member(975410595576840272)
            nickname = botMember.nick
            if nickname == None:
                nickname = botMember.name
            self.names[id] = nickname

    # Auto Leave

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # if the trigger was the bot and the action was joining a channel
        id = int(member.guild.id)
        if member.id == self.bot.user.id and before.channel == None and after.channel != None:
            cooldownMinutes = 10
            time = 0
            while True:
                await asyncio.sleep(1)
                time += 1
                if self.is_playing[id] and not self.is_paused[id]:
                    time = 0
                if time == cooldownMinutes * 60:
                    self.is_playing[id] = False
                    self.is_paused[id] = False
                    self.musicQueue[id] = []
                    self.queueIndex[id] = 0
                    await self.vc[id].disconnect()
                    self.vc[id] = None
                if self.vc[id] == None or not self.vc[id].is_connected():
                    break
        # if the trigger is a user (not the bot) and the action was leaving a channel
        if member.id != self.bot.user.id and before.channel != None and after.channel != before.channel:
            remainingChannelMembers = before.channel.members
            if len(remainingChannelMembers) == 1 and remainingChannelMembers[0].id == self.bot.user.id and self.vc[id].is_connected():
                self.is_playing[id] = False
                self.is_paused[id] = False
                self.musicQueue[id] = []
                self.queueIndex[id] = 0
                await self.vc[id].disconnect()


    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        print("[" + datetime.time.now() + "] " + str(error))
        await ctx.send(embed=self.errorEmbedGen(error))

    def errorEmbedGen(self, error):
        embed = discord.Embed(
            title="ERRO :(",
            description="deu algum erro aí, adivinha quem vai ter que debugar?\n\nErro:\n**`" +
            str(error) + "`**",
            colour=self.embedDarkPink
        )
        return embed

    def generate_embed(self, ctx, song, type):
        TITLE = song['title']
        LINK = song['link']
        THUMBNAIL = song['thumbnail']
        AUTHOR = ctx.author
        AVATAR = AUTHOR.avatar

        if type == 1:
            nowPlaying = discord.Embed(
                title="tocando uma",
                description=f'[{TITLE}]({LINK})',
                colour=self.embedBlue
            )
            nowPlaying.set_thumbnail(url=THUMBNAIL)
            nowPlaying.set_footer(
                text=f"o corno que botou essa: {str(AUTHOR)}", icon_url=AVATAR)
            return nowPlaying

        if type == 2:
            songAdded = discord.Embed(
                title="na fila",
                description=f'[{TITLE}]({LINK})',
                colour=self.embedRed
            )
            songAdded.set_thumbnail(url=THUMBNAIL)
            songAdded.set_footer(
                text=f"o corno que botou essa: {str(AUTHOR)}", icon_url=AVATAR)
            return songAdded

        if type == 4:
            songInserted = discord.Embed(
                title="tá como próximo na fila",
                description=f'[{TITLE}]({LINK})',
                colour=self.embedRed
            )
            songInserted.set_thumbnail(url=THUMBNAIL)
            songInserted.set_footer(
                text=f"o corno que botou essa: {str(AUTHOR)}", icon_url=AVATAR)
            return songInserted

        if type == 3:
            songRemoved = discord.Embed(
                title="boa ideia, puta música bosta",
                description=f'[{TITLE}]({LINK})',
                colour=self.embedRed
            )
            songRemoved.set_thumbnail(url=THUMBNAIL)
            songRemoved.set_footer(
                text=f"corno que removeu: {str(AUTHOR)}", icon_url=AVATAR)
            return songRemoved

    async def join_VC(self, ctx, channel):
        roll = random.randint(0, 6)
        
        id = int(ctx.guild.id)
        if self.vc[id] == None or not self.vc[id].is_connected():
            self.vc[id] = await channel.connect()
            await ctx.send('cheguei porra')

            if self.vc[id] == None:
                await ctx.send("tu tem q entrar em algum channel primeiro")
                return
        else:
            await self.vc[id].move_to(channel)
            await ctx.send(f"{join_message[roll]}")

    def get_YT_title(self, VideoID):
        params = {"format": "json",
                  "url": "https://www.youtube.com/watch?v=%s" % VideoID}
        url = "https://www.youtube.com/oembed"
        query_string = parse.urlencode(params)
        url = url + "?" + query_string
        with request.urlopen(url) as response:
            response_text = response.read()
            data = json.loads(response_text.decode())
            return data['title']

    def search_YT(self, search):
        queryString = parse.urlencode({'search_query': search})
        htmContent = request.urlopen(
            'http://www.youtube.com/results?' + queryString)
        searchResults = re.findall(
            '/watch\?v=(.{11})', htmContent.read().decode())
        return searchResults[0:10]

    def extract_YT(self, url):
        with YoutubeDL(self.YTDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except:
                return False
        return {
            'link': 'https://www.youtube.com/watch?v=' + url,
            'thumbnail': info['thumbnails'][-1]['url'],
            'source': info['url'],
            'title': info['title']
        }

    def play_next(self, ctx):
        id = int(ctx.guild.id)
        if not self.is_playing[id]:
            return
        if self.queueIndex[id] + 1 < len(self.musicQueue[id]):
            self.is_playing[id] = True
            self.queueIndex[id] += 1

            song = self.musicQueue[id][self.queueIndex[id]][0]
            message = self.generate_embed(ctx, song, 1)
            coro = ctx.send(embed=message)
            fut = run_coroutine_threadsafe(coro, self.bot.loop)
            try:
                fut.result()
            except:
                pass

            self.vc[id].play(discord.FFmpegPCMAudio(
                song['source'], **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
        else:
            coro = ctx.send("acabou as músicas, posso ir pra casa agr?")
            fut = run_coroutine_threadsafe(coro, self.bot.loop)
            try:
                fut.result()
            except:
                pass
            print("deu erro aqui meu mano")
            self.queueIndex[id] += 1
            self.is_playing[id] = False

    async def play_music(self, ctx):
        roll = random.randint(0, (len(join_message) - 1))
        id = int(ctx.guild.id)

        if self.queueIndex[id] < len(self.musicQueue[id]):
            self.is_playing[id] = True
            self.is_paused[id] = False

            if self.vc[id] == None:
                await self.join_VC(ctx, self.musicQueue[id][self.queueIndex[id]][1])

            song = self.musicQueue[id][self.queueIndex[id]][0]
            message = self.generate_embed(ctx, song, 1)
            await ctx.send(embed=message)
            await ctx.send(join_message[roll])

            self.vc[id].play(discord.FFmpegPCMAudio(
                song['source'], **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
        else:
            await ctx.send("tem música nenhuma pra tocar")
            self.queueIndex[id] += 1
            self.is_playing[id] = False


    # Play Command

    @ commands.command(
        name="p",
        aliases=["play"],
        help="""
            (url || nome da música)
            Toca música do youtube.
            """
    )
    async def play(self, ctx, *args):
        search = " ".join(args)
        id = int(ctx.guild.id)
        try:
            userChannel = ctx.author.voice.channel               
        except:
            await ctx.send("tu tem q tar em algum channel meu mano")
            return
        if not args:
            if len(self.musicQueue[id]) == 0:
                await ctx.send("tem música nenhuma pra tocar")
                return
            elif not self.is_playing[id]:
                if self.musicQueue[id] == None or self.vc[id] == None:
                    await self.play_music(ctx)
                else:
                    self.is_paused[id] = False
                    self.is_playing[id] = True
                    self.vc[id].resume()
            else:
                return
        else:
            searchResults = self.search_YT(search)
            for i in range(10):
                song = self.extract_YT(searchResults[i])
                if not ("shopify" in str(song['title']).lower()):
                    break
            if type(song) == type(True):
                await ctx.send("tu digitou o nome da música meio cagado aí")
            else:
                self.musicQueue[id].append([song, userChannel])

                if self.is_paused[id]:
                    await ctx.send("tamo de volta")
                    self.is_playing[id] = True
                    self.is_paused[id] = False
                    self.vc[id].resume()

                if not self.is_playing[id]:
                    await self.play_music(ctx)
                else:
                    message = self.generate_embed(ctx, song, 2)
                    await ctx.send(embed=message)

    @ commands.command(
        name="add",
        aliases=["newsound"],
        help="""
            [nome , link]
            Adiciona um novo som ao bot
            """
    )
    async def new_sound(self, ctx, *args):
        if not args:
            await ctx.send('tem que passar o argumento pra essa função')
        else:
            try:
                name = args[0]
                link = args[1]
            except:
                await ctx.send('tá faltando o nome ou o link')
                return

            if link.startswith('https://www.youtube.com/watch?v='):
                searchResults = self.search_YT(link)
                
                for i in range(10):
                    added_sound = self.extract_YT(searchResults[i])
                    
                    if not ("shopify" in str(added_sound['title']).lower()):
                        break
            
                if type(added_sound) == type(True):
                    await ctx.send("tu digitou o nome da música meio cagado aí")
                    return
                else:
                    self.sounds[f'{name}'] = added_sound
                    await ctx.send('som adicionado')
            else:
                await ctx.send('isso não é um link de youtube válido, digita -man add pra ver como tem que ser o link')

    @ commands.command(
        name="rms",
        aliases=["removesound"],
        help="""
            [nome]
            Remove um som do bot
            """
    )
    async def remove_sound(self, ctx, *args):
        if not args:
            await ctx.send('tem que passar o argumento pra essa função')
        else:
            if args[0] in self.sounds:
                del self.sounds[f'{args[0]}']
                await ctx.send('som removido')
            else:
                await ctx.send('esse som não tá na lista')

    @ commands.command(
        name="sl",
        aliases=["soundlist"],
        help="""
            <>
            Lista os sons do bot
            """
    )
    async def sound_list(self, ctx):
        sl_embed = discord.Embed(
            title='Lista de sons disponíveis:',
            description='digite -y <nome do som> pra tocar o som',
            colour=self.embedBlue
        )
        if not self.sounds:
            await ctx.send('a lista tá vazia')
        else:
            for key in self.sounds.keys():
                sl_embed.add_field(name=f'{key}', value='', inline=False)
            
            await ctx.send(embed=sl_embed)
                

    @ commands.command(
        name="debug",
        aliases=["dbg"],
        help="""
            [nome]
            Um comando de debug, tá aqui temporariamente.
            """
    )
 
    async def debugger(self, ctx):
        await ctx.send(f'Status da classe: \n {self.is_playing}, \n {self.is_paused}, \n {self.musicQueue}, \n {self.queueIndex}, \n {self.vc}, \n {self.sound_playing}')
    
    @ commands.command(
        name="ps",
        aliases=["playsound"],
        help="""
            [nome]
            Toca um som do bot
            """
    )
    
    async def play_sound(self, ctx: str, *args: str) -> None:
        id = int(ctx.guild.id)
        if not args:
            await ctx.send('tem que passar o nome do som')
        else:
            if args[0] in self.sounds:
                search = self.sounds[f'{args[0]}']
                sound = search['source']
                
                try:
                    userChannel = ctx.author.voice.channel               
                except:
                    await ctx.send("tu tem q tar em algum channel")
                    return

                if self.vc[id] == None:
                    await self.join_VC(ctx, userChannel)
                    
                if not self.is_playing[id]:
                    self.vc[id].play(discord.FFmpegPCMAudio(
                        sound, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next(ctx))
                else:
                    await ctx.send('já tem música tocando, não dá pra tocar um som por cima')
                    return
            else:
                await ctx.send('não tem esse som')
                await ctx.send(args[0])
                return
    


    @ commands.command(
        name="pa",
        aliases=["p-add"],
        help="""
            [url || busca]
            Coloca o primeiro resultado do youtube na fila.
            """
    )
    async def add(self, ctx, *args):
        search = " ".join(args)

        try:
            userChannel = ctx.author.voice.channel
        except:
            await ctx.send("tu n tá em channel nenhum meu parça")
            return
        if not args:
            await ctx.send("fala a música q tu quer q eu bote aí caraio")
        else:
            song = self.extract_YT(self.search_YT(search)[0])
            if type(song) == type(True):
                await ctx.send("achei essa música não parça")
                return
            else:
                self.musicQueue[ctx.guild.id].append([song, userChannel])
                message = self.generate_embed(ctx, song, 2)
                await ctx.send(embed=message)

    # AddNext Command

    @ commands.command(
        name="pn",
        aliases=["addnext"],
        help="""
            [url || nome da música]
            Coloca o primeiro resultado da busca na fila.
            """
    )
    async def addNext(self, ctx, *args):
        search = " ".join(args)

        try:
            userChannel = ctx.author.voice.channel
        except:
            await ctx.send("entra em algum channel primeiro")
            return
        if not args:
            await ctx.send("como eu vou adicionar alguma música se tu n me diz qual?")
        else:
            song = self.extract_YT(self.search_YT(search)[0])
            if type(song) == type(True):
                await ctx.send("achei a música não mano")
                return
            else:
                self.musicQueue[ctx.guild.id].insert(
                    self.queueIndex + 1, [song, userChannel])
                message = self.generate_embed(ctx, song, 4)
                await ctx.send(embed=message)
    # Remove Command

    @ commands.command(
        name="rm",
        aliases=["remove"],
        help="""
            <>
            Remove a última música da lista.
            """
    )
    async def remove(self, ctx):
        id = int(ctx.guild.id)
        if self.musicQueue[id] != []:
            song = self.musicQueue[id][-1][0]
            removeSongEmbed = self.generate_embed(ctx, song, 3)
            await ctx.send(embed=removeSongEmbed)
        else:
            await ctx.send("tem nada na fila")
        self.musicQueue[id] = self.musicQueue[id][:-1]
        if self.musicQueue[id] == []:
            # clear queue and stop playing
            if self.vc[id] != None and self.is_playing[id]:
                self.is_playing[id] = False
                self.is_paused[id] = False
                self.vc[id].stop()
            self.queueIndex[id] = 0
        elif self.queueIndex[id] == len(self.musicQueue[id]) and self.vc[id] != None and self.vc[id]:
            self.vc[id].pause()
            self.queueIndex[id] -= 1
            await self.play_music(ctx)

    # Pause Command

    @ commands.command(
        name="s",
        aliases=["pause"],
        help="""
            <>
            Pausa a música.
            """,
    )
    async def pause(self, ctx):
        id = int(ctx.guild.id)
        if not self.vc[id]:
            await ctx.send("oxe, tô tocando nada")
        elif self.is_playing[id]:
            await ctx.send("nem tu aguentou essa música de corno?")
            self.is_playing[id] = False
            self.is_paused[id] = True
            self.vc[id].pause()
    # Resume Command

    @ commands.command(
        name="u",
        aliases=["resume"],
        help="""
            <>
            Despausa a música.
            """,
    )
    async def resume(self, ctx):
        id = int(ctx.guild.id)
        if not self.vc[id]:
            await ctx.send("tem nada tocando maluco")
        if self.is_paused[id]:
            await ctx.send("tamo de volta")
            self.is_playing[id] = True
            self.is_paused[id] = False
            self.vc[id].resume()

    # Skip Command

    @ commands.command(
        name="pr",
        aliases=["previous"],
        help="""
            <>
            Toca a mesma música que acabou de tocar.
            """,
    )
    async def previous(self, ctx):
        id = int(ctx.guild.id)
        if self.vc[id] == None:
            await ctx.send("entra em algum channel primeiro mano")
        elif self.queueIndex[id] <= 0:
            await ctx.send("tinha nenhuma música tocando antes dessa")
            self.vc[id].pause()
            await self.play_music(ctx)
        elif self.vc[id] != None and self.vc[id]:
            self.vc[id].pause()
            self.queueIndex[id] -= 1
            await self.play_music(ctx)

    # Skip Command

    @ commands.command(
        name="k",
        aliases=["skip"],
        help="""
            <>
            Pula pra próxima música da fila. Se não tiver nenhuma, vai tocar a mesma música.
            """,
    )
    async def skip(self, ctx):
        id = int(ctx.guild.id)
        if self.vc[id] == None:
            await ctx.send("entra em algum channel primeiro mano")
        elif self.queueIndex[id] >= len(self.musicQueue[id]) - 1:
            await ctx.send("não tem nenhuma música além dessa, vô tocá ela de novo")
            self.vc[id].pause()
            await self.play_music(ctx)
        elif self.vc[id] != None and self.vc[id]:
            self.vc[id].pause()
            self.queueIndex[id] += 1
            await self.play_music(ctx)

    # List Queue Command

    @ commands.command(
        name="ls",
        aliases=["queue"],
        help="""
            <>
            Lista as músicas que tão na fila.
            """,
    )
    async def queue(self, ctx):
        id = int(ctx.guild.id)
        returnValue = ""
        if self.musicQueue[id] == []:
            await ctx.send("tem música nenhuma na fila")
            return

        if len(self.musicQueue[id]) <= self.queueIndex[id]:
            await ctx.send("acabou as músicas")
            return

        for i in range(self.queueIndex[id], len(self.musicQueue[id])):
            upNextSongs = len(
                self.musicQueue[id]) - self.queueIndex[id]
            if i > 5 + upNextSongs:
                break
            returnIndex = i - self.queueIndex[id]
            if returnIndex == 0:
                returnIndex = "tocando"
            elif returnIndex == 1:
                returnIndex = "próxima"
            returnValue += f"{returnIndex} - [{self.musicQueue[id][i][0]['title']}]({self.musicQueue[id][i][0]['link']})\n"

            if returnValue == "":
                await ctx.send("a fila tá vazia")
                return

        queue = discord.Embed(
            title="fila do INSS",
            description=returnValue,
            colour=self.embedGreen
        )
        await ctx.send(embed=queue)

    # Clear Queue Command

    @ commands.command(
        name="rls",
        aliases=["clear"],
        help="""
            <>
            Remove todas as músicas da fila.
            """,
    )
    async def clear(self, ctx):
        id = int(ctx.guild.id)
        if self.vc[id] != None and self.is_playing[id]:
            self.is_playing[id] = False
            self.is_paused[id] = False
            self.vc[id].stop()
        if self.musicQueue[id] != []:
            await ctx.send("limpei a lista")
            self.musicQueue[id] = []
        self.queueIndex[id] = 0

    # Join VC Command

    @ commands.command(
        name="j",
        aliases=["join"],
        help="""
            <>
            Conecta ao canal de voz.
            """,
    )
    async def join(self, ctx):
        if ctx.author.voice:
            userChannel = ctx.author.voice.channel
            await self.join_VC(ctx, userChannel)
            await ctx.send(f"{self.names[ctx.guild.id]} entrou {userChannel}!")
        else:
            await ctx.send("tu n tá em channel nenhum fio")

    # Leave VC Command

    @ commands.command(
        name="x",
        aliases=["leave"],
        help="""
            <>
            Tira o bot do canal e limpa a fila.
            """,
    )
    async def leave(self, ctx):
        roll = random.randint(0, 6)

        id = int(ctx.guild.id)
        self.is_playing[id] = False
        self.is_paused[id] = False
        self.musicQueue[id] = []
        self.queueIndex[id] = 0
        if self.vc[id] != None:
            await ctx.send(f'{leave_message[roll]}')
            await self.vc[id].disconnect()
            self.vc[id] = None
