using System.ComponentModel.DataAnnotations;

namespace Core.Entity;

public class Channel
{
    [Required] public Guid Id { get; set; }
    public long ChannelId { get; set; }
    public Chat SourceChat { get; set; }
    public Guid SourceChatId { get; set; }
}