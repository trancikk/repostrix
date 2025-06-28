using Core.Services;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;

namespace Core.Extensions;

public static class PersistenceServicesRegistration
{
    public static IServiceCollection ConfigurePersistenceServices(this IServiceCollection services,
        IConfiguration configuration, bool isDevelopment = true)
    {
        if (isDevelopment)
        {
            services.AddDbContextPool<AppDbContext>((serviceProvider, options) =>
                options
                    .EnableDetailedErrors()
                    .EnableSensitiveDataLogging()
                    .UseNpgsql(
                        configuration.GetConnectionString("Default")));

            services.AddDbContextFactory<AppDbContext>((serviceProvider, options) =>
                options
                    .EnableDetailedErrors()
                    .EnableSensitiveDataLogging()
                    .UseNpgsql(
                        configuration.GetConnectionString("Default")));
        }
        else
        {
            services.AddDbContextPool<AppDbContext>((serviceProvider, options) =>
            {
                options.UseNpgsql(
                    Environment.GetEnvironmentVariable("AZURE_SQL_CONNECTIONSTRING"));
            });

            services.AddDbContextFactory<AppDbContext>((serviceProvider, options) =>
            {
                options.UseNpgsql(
                    Environment.GetEnvironmentVariable("AZURE_SQL_CONNECTIONSTRING"));
            });
        }
        services.AddScoped<PostService>();
        services.AddSingleton<PostService>();
        services.AddSingleton<ChannelService>();

        return services;
    }
}