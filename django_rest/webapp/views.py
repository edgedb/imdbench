from django.http import HttpResponse
from rest_framework import viewsets
from rest_framework.response import Response
from webapp import models, serializers

from .profiler import profiled


def index(request):
    return HttpResponse("Django REST benchmark.")


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


class BaseDetailsViewSet(viewsets.ModelViewSet):
    @profiled
    def retrieve(self, *args, **kwargs):
        return super().retrieve(*args, **kwargs)

    @profiled
    def list(self, request):
        # extract various ordering and pagination params from the GET request
        order_by = request.GET.get('order', self.default_order)
        order_dir = request.GET.get('dir', 'asc')
        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 10))

        queryset = self.queryset.order_by(
            order_by if order_dir == 'asc' else f'-{order_by}'
        )[offset:offset + limit]

        return Response(self.serializer_class(queryset, many=True).data)


class MovieDetailsViewSet(BaseDetailsViewSet):
    """
    API endpoint that allows to view a detailed movie info.
    """
    queryset = models.Movie.objects
    serializer_class = serializers.MovieDetailsSerializer
    default_order = 'title'


class PersonDetailsViewSet(BaseDetailsViewSet):
    """
    API endpoint that allows to view a detailed person info.
    """
    queryset = models.Person.objects
    serializer_class = serializers.PersonDetailsSerializer
    default_order = 'last_name'


class UserDetailsViewSet(BaseDetailsViewSet):
    """
    API endpoint that allows to view a detailed user info.
    """
    queryset = models.User.objects
    serializer_class = serializers.UserDetailsSerializer
    default_order = 'name'
