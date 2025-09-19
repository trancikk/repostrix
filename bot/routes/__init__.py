from . import channel, post

all_routes = [
    channel.channel_router,
    post.post_router,
]

_all_commands = [
    channel.channel_commands,
]

all_commands = [item for l in _all_commands for item in l]
