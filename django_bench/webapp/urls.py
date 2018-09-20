from django.urls import path, re_path, include
from rest_framework import routers

from . import views


router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'people', views.PersonViewSet)
router.register(r'movies', views.MovieViewSet)
router.register(r'reviews', views.ReviewViewSet)


urlpatterns = [
    path('', views.index, name='index'),
    re_path(r'^api/', include(router.urls)),
    # REST framework
    path('api/movie_details/<int:pk>',
         views.MovieDetailsViewSet.as_view({'get': 'retrieve'})),
    path('api/pages/movie_details/',
         views.MovieDetailsViewSet.as_view({'get': 'list'})),
    path('api/person_details/<int:pk>',
         views.PersonDetailsViewSet.as_view({'get': 'retrieve'})),
    path('api/pages/person_details/',
         views.PersonDetailsViewSet.as_view({'get': 'list'})),
    path('api/user_details/<int:pk>',
         views.UserDetailsViewSet.as_view({'get': 'retrieve'})),
    path('api/pages/user_details/',
         views.UserDetailsViewSet.as_view({'get': 'list'})),
    re_path(r'^api-auth/',
            include('rest_framework.urls', namespace='rest_framework')),

    # custom views not using rest_framework
    path('api/custom/movie_details/<int:pk>',
         views.CustomMovieView.as_view(), name='movie_details'),
    path('api/custom/pages/movie_details/',
         views.CustomMovieView.as_view(), name='movie_details'),
    path('api/custom/person_details/<int:pk>',
         views.CustomPersonView.as_view(), name='person_details'),
    path('api/custom/pages/person_details/',
         views.CustomPersonView.as_view(), name='person_details'),
    path('api/custom/user_details/<int:pk>',
         views.CustomUserView.as_view(), name='user_details'),
    path('api/custom/pages/user_details/',
         views.CustomUserView.as_view(), name='user_details'),
]
