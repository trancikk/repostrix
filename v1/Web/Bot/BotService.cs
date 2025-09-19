using Core;
using Core.Entity;
using Core.Services;

namespace Web.Bot;

public class BotService(Reposter reposter, PostService postService, ChannelService channelService)
{
    public async Task<string> GetFileUrlAsync(string fileId)
    {
        return await reposter.GetFileUrlAsync(fileId);
    }

    public async Task SendPostAsync(Post post)
    {
        var channels = await channelService.FindTargetChannelsAsync(post.SourceChat.ChatId);
        await reposter.SendPost(post, channels);
        await postService.ChangePostStatus(post.Id, PostStatus.Posted);
    }

    public async Task SendPostAsync(Guid postId, long chatId)
    {
        var existingPost = await postService.FindPostById(postId);
        if (existingPost is not null)
        {
            await SendPostAsync(existingPost);
        }
    }
}