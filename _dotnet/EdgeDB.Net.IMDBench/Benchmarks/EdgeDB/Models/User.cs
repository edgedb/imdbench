using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace EdgeDB.Net.IMDBench.Benchmarks.EdgeDB.Models
{
    internal sealed class User : HasImage
    {
        public string? Name { get; set; }
        
        public Review[]? LatestReviews { get; set; }
    }
}
