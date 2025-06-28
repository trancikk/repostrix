using Core.Entity;
using Microsoft.EntityFrameworkCore;

namespace Core.Services;

public class ChannelService(IDbContextFactory<AppDbContext> dbContextFactory)
{
    public async Task<Chat?> FindChatByChatId(long chatId, AppDbContext context)
    {
        return await context.Chats.Where(c => chatId == c.ChatId).FirstOrDefaultAsync();
    }
    
    public async Task<ICollection<Channel>> FindTargetChannelsAsync(long chatId)
    {
        var context = await dbContextFactory.CreateDbContextAsync();
        return await context.Chats.Include(c => c.TagetChannels)
            .Where(c => c.ChatId == chatId)
            .SelectMany(c => c.TagetChannels)
            .ToListAsync();
    }

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