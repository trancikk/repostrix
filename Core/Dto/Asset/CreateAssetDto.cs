using Core.Entity;

namespace Core.Dto.Asset;

public class CreateAssetDto
{
    public AssetType AssetType { get; set; }
    public string FileId { get; set; }
    public string? MediaGroupId { get; set; }
    public string? Text { get; set; }
}