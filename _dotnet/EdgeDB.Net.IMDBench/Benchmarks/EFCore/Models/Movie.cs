using Microsoft.EntityFrameworkCore;
using System;
using System.Collections.Generic;

namespace EdgeDB.Net.IMDBench.Benchmarks.EFCore.Models;

public partial class Movie
{
    public int Id { get; set; }

    public string Image { get; set; } = null!;

    public string Title { get; set; } = null!;

    public int Year { get; set; }

    public string Description { get; set; } = null!;

    public virtual ICollection<Actor> Actors { get; set; } = new List<Actor>();

    public virtual ICollection<Director> Directors { get; set; } = new List<Director>();

    public virtual ICollection<Review> Reviews { get; set; } = new List<Review>();

    public double? AvgerageRating { get; set; }
}

public static class MovieHelpers
{
    public static IQueryable<Movie> ApplyAverageRating(this IQueryable<Movie> querable)
    {
        return querable
            .Select(x => new Movie
            {
                Actors = x.Actors,
                Description = x.Description,
                Directors = x.Directors,
                Id = x.Id,
                Image = x.Image,
                Reviews = x.Reviews,
                Title = x.Title,
                Year = x.Year,
                AvgerageRating = x.Reviews.Any() ? x.Reviews.Average(y => y.Rating) : null
            });
    }

    public static void ApplyAverageRating(this IEnumerable<Movie> movie)
    {
        foreach(var m in movie)
        {
            if(m.Reviews.Any())
                m.AvgerageRating = m.Reviews.Average(x => x.Rating);
        }
    }
}