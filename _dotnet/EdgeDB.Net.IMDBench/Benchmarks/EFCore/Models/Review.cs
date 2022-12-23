using System;
using System.Collections.Generic;

namespace EdgeDB.Net.IMDBench.Benchmarks.EFCore.Models;

public partial class Review
{
    public int Id { get; set; }

    public string Body { get; set; } = null!;

    public int Rating { get; set; }

    public DateTime CreationTime { get; set; }

    public int AuthorId { get; set; }

    public int MovieId { get; set; }

    public virtual User Author { get; set; } = null!;

    public virtual Movie Movie { get; set; } = null!;
}
