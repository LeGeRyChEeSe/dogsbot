import discord
from discord.ext import commands


class Admin(commands.Cog):

    def __init__(self, client):
        self.client = client

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print("Le bot est prêt.")

    # Commands
    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f"Pong! (Latence du bot: {round(self.client.latency * 1000)}ms)")

    @commands.command(aliases=["purge", "erase", "delete"])
    async def clear(self, ctx, amount=5):
        await ctx.channel.purge(limit=amount + 1)
        print(f"{amount} messages ont été effacé du salon {ctx.channel.name}")

    @commands.command()
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        await member.kick(reason=reason)
        await ctx.send(f"{member.mention} a été expulsé!")

    @commands.command()
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        await member.ban(reason=reason)
        await ctx.send(f"{member.mention} a été banni!")

    @commands.command()
    async def unban(self, ctx, *, member):
        banned_users = await ctx.guild.bans()

        try:
            member_id = int(member)
            for ban_entry in banned_users:
                user = ban_entry.user
                if (user.id == member_id):
                    await ctx.guild.unban(user)
                    return await ctx.send(f"{user.name}#{user.discriminator} a été débanni!")

        except ValueError as err1:
            print("1er try: ", err1)
            try:
                member_name, member_discriminator = member.split('#')
                for ban_entry in banned_users:
                    user = ban_entry.user
                    if (user.name, user.discriminator) == (member_name, member_discriminator):
                        await ctx.guild.unban(user)
                        return await ctx.send(f"{user.name}#{user.discriminator} a été débanni!")

            except Exception as err2:
                print("2e try: ", err2)
                return await ctx.send("Cet utilisateur n'existe pas ou n'a pas été banni!")

            return await ctx.send("Cet utilisateur n'existe pas ou n'a pas été banni!")


def setup(client):
    client.add_cog(Admin(client))
