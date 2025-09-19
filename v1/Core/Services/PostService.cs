using Core.Dto.Asset;
using Core.Entity;
using Core.Extensions;
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

    public async Task<int> ChangePostStatus(Guid postId, PostStatus status)
    {
        var context = await dbContextFactory.CreateDbContextAsync();
        return await context.Posts.Where(post => post.Id == postId).ExecuteUpdateAsync(s =>
            s.SetProperty(post => post.Status, status));
    }

    public async Task<int> CancelPostAsync(Guid postId)
    {
        await using var context = await dbContextFactory.CreateDbContextAsync();
        var existingPost = await context.Posts.FindAsync(postId);
        if (existingPost is null) return 0;
        existingPost.Status = PostStatus.Canceled;
        await context.SaveChangesAsync();
        return 1;
    }

    public async Task<List<Post>> GetRandomPostsAsync()
    {
        await using var context = await dbContextFactory.CreateDbContextAsync();
        var randomPosts = await context.Posts.Where(p => p.Status == PostStatus.Pending)
            .GroupBy(p => p.SourceChatId)
            .Select(g => g.Select(x => x.Id).ToList().GetRandom())
            .ToListAsync();

        return await context.Posts.Where(p => p.Status == PostStatus.Pending)
            .Where(p => randomPosts.Contains(p.Id))
            .Include(p => p.Assets)
            .Include(p => p.SourceChat)
            .ThenInclude(c => c.TagetChannels)
            .ToListAsync();
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
            PublicUrl = assetDto.PublicUrl,
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