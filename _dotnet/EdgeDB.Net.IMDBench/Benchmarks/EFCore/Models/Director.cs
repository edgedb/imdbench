using System;
using System.Collections.Generic;

namespace EdgeDB.Net.IMDBench.Benchmarks.EFCore.Models;

public partial class Director
{
    public int Id { get; set; }

    public int? ListOrder { get; set; }

    public int PersonId { get; set; }

    public int MovieId { get; set; }

    public virtual Movie Movie { get; set; } = null!;

    public virtual Person Person { get; set; } = null!;
}
