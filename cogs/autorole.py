import discord
from discord.ext import commands
import json

class Autorole(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("Autorole.py is ready.")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        with open ("cogs/json/autorole.json", "r") as f:
            auto_role = json.load(f)

        join_role = discord.utils.get(member.guild.roles, name=auto_role[str(member.guild.id)])

        await member.add_roles(join_role)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def joinrole(self, ctx, role: discord.Role):
        with open ("cogs/json/autorole.json", "r") as f:
            auto_role = json.load(f)

        auto_role[str(ctx.guild.id)] = str(role.name)

        with open("cogs/json/autorole.json", "w") as f:
            json.dump(auto_role, f, intent=4)

        conf_embed = discord.Embed(color=discord.Color.green())
        conf_embed.add_field(name="Success!",value=f"The auto-role has been set to {role.mention}.")
        conf_embed.set_footer(text=f"Actions take by {ctx.author.name}")
        await ctx.send(embed=conf_embed)

async def setup(client):
    await client.add_cog(Autorole(client))