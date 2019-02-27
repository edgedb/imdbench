from django.urls import path, re_path, include

from . import views


urlpatterns = [
    path('', views.index, name='index'),

    # custom views not using rest_framework
    path('api/movie_details/<int:pk>',
         views.CustomMovieView.as_view(), name='movie_details'),
    path('api/pages/movie_details/',
         views.CustomMovieView.as_view(), name='movie_details'),
    path('api/person_details/<int:pk>',
         views.CustomPersonView.as_view(), name='person_details'),
    path('api/pages/person_details/',
         views.CustomPersonView.as_view(), name='person_details'),
    path('api/user_details/<int:pk>',
         views.CustomUserView.as_view(), name='user_details'),
    path('api/pages/user_details/',
         views.CustomUserView.as_view(), name='user_details'),
]
