using Core.Entity;
using Microsoft.EntityFrameworkCore;

namespace Core.Services;

public class ChannelService(IDbContextFactory<AppDbContext> dbContextFactory)
{
    public async Task<Channel> RegisterNewChannelAsync(long chatId, long channelId)
    {
        var context = await dbContextFactory.CreateDbContextAsync();
        var existingChat = await context.Chats.FirstOrDefaultAsync(c => c.ChatId == chatId);
        var channel = new Channel
        {
            ChannelId = channelId,
        };
        if (existingChat != null)
        {
            channel.SourceChat = existingChat;
        }
        else
        {
            var chat = new Chat
            {
                ChatId = chatId,
                TagetChannels = [channel]
            };
            context.Chats.Add(chat);
            await context.SaveChangesAsync();
        }

        return channel;
    }
}