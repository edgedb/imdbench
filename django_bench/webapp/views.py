from django.http import HttpResponse, JsonResponse
from django.views import View
from rest_framework import viewsets
from rest_framework.response import Response
from webapp import models, serializers

from .profiler import profiled


def index(request):
    return HttpResponse("Django benchmark.")


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


class CustomView(View):
    """
    Custom view that allows more explicit control of the API endpoints
    and serialization.
    """

    @profiled
    def get(self, request, pk=None):
        # There are a couple of possibilities:
        # 1) pk is given and the result is supposed to be a single tree.
        # 2) no pk is given and the result is a "page" of data
        if pk is not None:
            resp = self.render(self.fetch_one(pk))
            return JsonResponse(resp)

        else:
            resp = [self.render(item) for item in self.fetch_page(request)]
            return JsonResponse(resp, safe=False)

    def fetch_one(self, pk):
        return self.queryset.filter(id=pk).first()

    def fetch_page(self, request):
        # extract various ordering and pagination params from the GET request
        order_by = request.GET.get('order', self.default_order)
        order_dir = request.GET.get('dir', 'asc')
        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 10))

        queryset = self.queryset.order_by(
            order_by if order_dir == 'asc' else f'-{order_by}'
        )[offset:offset + limit]

        return queryset.all()


class CustomMovieView(CustomView):
    queryset = models.Movie.objects
    default_order = 'title'

    def render(self, movie):
        result = {}

        if movie:
            directors = [rel.person for rel in
                         movie.directors_rel.order_by(
                            'list_order', 'person__last_name'
                         ).select_related('person')]
            cast = [rel.person for rel in
                    movie.cast_rel.order_by(
                        'list_order', 'person__last_name'
                    ).select_related('person')]
            reviews = movie.reviews \
                           .order_by('-creation_time').select_related('author')

            result = {
                'id': movie.id,
                'image': movie.image,
                'title': movie.title,
                'year': movie.year,
                'description': movie.description,
                'directors': [{
                    'id': person.id,
                    'full_name': person.get_full_name(),
                    'image': person.image,
                } for person in directors],
                'cast': [{
                    'id': person.id,
                    'full_name': person.get_full_name(),
                    'image': person.image,
                } for person in cast],
                'avg_rating': movie.get_avg_rating(),
                'reviews': [{
                    'id': review.id,
                    'body': review.body,
                    'rating': review.rating,
                    'author': {
                        'id': review.author.id,
                        'name': review.author.name,
                        'image': review.author.image,
                    },
                } for review in reviews],
            }

        return result


class CustomPersonView(CustomView):
    queryset = models.Person.objects
    default_order = 'last_name'

    def render(self, person):
        result = {}

        if person:
            result = {
                'id': person.id,
                'full_name': person.get_full_name(),
                'image': person.image,
                'bio': person.bio,
                'acted_in': [{
                    'id': movie.id,
                    'image': movie.image,
                    'title': movie.title,
                    'year': movie.year,
                    'avg_rating': movie.get_avg_rating(),
                } for movie in person.acted_in.order_by('year', 'title')],
                'directed': [{
                    'id': movie.id,
                    'image': movie.image,
                    'title': movie.title,
                    'year': movie.year,
                    'avg_rating': movie.get_avg_rating(),
                } for movie in person.directed.order_by('year', 'title')],
            }

        return result


class CustomUserView(CustomView):
    queryset = models.User.objects
    default_order = 'name'

    def render(self, user):
        result = {}

        if user:
            result = {
                'id': user.id,
                'name': user.name,
                'image': user.image,
                'latest_reviews': [{
                    'id': review.id,
                    'body': review.body,
                    'rating': review.rating,
                    'movie': {
                        'id': review.movie.id,
                        'image': review.movie.image,
                        'title': review.movie.title,
                        'avg_rating': review.movie.get_avg_rating(),
                    },
                } for review in user.reviews
                                    .order_by('-creation_time')
                                    .select_related('movie')[:3]
                ],
            }

        return result
