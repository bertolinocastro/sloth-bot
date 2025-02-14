import discord
from discord.ext import commands
import os
from extra.useful_variables import rules
from extra import utils
from datetime import datetime
from discord_slash import cog_ext, SlashContext
from discord_slash.model import SlashCommandPermissionType
from discord_slash.utils.manage_commands import create_option, create_choice, create_permission, create_multi_ids_permission


admin_role_id = int(os.getenv('ADMIN_ROLE_ID'))
owner_role_id = int(os.getenv('OWNER_ROLE_ID'))
mod_role_id = int(os.getenv('MOD_ROLE_ID'))
allowed_roles = [owner_role_id, admin_role_id, mod_role_id]

guild_ids = [int(os.getenv('SERVER_ID'))]

class Embeds(commands.Cog):
    '''
    A cog related to embedded messages.
    '''

    def __init__(self, client):
        self.client = client

    # Events
    @commands.Cog.listener()
    async def on_ready(self):
        print('Embeds cog is ready.')

    # Sends an embedded message
    @commands.command(aliases=['emb'])
    @commands.has_any_role(*allowed_roles)
    async def embed(self, ctx):
        """ (MOD) Sends an embedded message. """

        await ctx.message.delete()
        if len(ctx.message.content.split()) < 2:
            return await ctx.send('You must inform all parameters!')

        msg = ctx.message.content.split(ctx.message.content.split(' ')[0], 1)
        embed = discord.Embed(description=msg[1], colour=discord.Colour.dark_green())
        await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="embed", description="(MOD) Makes an improved embedded message", default_permission=False,
                options=[
                    create_option(name="description", description="Description.", option_type=3, required=False),
                    create_option(name="title", description="Title.", option_type=3, required=False),
                    create_option(name="timestamp", description="If timestamp is gonna be shown.", option_type=5, required=False),
                    create_option(name="url", description="URL for the title.", option_type=3, required=False),
                    create_option(name="thumbnail", description="Thumbnail for the embed.", option_type=3, required=False),
                    create_option(name="image", description="Display image.", option_type=3, required=False),
                    create_option(name="color", description="The color for the embed.", option_type=3, required=False,
                        choices=[
                            create_choice(name="Blue", value="0011ff"), create_choice(name="Red", value="ff0000"),
                            create_choice(name="Green", value="00ff67"), create_choice(name="Yellow", value="fcff00"),
                            create_choice(name="Black", value="000000"), create_choice(name="White", value="ffffff"),
                            create_choice(name="Orange", value="ff7100"), create_choice(name="Brown", value="522400"),
                            create_choice(name="Purple", value="380058"),
                        ])
                ], guild_ids=guild_ids,
                permissions={
                    guild_ids[0]: [
                        create_permission(int(os.getenv('COSMOS_ID')), SlashCommandPermissionType.USER, True),
                        create_permission(owner_role_id, SlashCommandPermissionType.ROLE, True),
                        create_permission(admin_role_id, SlashCommandPermissionType.ROLE, True),
                        create_permission(mod_role_id, SlashCommandPermissionType.ROLE, True)
                    ]
                })
    async def _embed(self, ctx, **fields):

        # Checks if there's a timestamp and sorts time
        if (timestamp := fields.get('timestamp')) is not None:
            if timestamp:
                fields['timestamp'] = await utils.parse_time()
            else:
                fields.pop('timestamp', None)

        description = fields.get('description')
        fields['description'] = description.replace(r'\n', '\n')

        if (color := fields.get('color')) is not None:
            if color:
                fields['color'] = int(color, 16)
            else:
                fields.pop('color', None)

        emb = discord.Embed(**{k:v for k, v in fields.items() if k not in ['thumbnail', 'image']})

        if (thumbnail := fields.get('thumbnail')) is not None:
            if thumbnail:
                emb.set_thumbnail(url=thumbnail)
            else:
                fields.pop('thumbnail', None)

        if (image := fields.get('image')) is not None:
            if image:
                emb.set_image(url=image)
            else:
                fields.pop('image', None)


        await ctx.send(embeds=[emb])

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def embed_join_us(self, ctx):
        '''
        (ADM) Sends the join-us embedded message.
        '''
        await ctx.message.delete()
        embed = discord.Embed(title="Join our Staff!",
                              description="```We depend on people like you to keep this community running, and any help is welcome. if you feel like you would like to contribute apply to any of the positions below: ```",
                              url='https://docs.google.com/forms/d/1H-rzl9AKgfH1WuKN7nYAW-xJx411Q4-HxfPXuPUFQXs',
                              colour=2788104, timestamp=ctx.message.created_at)
        embed.add_field(name=":police_officer: Become a Moderator",
                        value='Would you like to help us by mediating conflicts in the voice channels and becoming an official part of our staff? [Click here to apply](https://docs.google.com/forms/d/e/1FAIpQLSfFXh7GrwftdDro6iqtuw9W4-G2dZfhqvCcEB1jQacQMdNJtA/viewform)',
                        inline=False)
        embed.add_field(name=":man_teacher: Become a Teacher",
                        value="Do you want to teach on our server? Since this community is made by people like you, we are always looking for people to join our ranks ! Teach your native language here ! [Click here to apply](https://docs.google.com/forms/d/1H-rzl9AKgfH1WuKN7nYAW-xJx411Q4-HxfPXuPUFQXs)",
                        inline=False)
        embed.add_field(name="All positions are unsalaried, for professional enquiry please get in touch.",
                        value="```Other available positions !```", inline=False)
        embed.add_field(name=":musical_note:  Karaoke Night Organizer",
                        value="We are looking for someone to take over the **Karaoke Night** event, A 40 minute per week event that would unite people in a voice chat to sing karaoke.You would have to organize and screenshare karaoke songs on a given day of the week. To anyone interested in this position please contact <@423829836537135108> privately.",
                        inline=False)
        embed.add_field(name=":speaking_head: Moderator in the Debate Club",
                        value="We are searching for someone willing to moderate debates impartially once a week, Must have command of the English language and over 16 years old.",
                        inline=False)
        embed.add_field(name="Apply now!", value="Or Later?", inline=True)
        embed.add_field(name="Apply Tomorrow!", value="Or after tomorrow?", inline=True)
        embed.set_footer(text='Cosmos',
                         icon_url='https://cdn.discordapp.com/avatars/423829836537135108/da15dea5017edf5567e531fc6b97f935.jpg?size=2048')
        embed.set_thumbnail(url='https://i.imgur.com/bFfenC9.png')
        embed.set_image(url='https://cdn.discordapp.com/attachments/668049600871006208/689196815509094403/unnamed.png')
        embed.set_author(name='The Language Sloth', url='https://discordapp.com',
                         icon_url='https://cdn.discordapp.com/attachments/562019489642709022/676564701399744512/jungle_2.gif')
        await ctx.send(embed=embed)


def setup(client):
    client.add_cog(Embeds(client))
