using System.ComponentModel.DataAnnotations;

namespace Core.Entity;

public class Chat
{
    [Required] public Guid Id { get; set; }
    public long ChatId { get; set; }
    public ICollection<Channel> TagetChannels { get; set; } = [];
    public ICollection<Post> Posts { get; set; } = [];
}