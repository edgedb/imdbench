using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace EdgeDB.Net.IMDBench.Benchmarks.EdgeDB.Models
{
    internal sealed class Review
    {
        public User? Author { get; set; }
        public Movie? Movie { get; set; }
        public string? Body { get; set; }
        public DateTime CreationTime { get; set; }
        public long Rating { get; set; }
    }
}
