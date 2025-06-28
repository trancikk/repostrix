using Core.Services;
using Quartz;

namespace Web.Bot;

public class BotPostingJob(BotService botService, PostService postService): IJob
{
    public async Task Execute(IJobExecutionContext context)
    {
        var randomPost = await postService.GetRandomPostAsync();
        if (randomPost is not null)
        {
            await botService.SendPostAsync(randomPost);
        }
    }
}