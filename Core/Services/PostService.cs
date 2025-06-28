using Core.Dto.Asset;
using Core.Entity;
using Microsoft.EntityFrameworkCore;

namespace Core.Services;

public class PostService(IDbContextFactory<AppDbContext> dbContextFactory, ChannelService channelService)
{
    private readonly SemaphoreSlim _semaphoreSlim = new(1);

    public async Task<Post?> FindPostById(Guid postId)
    {
        var context = await dbContextFactory.CreateDbContextAsync();
        return await context.Posts.Include(p => p.Assets)
            .Where(p => p.Id == postId)
            .FirstOrDefaultAsync();
    }

    public async Task<Post?> FindPostByMediaGroupId(string? mediaGroupId)
    {
        var context = await dbContextFactory.CreateDbContextAsync();
        return await FindPostByMediaGroupId(mediaGroupId, context);
    }

    private static async Task<Post?> FindPostByMediaGroupId(string? mediaGroupId, AppDbContext context)
    {
        if (mediaGroupId is null or "") return null;
        return await context.Posts.FirstOrDefaultAsync(p => p.MediaGroupId == mediaGroupId);
    }

    public async Task<Asset> AddNewAssetAsync(CreateAssetDto assetDto)
    {
        // await _semaphoreSlim.WaitAsync();
        await using var context = await dbContextFactory.CreateDbContextAsync();

        var existingChat = await channelService.FindChatByChatId(assetDto.SourceChatId, context);

        if (existingChat == null) throw new ArgumentException("Chat ID doesn't exist");
        var post = await FindPostByMediaGroupId(assetDto.MediaGroupId, context)
                   ?? AddNewPost(context, existingChat);
        post.Text = assetDto.Text;
        post.MediaGroupId = assetDto.MediaGroupId;
        var asset = new Asset
        {
            AssetType = assetDto.AssetType,
            MediaGroupId = assetDto.MediaGroupId,
            FileId = assetDto.FileId,
            Post = post,
        };
        context.Assets.Add(asset);
        await context.SaveChangesAsync();
        // _semaphoreSlim.Release();
        return asset;

        //TODO rework
    }

    public async Task<Asset> AddNewAssetAsync(Asset asset)
    {
        var context = await dbContextFactory.CreateDbContextAsync();
        context.Assets.Add(asset);
        await context.SaveChangesAsync();
        return asset;
    }

    private static Post AddNewPost(AppDbContext context, Chat chat)
    {
        var post = new Post
        {
            SourceChat = chat
        };
        context.Posts.Add(post);
        return post;
    }

    public async Task<Post> AddNewPost(Post post)
    {
        var context = await dbContextFactory.CreateDbContextAsync();
        context.Posts.Add(post);
        await context.SaveChangesAsync();
        return post;
    }
}