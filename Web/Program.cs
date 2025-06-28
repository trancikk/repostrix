using Core.Extensions;
using Microsoft.AspNetCore.Builder;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Quartz;
using Quartz.Impl;
using Web.Bot;


var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddControllersWithViews();
builder.Services.ConfigurePersistenceServices(builder.Configuration, builder.Environment.IsDevelopment());
builder.Services.AddHostedService<Reposter>();
builder.Services.AddScoped<Reposter>();
builder.Services.AddScoped<BotService>();

// Add Quartz services
builder.Services.AddQuartz(q =>
{
    // Register the job
    q.AddJob<BotPostingJob>(opts => opts.WithIdentity("BotPostingJob"));

    // Create a trigger for hourly execution
    q.AddTrigger(opts => opts
            .ForJob("BotPostingJob")
            .WithIdentity("MyHourlyJob-trigger")
            .WithCronSchedule("0 0 * ? * * *") // Every hour
    );
});
builder.Services.AddQuartzHostedService(q => q.WaitForJobsToComplete = true);

var app = builder.Build();

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Home/Error");
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}

app.UseHttpsRedirection();
app.UseRouting();

app.UseAuthorization();

app.MapStaticAssets();

app.MapControllerRoute(
        name: "default",
        pattern: "{controller=Home}/{action=Index}/{id?}")
    .WithStaticAssets();


app.Run();