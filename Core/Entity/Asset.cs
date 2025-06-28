using System.ComponentModel.DataAnnotations;

namespace Core.Entity;

public class Asset
{
    public Guid Id { get; set; }
    public string? FileId { get; set; }
    public AssetType AssetType { get; set; }
    public Post Post { get; set; }
    public Guid PostId { get; set; }
    public string? MediaGroupId { get; set; }
}

public enum AssetType
{
    Image,
    Video,
    Animation
}