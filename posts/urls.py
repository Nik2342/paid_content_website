from django.urls import path

from posts.apps import PostsConfig
from posts.views import (
    PostListView,
    PostCreateView,
    PostDetailView,
    PostUpdateView,
    PostDeleteView,
)

app_name = PostsConfig.name


urlpatterns = [
    path("",PostListView.as_view(), name="posts_list"),
    path("posts/", PostListView.as_view(), name="posts_list"),
    path("posts/create/", PostCreateView.as_view(), name="post_create"),
    path("posts/<int:pk>/", PostDetailView.as_view(), name="post_detail"),
    path("posts/<int:pk>/update/", PostUpdateView.as_view(), name="post_update"),
    path("posts/<int:pk>/delete/", PostDeleteView.as_view(), name="post_delete"),
]
