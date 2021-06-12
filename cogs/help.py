import discord
from discord.ext import commands


class MyHelp(commands.HelpCommand):

    def get_command_signature(self, command: commands.Command):
        return '`%s%s`' % (self.clean_prefix, command.qualified_name)

    async def send_bot_help(self, mapping):
        embed = discord.Embed(title="Help")
        embed.color = discord.Color.red()
        embed.set_footer(
            text=f"Pour en savoir plus sur une catégorie, tapez {self.clean_prefix}help <catégorie>\nPour en savoir plus sur une commande, tapez {self.clean_prefix}help <commande>")

        for cog, commands in mapping.items():
            filtered = await self.filter_commands(commands, sort=True)
            command_signatures = [
                self.get_command_signature(c) for c in filtered]
            if command_signatures:
                cog_name = getattr(cog, "qualified_name", "No Category")
                embed.add_field(name=cog_name, value="\n".join(
                    command_signatures), inline=False)

        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_command_help(self, command: commands.Command):
        embed = discord.Embed(title=command.name.title()
                              )
        embed.color = discord.Color.red()
        embed.description = command.brief

        if command.description:
            embed.add_field(name="Description",
                            value=command.description, inline=False)
        if command.aliases:
            new_aliases = []
            for c in command.aliases:
                if command.full_parent_name:
                    new_aliases.append(f"`{self.clean_prefix}{command.full_parent_name} {c}`")
                else:
                    new_aliases.append(f"`{self.clean_prefix}{c}`")
            embed.add_field(name="Alias", value="\n".join(
                new_aliases), inline=False)

        if command.full_parent_name:
            embed.add_field(name="Comment utiliser la commande",
                            value=f"`{self.clean_prefix}{command.full_parent_name} {command.name}` {command.usage}", inline=False)
        else:
            embed.add_field(name="Comment utiliser la commande",
                            value=f"`{self.clean_prefix}{command.name}` {command.usage}", inline=False)
        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_group_help(self, group: commands.Group):
        embed = discord.Embed(title=group.name.title()
                              )
        embed.color = discord.Color.red()
        embed.description = group.brief
        embed.set_footer(
            text=f"Pour en savoir plus sur une sous-commande, tapez {self.clean_prefix}help {group.name} <sous-commande>")

        if group.description:
            embed.add_field(name="Description",
                            value=group.description, inline=False)
        if group.aliases:
            new_aliases = []
            for c in group.aliases:
                new_aliases.append(f"`{self.clean_prefix}{c}`")
            embed.add_field(name="Alias", value="\n".join(
                new_aliases), inline=False)

        if group.usage:
            embed.add_field(name="Comment utiliser la commande",
                            value=f"`{self.clean_prefix}{group.name}` {group.usage}", inline=False)

        if group.commands:
            embed.add_field(name="Sous-commandes",
                            value="\n".join((f"`{self.clean_prefix}{c.qualified_name}`" for c in group.commands)))
        channel = self.get_destination()
        await channel.send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        embed = discord.Embed(
            title=cog.qualified_name)
        embed.color = discord.Color.red()
        embed.set_footer(
            text=f"Pour en savoir plus sur une commande, tapez {self.clean_prefix}help <commande>\nPour afficher le menu principal, tapez {self.clean_prefix}help")

        filtered = await self.filter_commands(cog.get_commands(), sort=True)
        command_signatures = [
            self.get_command_signature(c) for c in filtered]
        if command_signatures:
            for c in filtered:
                embed.add_field(
                    name=f"`{self.clean_prefix}{c}`", value=c.brief, inline=False)
        channel = self.get_destination()
        await channel.send(embed=embed)


class Help(commands.Cog):
    def __init__(self, client):
        self._original_help_command = client.help_command
        self.client = client
        client.help_command = MyHelp()
        client.help_command.cog = self

    def cog_unload(self):
        self.client.help_command = self._original_help_command


def setup(client: commands.Bot):
    client.add_cog(Help(client))
