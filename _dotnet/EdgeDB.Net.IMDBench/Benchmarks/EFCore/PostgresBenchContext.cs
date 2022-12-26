using System;
using System.Collections.Generic;
using EdgeDB.Net.IMDBench.Benchmarks.EFCore.Models;
using Microsoft.EntityFrameworkCore;
using Microsoft.EntityFrameworkCore.Diagnostics;
using Microsoft.Extensions.Caching.Memory;

namespace EdgeDB.Net.IMDBench.Benchmarks.EFCore;

public partial class PostgresBenchContext : DbContext
{
    private readonly int _port;
    private readonly string _host;

    public PostgresBenchContext(string host, int port)
    {
        _host = host;
        _port = port;
    }

    public PostgresBenchContext(DbContextOptions<PostgresBenchContext> options)
        : base(options)
    {
        _host = "localhost";
        _port = 15432;
    }

    public virtual DbSet<Actor> Actors { get; set; }

    public virtual DbSet<Director> Directors { get; set; }

    public virtual DbSet<Movie> Movies { get; set; }

    public virtual DbSet<Person> Persons { get; set; }

    public virtual DbSet<Review> Reviews { get; set; }

    public virtual DbSet<User> Users { get; set; }

    protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
        => optionsBuilder
            .UseNpgsql($"Host={_host};Port={_port};Database=postgres_bench;User ID=postgres_bench;");
    
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Actor>(entity =>
        {
            entity.HasKey(e => e.Id).HasName("actors_pkey");

            entity.ToTable("actors");

            entity.HasIndex(e => e.MovieId, "actors_movie_index");

            entity.HasIndex(e => e.PersonId, "actors_person_index");

            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.ListOrder).HasColumnName("list_order");
            entity.Property(e => e.MovieId).HasColumnName("movie_id");
            entity.Property(e => e.PersonId).HasColumnName("person_id");

            entity.HasOne(d => d.Movie).WithMany(p => p.Actors)
                .HasForeignKey(d => d.MovieId)
                .OnDelete(DeleteBehavior.ClientSetNull)
                .HasConstraintName("actors_movie_id_fkey");

            entity.HasOne(d => d.Person).WithMany(p => p.Actors)
                .HasForeignKey(d => d.PersonId)
                .OnDelete(DeleteBehavior.ClientSetNull)
                .HasConstraintName("actors_person_id_fkey");
        });

        modelBuilder.Entity<Director>(entity =>
        {
            entity.HasKey(e => e.Id).HasName("directors_pkey");

            entity.ToTable("directors");

            entity.HasIndex(e => e.MovieId, "directors_movie_index");

            entity.HasIndex(e => e.PersonId, "directors_person_index");

            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.ListOrder).HasColumnName("list_order");
            entity.Property(e => e.MovieId).HasColumnName("movie_id");
            entity.Property(e => e.PersonId).HasColumnName("person_id");

            entity.HasOne(d => d.Movie).WithMany(p => p.Directors)
                .HasForeignKey(d => d.MovieId)
                .OnDelete(DeleteBehavior.ClientSetNull)
                .HasConstraintName("directors_movie_id_fkey");

            entity.HasOne(d => d.Person).WithMany(p => p.Directors)
                .HasForeignKey(d => d.PersonId)
                .OnDelete(DeleteBehavior.ClientSetNull)
                .HasConstraintName("directors_person_id_fkey");
        });

        modelBuilder.Entity<Movie>(entity =>
        {
            entity.HasKey(e => e.Id).HasName("movies_pkey");

            entity.ToTable("movies");

            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.Description).HasColumnName("description");
            entity.Property(e => e.Image).HasColumnName("image");
            entity.Property(e => e.Title).HasColumnName("title");
            entity.Property(e => e.Year).HasColumnName("year");

            entity.Ignore(e => e.AvgerageRating);
        });

        modelBuilder.Entity<Person>(entity =>
        {
            entity.HasKey(e => e.Id).HasName("persons_pkey");

            entity.ToTable("persons");

            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.Bio).HasColumnName("bio");
            entity.Property(e => e.FirstName).HasColumnName("first_name");
            entity.Property(e => e.Image).HasColumnName("image");
            entity.Property(e => e.LastName).HasColumnName("last_name");
            entity.Property(e => e.MiddleName)
                .HasDefaultValueSql("''::text")
                .HasColumnName("middle_name");
        });

        modelBuilder.Entity<Review>(entity =>
        {
            entity.HasKey(e => e.Id).HasName("reviews_pkey");

            entity.ToTable("reviews");

            entity.HasIndex(e => e.CreationTime, "creation_time_index");

            entity.HasIndex(e => e.AuthorId, "review_author_index");

            entity.HasIndex(e => e.MovieId, "review_movie_index");

            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.AuthorId).HasColumnName("author_id");
            entity.Property(e => e.Body).HasColumnName("body");
            entity.Property(e => e.CreationTime).HasColumnName("creation_time");
            entity.Property(e => e.MovieId).HasColumnName("movie_id");
            entity.Property(e => e.Rating).HasColumnName("rating");

            entity.HasOne(d => d.Author).WithMany(p => p.Reviews)
                .HasForeignKey(d => d.AuthorId)
                .OnDelete(DeleteBehavior.ClientSetNull)
                .HasConstraintName("reviews_author_id_fkey");

            entity.HasOne(d => d.Movie).WithMany(p => p.Reviews)
                .HasForeignKey(d => d.MovieId)
                .OnDelete(DeleteBehavior.ClientSetNull)
                .HasConstraintName("reviews_movie_id_fkey");
        });

        modelBuilder.Entity<User>(entity =>
        {
            entity.HasKey(e => e.Id).HasName("users_pkey");

            entity.ToTable("users");

            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.Image).HasColumnName("image");
            entity.Property(e => e.Name).HasColumnName("name");
        });

        OnModelCreatingPartial(modelBuilder);
    }

    partial void OnModelCreatingPartial(ModelBuilder modelBuilder);
}
