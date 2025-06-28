using Core.Dto.Asset;
using Core.Entity;
using Microsoft.EntityFrameworkCore;

namespace Core.Services;

public class PostService(IDbContextFactory<AppDbContext> dbContextFactory)
{
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
        var context = await dbContextFactory.CreateDbContextAsync();
        var mediaGroupId = assetDto.MediaGroupId;

        var post = await FindPostByMediaGroupId(assetDto.MediaGroupId, context)
                   ?? AddNewPost(context);
        post.Text = assetDto.Text;
        var asset = new Asset
        {
            AssetType = assetDto.AssetType,
            MediaGroupId = assetDto.MediaGroupId,
            FileId = assetDto.FileId,
            Post = post
        };
        context.Assets.Add(asset);
        await context.SaveChangesAsync();
        return asset;
    }

    public async Task<Asset> AddNewAssetAsync(Asset asset)
    {
        var context = await dbContextFactory.CreateDbContextAsync();
        context.Assets.Add(asset);
        await context.SaveChangesAsync();
        return asset;
    }

    private static Post AddNewPost(AppDbContext context)
    {
        var post = new Post();
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