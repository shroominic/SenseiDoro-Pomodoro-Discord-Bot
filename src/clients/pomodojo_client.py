from session import Session
from discord.ext import commands


# Bot Client Class
class PomoDojoClient(commands.Bot):
    def __init__(self, *args, **options):
        super(PomoDojoClient, self).__init__(*args, **options)
        # stores all open sessions
        self.sessions: [Session] = []
