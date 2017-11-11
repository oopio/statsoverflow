import discord, aiohttp
from discord.ext import commands
from ext import embeds_coc
import json
from __main__ import InvalidTag
from ext.paginator import PaginatorSession
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import io
import string


class TagCheck(commands.MemberConverter):

    async def convert(self, ctx, argument):
        # Try to convert it to a member.
        try:
            user = await super().convert(ctx, argument)
        except commands.BadArgument:
            pass 
        else:
            return user

        # Not a user so its a tag.
        return argument.strip('#').upper()

class COC_Stats:

    def __init__(self, bot):
        self.bot = bot
        with open('data/config.json') as config:
            self.session = aiohttp.ClientSession(
                headers={
                'Authorization': f"Bearer {json.load(config)['coc-token']}"
                })
        self.conv = TagCheck()


    async def get_clan_from_profile(self, ctx, tag, message):
        async with self.session.get(f"https://api.clashofclans.com/v1/players/%23{tag}") as p:
            profile = await p.json()
        try:
            clan_tag = profile['clan']['tag']
        except KeyError:
            await ctx.send(message)
            raise ValueError(message)
        else:
            return clan_tag.replace("#", "")


    async def resolve_tag(self, ctx, tag_or_user, clan=False):
        if not tag_or_user:
            try:
                tag = ctx.get_tag('clashofclans')
            except Exception as e:
                print(e)
                await ctx.send('You don\'t have a saved tag.')
                raise e
            else:
                if clan is True:
                    return await self.get_clan_from_profile(ctx, tag, 'You don\'t have a clan!')
                return tag
        if isinstance(tag_or_user, discord.Member):
            try:
                tag = ctx.get_tag('clashofclans', tag_or_user.id)
            except KeyError as e:
                await ctx.send('That person doesnt have a saved tag!')
                raise e
            else:
                if clan is True:
                    return await self.get_clan_from_profile(ctx, tag, 'That person does not have a clan!')
                return tag
        else:
            return tag_or_user

    @commands.group(invoke_without_command=True)
    async def cocprofile(self, ctx, *, tag_or_user: TagCheck=None):
        '''Gets the Clash of Clans profile of a player.'''
        tag = await self.resolve_tag(ctx, tag_or_user)

        await ctx.trigger_typing()
        try:
            async with self.session.get(f"https://api.clashofclans.com/v1/players/%23{tag}") as p:
                profile = await p.json()
        except Exception as e:
            return await ctx.send(f'`{e}`')
        else:
            ems = await embeds_coc.format_profile(ctx, profile)
            session = PaginatorSession(
                ctx=ctx,
                pages=ems,
                footer_text='Statsy | Powered by the COC API'
                )
            await session.run()

    @commands.group(invoke_without_command=True)
    async def cocachieve(self, ctx, *, tag_or_user: TagCheck=None):
        '''Gets the Clash of Clans achievements of a player.'''
        tag = await self.resolve_tag(ctx, tag_or_user)

        await ctx.trigger_typing()
        try:
            async with self.session.get(f"https://api.clashofclans.com/v1/players/%23{tag}") as p:
                profile = await p.json()
        except Exception as e:
            return await ctx.send(f'`{e}`')
        else:
            ems = await embeds_coc.format_achievements(ctx, profile)
            session = PaginatorSession(
                ctx=ctx,
                pages=ems,
                footer_text='Statsy | Powered by the COC API'
                )
            await session.run()


    @commands.group(invoke_without_command=True)
    async def cocclan(self, ctx, *, tag_or_user: TagCheck=None):
        '''Gets a clan by tag or by profile. (tagging the user)'''
        tag = await self.resolve_tag(ctx, tag_or_user, clan=True)

        await ctx.trigger_typing()
        try:
            async with self.session.get(f"https://api.clashofclans.com/v1/clans/%23{tag}") as c:
                clan = await c.json()
        except Exception as e:
            return await ctx.send(f'`{e}`')
        else:
            ems = await embeds_coc.format_clan(ctx, clan)
            session = PaginatorSession(
                ctx=ctx,
                pages=ems,
                footer_text='Statsy | Powered by the COC API'
                )
            await session.run()

    @commands.group(invoke_without_command=True)
    async def cocmembers(self, ctx, *, tag_or_user: TagCheck=None):
        '''Gets all the members of a clan.'''
        tag = await self.resolve_tag(ctx, tag_or_user, clan=True)

        await ctx.trigger_typing()
        try:
            async with self.session.get(f"https://api.clashofclans.com/v1/clans/%23{tag}") as c:
                clan = await c.json()
        except Exception as e:
            return await ctx.send(f'`{e}`')
        else:
            ems = await embeds_coc.format_members(ctx, clan)
            if len(ems) > 1:
                session = PaginatorSession(
                    ctx=ctx, 
                    pages=ems, 
                    footer_text=f'{clan["members"]}/50 members'
                    )
                await session.run()
            else:
                await ctx.send(embed=ems[0])

    @cocmembers.command()
    async def best(self, ctx, *, tag_or_user: TagCheck=None):
        '''Finds the best members of the clan currently.'''
        tag = await self.resolve_tag(ctx, tag_or_user, clan=True)
        async with ctx.typing():
            try:
                async with self.session.get(f"https://api.clashofclans.com/v1/clans/%23{tag}") as c:
                    clan = await c.json()
            except Exception as e:
                return await ctx.send(f'`{e}`')
            else:
                if clan['members'] < 4:
                    return await ctx.send('Clan must have more than 4 players for heuristics.')
                else:
                    em = await embeds_coc.format_most_valuable(ctx, clan)
                    await ctx.send(embed=em)

    @cocmembers.command()
    async def worst(self, ctx, *, tag_or_user: TagCheck=None):
        '''Finds the worst members of the clan currently.'''
        tag = await self.resolve_tag(ctx, tag_or_user, clan=True)
        async with ctx.typing():
            try:
                async with self.session.get(f"https://api.clashofclans.com/v1/clans/%23{tag}") as c:
                    clan = await c.json()
            except Exception as e:
                return await ctx.send(f'`{e}`')
            else:
                if clan['members'] < 4:
                    return await ctx.send('Clan must have more than 4 players for heuristics.')
                else:
                    em = await embeds_coc.format_least_valuable(ctx, clan)
                    await ctx.send(embed=em)

            
    @commands.command()
    async def cocsave(self, ctx, *, tag):
        '''Saves a Clash of Clans tag to your discord.

        Ability to save multiple tags coming soon.
        '''
        ctx.save_tag(tag.replace("#", ""), 'clashofclans')
        await ctx.send('Successfuly saved tag.')

    @commands.command()
    async def cocwar(self, ctx, *, tag_or_user: TagCheck=None):
        '''WIP Check your current war status.'''
        image = await self.bot.loop.run_in_executor(None, self.war_image, 'https://api-assets.clashofclans.com/badges/512/REuMPl3FAw5LBpuSc3q9yLnULe45VaUgmoxYbolK_EY.png', 'https://api-assets.clashofclans.com/badges/512/Zwr2pvJSYsWYvRKh6Eoew-JEdXOy7uehMXp70fM6BPk.png')
        em = discord.Embed()
        em.set_image('attachment://war.png')
        await ctx.send(file=discord.File(image, 'war.png'), embed=em)

    def war_image(self, clan_url, opponent_url):

        bg_image = Image.open("data/war-bg.png")
        size = bg_image.size

        image = Image.new("RGBA", size)
        image.paste(bg_image)

        c = io.BytesIO(clan_url):
        clan_img = Image.open(c)

        o = io.BytesIO(opponent_url):
        opp_img = Image.open(o)

        c_box = (50, 55.5, 562, 567.5)
        image.paste(clan_img, box, clan_img)

        file = io.BytesIO()
        image.save(file, format="PNG")
        file.seek(0)
        return file


def setup(bot):
    cog = COC_Stats(bot)
    bot.add_cog(cog)
