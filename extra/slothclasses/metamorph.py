import discord
from discord.ext import commands
from .player import Player, Skill
from mysqldb import the_database
from extra.menu import ConfirmSkill
from extra import utils
import os
from datetime import datetime

bots_and_commands_channel_id = int(os.getenv('BOTS_AND_COMMANDS_CHANNEL_ID'))


class Metamorph(Player):

    emoji = '<:Metamorph:839498019204497458>'

    def __init__(self, client) -> None:
        self.client = client

    @commands.command(aliases=['transmutate', 'trans'])
    @Player.skill_on_cooldown()
    @Player.user_is_class('metamorph')
    @Player.skill_mark()
    async def transmutation(self, ctx) -> None:
        """ Transmutates into a different form for 1 day, that you can see in your z!profile. """

        if ctx.channel.id != bots_and_commands_channel_id:
            return await ctx.send(f"**{ctx.author.mention}, you can only use this command in {self.bots_txt.mention}!**")

        member = ctx.author

        member_fx = await self.get_user_effects(member)

        if 'knocked_out' in member_fx:
            return await ctx.send(f"**{member.mention}, you can't use your skill, because you are knocked-out!**")

        if 'transmutated' in member_fx:
            return await ctx.send(f"**You are already transmutated, {member.mention}!**")

        confirmed = await ConfirmSkill(f"**{member.mention}, are you sure you want to transmutate yourself into a diffrent form for 1 day?**").prompt(ctx)
        if not confirmed:
            return await ctx.send(f"**{member.mention}, not transmutating, then!**")

        _, exists = await Player.skill_on_cooldown(skill=Skill.ONE).predicate(ctx)

        timestamp = await utils.get_timestamp()
        await self.insert_skill_action(
            user_id=member.id, skill_type="transmutation",
            skill_timestamp=timestamp, target_id=member.id,
            channel_id=ctx.channel.id
        )
        if exists:
            await self.update_user_skill_ts(member.id, Skill.ONE, timestamp)
        else:
            await self.insert_user_skill_cooldown(member.id, Skill.ONE, timestamp)
        # Updates user's skills used counter
        await self.update_user_skills_used(user_id=member.id)

        transmutation_embed = await self.get_transmutation_embed(channel=ctx.channel, perpetrator_id=member.id)
        await ctx.send(embed=transmutation_embed)

    async def check_transmutations(self) -> None:

        """ Check on-going transmutations and their expiration time. """

        transmutations = await self.get_expired_transmutations()
        for tm in transmutations:
            # print(tm)
            await self.delete_skill_action_by_target_id_and_skill_type(tm[3], 'transmutation')

            channel = self.bots_txt

            await channel.send(
                content=f"<@{tm[0]}>",
                embed=discord.Embed(
                    description=f"**<@{tm[3]}>'s `Transmutation` has just expired! 🐩→💥→🦥**",
                    color=discord.Color.red()))

    async def check_frogs(self) -> None:

        """ Check on-going frogs and their expiration time. """

        frogs = await self.get_expired_frogs()
        for f in frogs:
            try:
                await self.delete_skill_action_by_target_id_and_skill_type(f[3], 'frog')

                channel = self.bots_txt

                await channel.send(
                    content=f"<@{f[0]}>",
                    embed=discord.Embed(
                        description=f"**<@{f[3]}>'s `Frog` has just expired! 🐸→💥→🦥**",
                        color=discord.Color.red()))
            except:
                pass

    @commands.command(aliases=['frogify'])
    @Player.skills_used(requirement=5)
    @Player.skill_on_cooldown(skill=Skill.TWO)
    @Player.user_is_class('metamorph')
    @Player.skill_mark()
    async def frog(self, ctx, target: discord.Member = None) -> None:
        """ Makes someone a frog temporarily.
        :param target: The person who you want to frog. """

        if ctx.channel.id != bots_and_commands_channel_id:
            return await ctx.send(f"**{ctx.author.mention}, you can only use this command in {self.bots_txt.mention}!**")

        attacker = ctx.author

        attacker_effects = await self.get_user_effects(member=attacker)

        if 'knocked_out' in attacker_effects:
            return await ctx.send(f"**{attacker.mention}, you can't use your skill, because you are knocked-out!**")

        if not target:
            return await ctx.send(f"**Please, inform a target to frog, {attacker.mention}!**")

        if target.id == attacker.id:
            return await ctx.send(f"**You cannot frog yourself, {attacker.mention}!**")

        if target.bot:
            return await ctx.send(f"**{attacker.mention}, you cannot frog a bot!**")

        target_sloth_profile = await self.get_sloth_profile(target.id)
        if not target_sloth_profile:
            return await ctx.send(f"**You cannot frog someone who doesn't have an account, {attacker.mention}!**")

        if target_sloth_profile[1] == 'default':
            return await ctx.send(f"**You cannot frog someone who has a `default` Sloth class, {attacker.mention}!**")

        target_effects = await self.get_user_effects(member=target)

        if 'frogged' in target_effects:
            return await ctx.send(f"**{target.mention} is already frogged, {attacker.mention}!**")

        if 'protected' in target_effects:
            return await ctx.send(f"**{target.mention} is protected against threats, {attacker.mention}!**")

        confirmed = await ConfirmSkill(f"**{attacker.mention}, are you sure you want to frog {target.mention}?**").prompt(ctx)
        if not confirmed:
            return await ctx.send(f"**{attacker.mention}, not frogging them, then!**")

        _, exists = await Player.skill_on_cooldown(skill=Skill.TWO).predicate(ctx)

        timestamp = await utils.get_timestamp()
        await self.insert_skill_action(
            user_id=attacker.id, skill_type="frog",
            skill_timestamp=timestamp, target_id=target.id,
            channel_id=ctx.channel.id
        )
        try:
            if exists:
                await self.update_user_skill_ts(attacker.id, Skill.TWO, timestamp)
            else:
                await self.insert_user_skill_cooldown(ctx.author.id, Skill.TWO, timestamp)
            # Updates user's skills used counter
            await self.update_user_skills_used(user_id=attacker.id)
        except Exception as e:
            print(e)
            await ctx.send(f"**Something went wrong with it, {attacker.mention}!**")
        else:
            frogged_embed = await self.get_frogged_embed(channel=ctx.channel, attacker_id=attacker.id, target_id=target.id)
            await ctx.send(embed=frogged_embed)
            if 'reflect' in target_effects:
                await self.reflect_attack(ctx, attacker, target, 'frog')

    async def get_transmutation_embed(self, channel, perpetrator_id: int) -> discord.Embed:
        """ Makes an embedded message for a transmutation action.
        :param channel: The context channel.
        :param perpetrator_id: The ID of the perpetrator of the transmutation. """

        timestamp = await utils.get_timestamp()

        transmutation_embed = discord.Embed(
            title="A Transmutation just happened in front of everyone's eyes!",
            timestamp=datetime.fromtimestamp(timestamp)
        )
        transmutation_embed.description = f"**<@{perpetrator_id}> transmutated themselves into something else! 🦥→💥→🐩**"
        transmutation_embed.color = discord.Color.green()

        transmutation_embed.set_thumbnail(url="https://thelanguagesloth.com/media/sloth_classes/Metamorph.png")
        transmutation_embed.set_footer(text=channel.guild, icon_url=channel.guild.icon.url)

        return transmutation_embed

    async def get_frogged_embed(self, channel, attacker_id: int, target_id: int) -> discord.Embed:
        """ Makes an embedded message for a frog action.
        :param channel: The context channel.
        :param attacker_id: The ID of the attacker.
        :param target_id: The ID of the target. """

        timestamp = await utils.get_timestamp()

        transmutation_embed = discord.Embed(
            title="A Prince(ss) rolled back Time!",
            timestamp=datetime.fromtimestamp(timestamp)
        )
        transmutation_embed.description = f"**<@{attacker_id}> frogged <@{target_id}>!  🦥→💥→🐸**"
        transmutation_embed.color = discord.Color.green()

        transmutation_embed.set_thumbnail(url="https://thelanguagesloth.com/media/sloth_classes/Metamorph.png")
        transmutation_embed.set_footer(text=channel.guild, icon_url=channel.guild.icon.url)

        return transmutation_embed


    @commands.command()
    @Player.skills_used(requirement=20)
    @Player.skill_on_cooldown(skill=Skill.THREE)
    @Player.user_is_class('metamorph')
    @Player.skill_mark()
    @Player.not_ready()
    async def mirror(self, ctx, target: discord.Member = None) -> None:
        """ Mirrors someone else's first skill.
        :param target: The person from whom to mirror the skill.

        * Cooldown: 1 day.
        * Skill cost: 50łł. """

        perpetrator = ctx.author

        if not target:
            return await ctx.send(f"**Please, inform a target, {perpetrator.mention}!**")

        # Do the magic