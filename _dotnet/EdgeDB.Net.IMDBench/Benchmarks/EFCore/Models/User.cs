using System;
using System.Collections.Generic;

namespace EdgeDB.Net.IMDBench.Benchmarks.EFCore.Models;

public partial class User
{
    public int Id { get; set; }

    public string Name { get; set; } = null!;

    public string Image { get; set; } = null!;

    public virtual ICollection<Review> Reviews { get; } = new List<Review>();
}
