using Core.Dto.Asset;
using Core.Entity;
using Core.Services;
using Telegram.Bot;
using Telegram.Bot.Types;
using Telegram.Bot.Types.Enums;
using Chat = Core.Entity.Chat;

namespace Web.Bot;

public class Reposter(PostService postService, ChannelService channelService) : BackgroundService
{
    public async Task<string> GetFileUrlAsync(string fileId)
    {
        var file = await Bot.GetFile(fileId);
        return $"https://api.telegram.org/file/bot{Token}/{file.FilePath}";
    }

    private const string Token = "8085912035:AAEVtFDBhoDwqhYV9A5WFPqATa5R4vT1VqM";
    private TelegramBotClient Bot { get; set; } = new(Token);

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
                if (update.Message?.Text != null && update.Message.Text.Contains('/'))
                {
                    await HandleCommand(update.Message);
                }
                else
                {
                    await HandleMessage(update.Message!);
                }

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
        var text = msg.Text ?? msg.Caption ?? string.Empty;
        var chatId = msg.Chat.Id;
        var chatName = msg.Chat.Title;
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
            Text = text,
            SourceChatId = chatId
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

        asset.PublicUrl = await GetFileUrlAsync(asset.FileId);
        await postService.AddNewAssetAsync(asset);
        await Bot.SendMessage(chatId, "Post has been added!");
        // When we get a command, we react accordingly
    }

    async Task HandleCommand(Message msg)
    {
        var command = msg.Text!;
        var data = command.Split('/');
        var parsedCommand = data[1];
        if (parsedCommand.Contains('@'))
        {
            parsedCommand = parsedCommand.Split("@")[0];
        }

        if (parsedCommand.Contains("register"))
        {
            var chatId = msg.Chat.Id;
            var channelId = parsedCommand.Split(' ').ElementAtOrDefault(1);
            var chatName = msg.Chat.Title ?? string.Empty;
            if (channelId is null)
            {
                await Bot.SendMessage(chatId, "Please provide channel id");
            }
            else
            {
                var result = long.TryParse(channelId, out var parsedChannelId);
                if (!result)
                {
                    await Bot.SendMessage(chatId, "Channel ID should be a number!");
                }
                else
                {
                    await channelService.RegisterNewChannelAsync(chatId, parsedChannelId, chatName);
                    await Bot.SendMessage(chatId, $"Channel {parsedChannelId} registered!");
                }
            }

            {
            }
        }

        await Task.CompletedTask;
    }

    public async Task SendPost(Post post, ICollection<Channel> channels)
    {
        foreach (var channel in channels)
        {
            foreach (var asset in post.Assets)
            {
                switch (asset.AssetType)
                {
                    case AssetType.Image:
                    {
                        await Bot.SendPhoto(channel.ChannelId, asset.FileId, caption: post.Text);
                        break;
                    }
                    case AssetType.Video:
                    {
                        await Bot.SendVideo(channel.ChannelId, asset.FileId, caption: post.Text);
                        break;
                    }
                    case AssetType.Animation:
                    {
                        await Bot.SendAnimation(channel.ChannelId, asset.FileId, caption: post.Text);
                        break;
                    }
                }
            }
        }
    }
}