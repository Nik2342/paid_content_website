from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import (
    CreateView,
    UpdateView,
    ListView,
    DeleteView,
    DetailView,
)
from django.http import JsonResponse
from django.shortcuts import redirect
from rest_framework.reverse import reverse_lazy
from posts.forms import PostForm
from posts.models import Post
from users.permissions import check_jwt_authentication


class JWTAuthMixin:

    def dispatch(self, request, *args, **kwargs):
        if not check_jwt_authentication(request):
            if self.request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"error": "Authentication required"}, status=401)
            return redirect(f"/users/login/?next={request.path}")
        return super().dispatch(request, *args, **kwargs)


class PostListView(ListView):
    model = Post
    template_name = "posts/posts_list.html"
    context_object_name = "posts"
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        posts = context["posts"]

        for post in posts:
            post.user_has_access = self.has_access_to_post(post)

        return context

    def has_access_to_post(self, post):
        if not post.is_paid:
            return True

        if not check_jwt_authentication(self.request):
            return False

        return self.request.user.has_paid_subscription


class PostDetailView(DetailView):
    model = Post
    template_name = "posts/post_detail.html"
    context_object_name = "post"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()

        context["user_has_access"] = self.has_access_to_post(post)

        return context

    def has_access_to_post(self, post):
        if not post.is_paid:
            return True

        if not check_jwt_authentication(self.request):
            return False

        return getattr(self.request.user, "has_paid_subscription", False)


class PostCreateView(JWTAuthMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = "posts/post_form.html"
    success_url = reverse_lazy("posts:posts_list")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(JWTAuthMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = "posts/post_form.html"
    success_url = reverse_lazy("posts:posts_list")

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)


class PostDeleteView(JWTAuthMixin, DeleteView):
    model = Post
    template_name = "posts/post_confirm_delete.html"
    success_url = reverse_lazy("posts:posts_list")

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)
