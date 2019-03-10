from _django import models
from rest_framework import serializers


# Generic serializers
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = '__all__'


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Person
        fields = '__all__'


class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Movie
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Review
        fields = '__all__'


# Movie-specific serializers
class MoviewReviewAuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ('id', 'name', 'image')


class MoviewReviewSerializer(serializers.ModelSerializer):
    author = MoviewReviewAuthorSerializer(many=False, read_only=True)

    class Meta:
        model = models.Review
        fields = ('id', 'body', 'rating', 'author')


class MoviewCrewSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = models.Person
        fields = ('id', 'full_name', 'image')

    def get_full_name(self, obj):
        return obj.get_full_name()


class MovieDetailsSerializer(serializers.ModelSerializer):
    reviews = serializers.SerializerMethodField()
    directors = serializers.SerializerMethodField()
    cast = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()

    class Meta:
        model = models.Movie
        fields = ('id', 'image', 'title', 'year', 'description',
                  'directors', 'cast', 'avg_rating', 'reviews')

    def get_reviews(self, obj):
        reviews = obj.reviews.all().order_by('-creation_time')
        # select all author links in one query
        return MoviewReviewSerializer(
            reviews.select_related('author'), many=True).data

    def get_directors(self, obj):
        crew = obj.directors_rel.all().order_by(
            'list_order', 'person__last_name')
        # select all person links in one query
        crew = [rel.person for rel in crew.select_related('person')]
        return MoviewCrewSerializer(crew, many=True).data

    def get_cast(self, obj):
        crew = obj.cast_rel.all().order_by(
            'list_order', 'person__last_name')
        # select all person links in one query
        crew = [rel.person for rel in crew.select_related('person')]
        return MoviewCrewSerializer(crew, many=True).data

    def get_avg_rating(self, obj):
        return obj.get_avg_rating()


# Person-specific serializers
class PersonMovieSerializer(serializers.ModelSerializer):
    avg_rating = serializers.SerializerMethodField()

    class Meta:
        model = models.Movie
        fields = ('id', 'image', 'title', 'year', 'avg_rating')

    def get_avg_rating(self, obj):
        return obj.get_avg_rating()


class PersonDetailsSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    acted_in = serializers.SerializerMethodField()
    directed = serializers.SerializerMethodField()

    class Meta:
        model = models.Person
        fields = ('id', 'full_name', 'image', 'bio', 'acted_in', 'directed')
        depth = 1

    def get_full_name(self, obj):
        return obj.get_full_name()

    def get_acted_in(self, obj):
        movies = obj.acted_in.all().order_by('year', 'title')
        return PersonMovieSerializer(movies, many=True).data

    def get_directed(self, obj):
        movies = obj.directed.all().order_by('year', 'title')
        return PersonMovieSerializer(movies, many=True).data


# User-specific serializers
class UserReviewMovieSerializer(serializers.ModelSerializer):
    avg_rating = serializers.SerializerMethodField()

    class Meta:
        model = models.Movie
        fields = ('id', 'image', 'title', 'avg_rating')

    def get_avg_rating(self, obj):
        return obj.get_avg_rating()


class UserReviewSerializer(serializers.ModelSerializer):
    movie = UserReviewMovieSerializer(many=False, read_only=True)

    class Meta:
        model = models.Review
        fields = ('id', 'body', 'rating', 'movie')


class UserDetailsSerializer(serializers.ModelSerializer):
    latest_reviews = serializers.SerializerMethodField()

    class Meta:
        model = models.User
        fields = ('id', 'name', 'image', 'latest_reviews')
        depth = 2

    def get_latest_reviews(self, obj):
        reviews = obj.reviews.all().order_by('-creation_time')
        # select all movie links in one query
        return UserReviewSerializer(
            reviews.select_related('movie')[:3], many=True).data
