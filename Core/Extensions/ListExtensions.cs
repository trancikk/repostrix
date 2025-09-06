namespace Core.Extensions;

public static class ListExtensions
{
    private static readonly Random Random = new();

    public static T GetRandom<T>(this IList<T> list)
    {
        if (list == null || list.Count == 0)
            throw new InvalidOperationException("Cannot select a random item from an empty list.");

        var index = Random.Next(list.Count); // random index [0, Count)
        return list[index];
    }
}