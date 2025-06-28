using Core.Entity;
using Microsoft.EntityFrameworkCore;

namespace Core;

public class AppDbContext(DbContextOptions<AppDbContext> options) : DbContext(options)
{
    public DbSet<Post> Posts { get; set; }
    public DbSet<Asset> Assets { get; set; }
}