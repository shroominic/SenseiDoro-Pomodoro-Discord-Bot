from timer import Timer
import asyncio
import json


# Pomodoro Session Class
class Session:
    def __init__(self, guild, category=None, work_time=30, pause_time=5, number_sessions=4):
        self.name = f"🍅 - [{work_time} | {pause_time}]"
        self.category = category
        self.guild = guild
        # channel enums
        self.start_button = "START SESSION"
        self.session_chat = "session_chat"
        self.lobby = "Lobby"
        # channels
        self.text_channel = None
        # todo hidden self.config_channel
        self.lobby_channel = None
        self.work_channel = None
        # timer settings
        self.number_sessions = number_sessions
        self.pause_time = pause_time
        self.work_time = work_time
        self.session_count = 0
        self.timer_message = None
        self.timer = None
        # todo statistics

    async def create_environment(self):
        # create session category
        self.category = await self.guild.create_category_channel(self.name)
        # create initial channels
        self.text_channel = await self.guild.create_text_channel(self.session_chat, category=self.category)
        self.lobby_channel = await self.guild.create_voice_channel(self.lobby, category=self.category)
        self.work_channel = await self.guild.create_voice_channel(self.start_button, category=self.category)
        # send serialization of session as message
        await self.text_channel.send(f"Session config: {self.to_json()}")

    async def setup_old_environment(self):
        for vc in self.category.voice_channels:
            channel_name = vc.name
            if self.lobby in channel_name:
                self.lobby_channel = vc
            if self.start_button in channel_name or "Session" in channel_name:
                self.work_channel = vc
        for tc in self.category.text_channels:
            channel_name = tc.name
            if self.session_chat in channel_name:
                self.text_channel = tc
        await self.reset_session()

    def increase_session_count(self):
        self.session_count += 1

    async def display_timer(self, time_left):
        info_timer_string = f"Time left: {time_left}"
        await self.timer_message.edit(content=info_timer_string)

    #   starting a session
    async def init_timer(self):
        self.timer = Timer(
            self.work_time,
            self.pause_time,
            self.number_sessions,
            self.display_timer,
            self.next_session,
            self.pause_session,
            self.reset_session)
        # start session timer
        asyncio.create_task(self.timer.run_session())

    async def start_session(self, member):
        # init session
        await self.text_channel.send("Session has started!")
        await member.edit(mute=True)
        self.timer_message = await self.text_channel.send(f"Time left: {self.work_time}")
        # the timer manages the whole session
        await self.init_timer()

    # session navigation
    async def next_session(self):
        self.increase_session_count()
        # TODO: Closed Permission for work_channel
        # rename session
        await self.work_channel.edit(name=f"Session [ {self.session_count} | {self.number_sessions} ]")
        # move all members from lobby to session
        for member in self.lobby_channel.members:
            await member.move_to(self.work_channel)
            await member.edit(mute=True)

    async def pause_session(self):
        # move and unmute all waiting members
        for member in self.work_channel.members:
            await member.move_to(self.lobby_channel)
            await member.edit(mute=False)
        # some chill quote
        await self.work_channel.edit(name="dude ... relax")

    async def reset_session(self):
        # move all back to lobby
        for member in self.work_channel.members:
            await member.move_to(self.lobby_channel)
            await member.edit(mute=False)
        # reset stats
        self.session_count = 0
        # start button
        await self.work_channel.edit(name=self.start_button)

    # deletes the category and all channels off self
    async def dispose(self):
        for vc in self.category.voice_channels:
            channel_id = vc.id
            asyncio.create_task(self.guild.get_channel(channel_id).delete())
        for tc in self.category.text_channels:
            channel_id = tc.id
            asyncio.create_task(self.guild.get_channel(channel_id).delete())
        asyncio.create_task(self.category.delete())

    # serializes important information to json string
    def to_json(self):
        return json.dumps({
            "work_time": self.work_time,
            "pause_time": self.pause_time,
            "number_sessions": self.number_sessions
        })