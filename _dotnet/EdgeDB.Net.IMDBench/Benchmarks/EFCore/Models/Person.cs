using System;
using System.Collections.Generic;

namespace EdgeDB.Net.IMDBench.Benchmarks.EFCore.Models;

public partial class Person
{
    public int Id { get; set; }

    public string FirstName { get; set; } = null!;

    public string MiddleName { get; set; } = null!;

    public string LastName { get; set; } = null!;

    public string Image { get; set; } = null!;

    public string Bio { get; set; } = null!;

    public virtual ICollection<Actor> Actors { get; } = new List<Actor>();

    public virtual ICollection<Director> Directors { get; } = new List<Director>();
}
