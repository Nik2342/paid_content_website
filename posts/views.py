from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views.generic import (
    CreateView,
    UpdateView,
    ListView,
    DeleteView,
    DetailView,
)

from rest_framework.reverse import reverse_lazy
from rest_framework_simplejwt.authentication import JWTAuthentication

from posts.forms import PostForm
from posts.models import Post


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

        if not self.request.user.is_authenticated:
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
        return (
            self.request.user.is_authenticated
            and self.request.user.has_paid_subscription
        )


class PostCreateView(CreateView):
    model = Post
    form_class = PostForm
    template_name = "posts/post_form.html"
    success_url = reverse_lazy("posts:posts_list")

    def authenticate_user(self, request):
        try:
            jwt_auth = JWTAuthentication()
            auth_result = jwt_auth.authenticate(request)
            return auth_result[0] if auth_result else None
        except:
            return None

    def form_valid(self, form):
        user = self.authenticate_user(self.request)

        if not user:
            return self.handle_no_permission()

        form.instance.author = user
        return super().form_valid(form)

    def handle_no_permission(self):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Authentication required'}, status=401)
        return redirect('users:login?next=' + self.request.path)


class PostUpdateView(UpdateView):
    model = Post
    form_class = PostForm
    template_name = "posts/post_form.html"
    success_url = reverse_lazy("posts:posts_list")

    def authenticate_user(self, request):
        try:
            jwt_auth = JWTAuthentication()
            auth_result = jwt_auth.authenticate(request)
            return auth_result[0] if auth_result else None
        except:
            return None

    def dispatch(self, request, *args, **kwargs):
        user = self.authenticate_user(request)
        if not user:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        user = self.authenticate_user(self.request)
        return Post.objects.filter(author=user) if user else Post.objects.none()

    def handle_no_permission(self):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Authentication required'}, status=401)
        return redirect('users:login?next=' + self.request.path)


class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = "posts/post_confirm_delete.html"
    success_url = reverse_lazy("posts:posts_list")

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)



