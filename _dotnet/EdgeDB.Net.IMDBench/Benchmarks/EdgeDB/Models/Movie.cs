using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace EdgeDB.Net.IMDBench.Benchmarks.EdgeDB.Models
{
    internal sealed class Movie : HasImage
    {
        public Person[]? Crew { get; set; }
        public Person[]? Directors { get; set; }
        public double AvgRating { get; set; }
        public string? Description { get; set; }
        public string? Title { get; set; }
        public long Year { get; set; }

        public Review[]? Reviews { get; set; }
    }
}
