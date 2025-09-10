using System.Diagnostics;
using Core;
using Core.Services;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Web.Bot;
using Web.Models;

namespace Web.Controllers;

public class HomeController(
    AppDbContext context,
    ILogger<HomeController> logger,
    PostService postService,
    ChannelService channelService,
    BotService botService
)
    : Controller
{
    private readonly ILogger<HomeController> _logger;

    [HttpGet]
    public async Task<IActionResult> SendPost(Guid postId, long chatId)
    {
        await botService.SendPostAsync(postId, chatId);
        return RedirectToAction("Index");
    }

    public async Task<IActionResult> CancelPost(Guid postId)
    {
        await postService.CancelPostAsync(postId);
        return RedirectToAction("Index");
    }

    public async Task<IActionResult> Index()
    {
        var channelsWithPosts = await context.Chats
            .Include(c => c.TagetChannels)
            .Include(c => c.Posts)
            .ThenInclude(p => p.Assets)
            .ToListAsync();
        return View(channelsWithPosts);
    }

    public IActionResult Privacy()
    {
        return View();
    }

    [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
    public IActionResult Error()
    {
        return View(new ErrorViewModel { RequestId = Activity.Current?.Id ?? HttpContext.TraceIdentifier });
    }
}