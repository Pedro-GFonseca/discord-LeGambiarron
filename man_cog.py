import discord
import datetime
from discord.ext import commands


async def setup(bot):
    await bot.add_cog(help_cog(bot))


class help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.embedOrange = 0xeab148
        self.embedDarkPink = 0x7d3243

    def infoEmbedGen(self, name):
        embed = discord.Embed(
            title="Tudo funcionando, aparentemente",
            description=f"""
            O prefixo do bot é **`'{self.bot.command_prefix}'`** pra ativar. É só falar **`-man`** pra ler o manual.

            O código tá no [github](https://github.com/Pedro-GFonseca/discord-LeGambiarron) se quiser ajudar a fazer""",
            colour=self.embedOrange
        )
        return embed

    def errorEmbedGen(self, error):
        embed = discord.Embed(
            title="ERRO :(",
            description="Deu erro aí, testa se dá pra continuar usando o bot, se não algum ADM precisa usar o comando -exec pra reiniciar o bot.\n\nError:\n**`" +
            str(error) + "`**",
            colour=self.embedDarkPink
        )
        return embed

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        print(print("[" + datetime.time.now() + "] " + str(error)))
        await ctx.send(embed=self.errorEmbedGen(error))

    @ commands.Cog.listener()
    async def on_ready(self):
        sendToChannels = []
        botNames = {}
        for guild in self.bot.guilds:
            channel = guild.text_channels[0]
            sendToChannels.append(channel)
            botMember = await guild.fetch_member(975410595576840272)
            nickname = botMember.nick
            if nickname == None:
                nickname = botMember.name
            botNames[guild.id] = nickname

    @ commands.command(
        name="man",
        aliases=["manual"],
        help="""
            (nome do comando)
            Dá uma descrição do comando especificado. Se não especificar nenhum comando, dá uma descrição de todos os comandos.
            """
    )
    async def help(self, ctx, arg=""):
        helpCog = self.bot.get_cog('help_cog')
        musicCog = self.bot.get_cog('music_cog')
        commands = helpCog.get_commands() + musicCog.get_commands()
        if arg != "":
            command = None
            for i, c in enumerate(commands):
                if c.name == arg:
                    command = commands[i]
            if command == None:
                await ctx.send("não tem comando com esse nome")
                return

            arguments = command.help.split("\n")[0]
            longHelp = command.help.split("\n")[2]
            aliases = ""
            for a in command.aliases:
                aliases += f"-{a}, "
            aliases = aliases.rstrip(", ")
            commandsEmbed = discord.Embed(
                title=f"-{command.name} informação",
                description=f"""
                Argumentos: **`{arguments}`**
                {longHelp}

                Aliases: **`{aliases}`**
                """,
                colour=self.embedOrange
            )

        else:
            commandDescription = ""
            for c in commands:
                arguments = c.help.split("\n")[0]
                shortHelp = c.help.split("\n")[1]
                commandDescription += f"**`-{c.name} {arguments}`** - {shortHelp}\n"
            commandsEmbed = discord.Embed(
                title="Lista de comandos",
                description=commandDescription,
                colour=self.embedOrange
            )

        commandKey = """
            **`Prefixo`** - '-'

            **`-command <>`** - não precisa de argumento
            **`-command ()`** - argumento opcional
            **`-command []`** - argumento obrigatório
            **`-command [arg]`** - 'arg' especifica o tipo de argumento (ex. "url" ou "keywords")
            **`-command (um || dois)`** - argumentos exclusivos. Ou passa o argumento um ou o dois
        """

        keyEmbed = discord.Embed(
            title="Como passar os comandos:",
            description=commandKey,
            colour=self.embedOrange
        )
        await ctx.send(embed=commandsEmbed)
        await ctx.send(embed=keyEmbed)

    @commands.command(
        name='info',
        aliases=[],
        help="""
            <>
            Mostra se tá tudo funcionando por aqui
            """
    )
    async def info(self, ctx):
        await ctx.send(embed=self.infoEmbedGen("Bobbert"))