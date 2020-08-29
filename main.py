import discord

class Bot(discord.Client):
    def __init__(self):
        super().__init__()

    async def on_ready(self):
        print("Loggé en tant que")
        print(self.user.name)
        print(self.user.id)
        await self.change_presence(activity=discord.CustomActivity(name=str("!help")))

    async def on_message(self, message):

        prefix = "!"

        args = message.content[:len(prefix)].strip().split(" ")
        #cmd = args.shift().toLowerCase()

        if (message.author == self.user):
            return

        if (message.content.startswith(prefix)):
            await message.channel.send("\nArguments :")
            await message.channel.send(args)


if __name__ == '__main__':

    bot = Bot()
    bot.run("NzQ4Njg5MDc1ODU4NDQwMzQz.X0hFCQ.rS-FLCyR2wvSItfzSK_qbAmE9U0")
