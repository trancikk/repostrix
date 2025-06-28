using Core.Entity;
using Core.Services;

namespace Web.Bot;

public class BotService(Reposter reposter, PostService postService, ChannelService channelService)
{
    public async Task<string> GetFileUrlAsync(string fileId)
    {
        return await reposter.GetFileUrlAsync(fileId);
    }

    public async Task SendPostAsync(Guid postId, long chatId)
    {
        var existingPost = await postService.FindPostById(postId);
        var channels = await channelService.FindTargetChannelsAsync(chatId);
        if (existingPost is not null)
        {
            await reposter.SendPost(existingPost, channels);
        }

        ;
    }
}