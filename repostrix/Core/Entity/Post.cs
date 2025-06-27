namespace Core.Entity;

public class Post
{
    public Guid Id { get; set; }
    public string? Text { get; set; }
    public int? MediaGroupId { get; set; }
}