namespace Core.Entity;

public class Post
{
    public Guid Id { get; set; }
    public string? Text { get; set; }
    public string? MediaGroupId { get; set; }
    public ICollection<Asset> Assets { get; set; } = [];
    public PostStatus Status { get; set; } = PostStatus.Pending;
}

public enum PostStatus
{
    Pending,
    Canceled,
    Posted
}