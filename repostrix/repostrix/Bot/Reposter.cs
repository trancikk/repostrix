using System.Text;
using Core.Dto.Asset;
using Core.Entity;
using Core.Services;
using Telegram.Bot;
using Telegram.Bot.Types;
using Telegram.Bot.Types.Enums;

namespace repostrix.Bot;

public class Reposter(PostService postService) : BackgroundService
{
    public TelegramBotClient Bot { get; set; } = new("8085912035:AAEVtFDBhoDwqhYV9A5WFPqATa5R4vT1VqM");

    protected override Task ExecuteAsync(CancellationToken stoppingToken)
    {
        using var cts = new CancellationTokenSource();
        Bot.StartReceiving(
            updateHandler: HandleUpdate,
            errorHandler: HandleError,
            cancellationToken: cts.Token
        );
        return Task.CompletedTask;
    }

    async Task HandleUpdate(ITelegramBotClient _, Update update, CancellationToken cancellationToken)
    {
        switch (update.Type)
        {
            // A message was received
            case UpdateType.Message:
                await HandleMessage(update.Message!);
                break;
        }
    }

    async Task HandleError(ITelegramBotClient _, Exception exception, CancellationToken cancellationToken)
    {
        await Console.Error.WriteLineAsync(exception.Message);
    }

    async Task HandleMessage(Message msg)
    {
        var user = msg.From;
        var text = msg.Text ?? string.Empty;
        var chatId = msg.Chat.Id;
        if (user is null)
            return;

        // Print to console
        Console.WriteLine($"{user.FirstName} wrote {text}");
        var video = msg.Video;
        var photo = msg.Photo;
        var mediaGroupId = msg.MediaGroupId;
        var animation = msg.Animation;
        var audio = msg.Audio;
        var caption = msg.Caption;

        var asset = new CreateAssetDto
        {
            MediaGroupId = mediaGroupId,
        };

        if (video is not null)
        {
            asset.AssetType = AssetType.Video;
            asset.FileId = video.FileId;
        }

        if (photo is not null)
        {
            asset.AssetType = AssetType.Image;
            asset.FileId = photo.Last().FileId;
        }

        if (animation is not null)
        {
            asset.AssetType = AssetType.Animation;
            asset.FileId = animation.FileId;
        }

        await postService.AddNewAssetAsync(asset);
        // When we get a command, we react accordingly
        if (text.StartsWith("/"))
        {
            await HandleCommand(chatId, text);
        }
    }

    async Task HandleCommand(long userId, string command)
    {
        var data = command.Split();
        var parsedCommand = data[0];
        if (parsedCommand.Contains('@'))
        {
            parsedCommand = parsedCommand.Split("@")[0];
        }

        await Task.CompletedTask;
    }
}