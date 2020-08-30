import discord
import random
import env
import events.client.on_ready
import events.client.on_message


class Bot(discord.Client):
    def __init__(self):
        super().__init__()

    async def on_ready(self):
        print(self.user.name + " loggé !")
        print("Id : " + str(self.user.id))
        print("En attente...")

    def random_colour(self):
        hexa = "0123456789abcdef"
        random_colour = "0x"
        for i in range(6):
            random_colour += random.choice(hexa)
        return discord.Colour(int(random_colour, 16))

    def create_embed(self, title, description, colour, image=None):
        embed = discord.Embed()
        embed.title = title
        embed.description = description
        embed.colour = colour
        if (image != None):
            embed.set_thumbnail(url=image)
        return embed

    async def on_message(self, message):

        server = message.guild
        channel = message.channel
        author = message.author
        content = message.content

        prefix = "!"

        if (author == self.user):
            return

        if (content.startswith(prefix + "dm")):

            try:
                name = content.split(" ")[1]
            except:
                return await channel.send("Aucun utilisateur.")

            member = discord.utils.get(
                server.members, name=name)

            try:
                return await member.send("Je suis arrivé dans tes DMs !")
            except discord.Forbidden:
                return await member.send("L'utilisateur n'accepte pas les DMs depuis des membres de ce serveur !")

        if (content.startswith(prefix + "em")):

            title = author.display_name

            roles = author.roles

            roles.sort(reverse=True)

            description = ""

            for role in roles:
                description += role.mention + "\n"

            colour = self.random_colour()

            image = author.avatar_url

            embed = self.create_embed(title, description, colour, image)

            return await channel.send(embed=embed)

        if (content.startswith(prefix + "invite")):
            invite = await channel.create_invite(max_age=3600, unique=False)

            if (message.mentions == None):
                return await channel.send(invite.url)
            else:
                for mention in message.mentions:
                    await mention.send(
                        "Vous avez reçu une invitation dans le serveur " + str(server) + " envoyée par " + invite.inviter.mention + " !\nElle est valable pour " + str(invite.max_age/3600) + "h !\n" + invite.url)
                return await channel.send("Le lien d'invitation au serveur " + server.name + " a été envoyé à toutes les personnes mentionnées.")

        if (content.startswith(prefix)):
            await channel.send("La commande " + content + " n'existe pas encore, veuillez patienter !")


if __name__ == '__main__':

    bot = Bot()
    bot.run(env.TOKEN)
