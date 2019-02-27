from django.db import models


class User(models.Model):
    name = models.CharField(max_length=200)
    image = models.CharField(max_length=200)


class Person(models.Model):
    first_name = models.CharField(max_length=200)
    middle_name = models.CharField(max_length=200, blank=True)
    last_name = models.CharField(max_length=200)
    image = models.CharField(max_length=200)
    bio = models.TextField(blank=True, null=True)

    def get_full_name(self):
        if self.middle_name:
            return f'{self.first_name} {self.middle_name} {self.last_name}'
        else:
            return f'{self.first_name} {self.last_name}'


class Movie(models.Model):
    image = models.CharField(max_length=200)
    title = models.CharField(max_length=200)
    year = models.IntegerField()
    description = models.TextField()
    directors = models.ManyToManyField(Person, through='Directors',
                                       related_name='directed')
    cast = models.ManyToManyField(Person, through='Cast',
                                  related_name='acted_in')

    def get_avg_rating(self):
        return self.reviews.all().aggregate(
            models.Avg('rating'))['rating__avg']


class Directors(models.Model):
    list_order = models.IntegerField(blank=True, null=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE,
                               related_name='directed_rel')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE,
                              related_name='directors_rel')


class Cast(models.Model):
    list_order = models.IntegerField(blank=True, null=True)
    person = models.ForeignKey(Person, on_delete=models.CASCADE,
                               related_name='acted_in_rel')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE,
                              related_name='cast_rel')


class Review(models.Model):
    body = models.TextField()
    rating = models.IntegerField()
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='reviews')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE,
                              related_name='reviews')
    creation_time = models.DateTimeField()
