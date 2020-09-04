import discord
from discord.ext import commands
import datetime

class AntiRemoval(commands.Cog):
    def __init__(self, client, db, webhook):
        self.client = client
        self.db = db
        self.webhook = webhook

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        whitelistedUsers = self.db.find_one({ "guild_id": guild.id })["users"]
        async for i in guild.audit_logs(limit=1, after=datetime.datetime.now() - datetime.timedelta(minutes = 15), action=discord.AuditLogAction.ban):
            if i.user.id in whitelistedUsers or i.user in whitelistedUsers:
                return
            
            await guild.ban(i.user)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        whitelistedUsers = self.db.find_one({ "guild_id": member.guild.id })["users"]
        async for i in member.guild.audit_logs(limit=1, after=datetime.datetime.now() - datetime.timedelta(minutes = 15), action=discord.AuditLogAction.kick):
            if i.user.id in whitelistedUsers or i.user in whitelistedUsers:
                return
                
            if i.target.id == member.id:
                await member.guild.ban(i.user)
                return