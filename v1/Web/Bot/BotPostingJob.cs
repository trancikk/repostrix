using Core.Services;
using Quartz;

namespace Web.Bot;

public class BotPostingJob(BotService botService, PostService postService) : IJob
{
    public async Task Execute(IJobExecutionContext context)
    {
        var randomPosts = await postService.GetRandomPostsAsync();
        foreach (var randomPost in randomPosts)
        {
            await botService.SendPostAsync(randomPost);
        }
    }
}