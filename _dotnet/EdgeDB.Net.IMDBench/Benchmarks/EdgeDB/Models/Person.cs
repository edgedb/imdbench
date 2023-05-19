using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace EdgeDB.Net.IMDBench.Benchmarks.EdgeDB.Models
{
    internal class Person : HasImage
    {
        public string? Bio { get; set; }

        public string? FirstName { get; set; }
        public string? FullName { get; set; }
        public string? LastName { get; set; }
        public string? MiddleName { get; set; }

        [EdgeDBProperty("@list_order")]
        public long ListOrder { get; set; }
        
        public Movie[]? ActedIn { get; set; }
        public Movie[]? Directed { get; set; }
    }
}
