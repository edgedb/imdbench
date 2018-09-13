from django.http import HttpResponse
from rest_framework import viewsets
from webapp import models, serializers


def index(request):
    return HttpResponse("Hello, world. Django benchmark.")


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = models.User.objects.all().order_by('id')
    serializer_class = serializers.UserSerializer


class PersonViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows people to be viewed or edited.
    """
    queryset = models.Person.objects.all().order_by('id')
    serializer_class = serializers.PersonSerializer


class MovieViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows movies to be viewed or edited.
    """
    queryset = models.Movie.objects.all().order_by('id')
    serializer_class = serializers.MovieSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows reviews to be viewed or edited.
    """
    queryset = models.Review.objects.all().order_by('id')
    serializer_class = serializers.ReviewSerializer


class MovieDetailsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows to view a detailed movie info.
    """
    queryset = models.Movie.objects.all().order_by('id')
    serializer_class = serializers.MovieDetailsSerializer


class PersonDetailsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows to view a detailed person info.
    """
    queryset = models.Person.objects.all().order_by('id')
    serializer_class = serializers.PersonDetailsSerializer


class UserDetailsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows to view a detailed user info.
    """
    queryset = models.User.objects.all().order_by('id')
    serializer_class = serializers.UserDetailsSerializer
