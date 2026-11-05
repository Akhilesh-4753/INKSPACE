from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .forms import SignUpForm, LoginForm, ProfileForm

def signup_view(request):
    """
    Handle user registration.
    MVT Flow:
    1. GET request renders empty SignUpForm.
    2. POST validates form inputs and creates new User instance.
    3. Auto-logs the user in and redirects to blog list.
    """
    if request.user.is_authenticated:
        return redirect('blogs:blog_list')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            full_name = form.cleaned_data['full_name'].strip()
            email = form.cleaned_data['email'].strip().lower()
            password = form.cleaned_data['password']

            # Generate unique username from email/name
            base_username = email.split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            # Split name into first and last
            parts = full_name.split(' ', 1)
            first_name = parts[0]
            last_name = parts[1] if len(parts) > 1 else ''

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            # Log the user in
            login(request, user)
            messages.success(request, f"Welcome to INKSPACE, {first_name or username}! Your account has been created successfully.")
            return redirect('blogs:blog_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = SignUpForm()

    return render(request, 'accounts/signup.html', {'form': form})

def login_view(request):
    """
    Handle user authentication with email or username.
    MVT Flow:
    1. GET renders LoginForm.
    2. POST resolves username or email and calls authenticate().
    3. If valid, logs in and respects 'remember_me' for session expiry.
    """
    if request.user.is_authenticated:
        return redirect('blogs:blog_list')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            credential = form.cleaned_data['username_or_email'].strip()
            password = form.cleaned_data['password']
            remember_me = form.cleaned_data.get('remember_me', False)

            # Allow user to log in with either email or username
            username_to_check = credential
            try:
                user_obj = User.objects.get(email__iexact=credential)
                username_to_check = user_obj.username
            except User.DoesNotExist:
                pass

            user = authenticate(request, username=username_to_check, password=password)

            if user is not None:
                login(request, user)
                if not remember_me:
                    # Session expires when user closes browser
                    request.session.set_expiry(0)
                else:
                    # 2 weeks session
                    request.session.set_expiry(1209600)

                messages.success(request, f"Welcome back, {user.first_name or user.username}!")
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('blogs:blog_list')
            else:
                messages.error(request, "Invalid email/username or password. Please try again.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    """
    Log out user and redirect to homepage.
    """
    if request.method in ['POST', 'GET']:
        logout(request)
        messages.info(request, "You have been logged out. We hope to see you back soon!")
    return redirect('blogs:blog_list')

@login_required
def profile_view(request):
    """
    Display and update user profile information.
    """
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('accounts:profile')
    else:
        form = ProfileForm(instance=request.user.profile)

    return render(request, 'accounts/profile.html', {'form': form})

@login_required
def toggle_follow_view(request, author_id):
    """
    Handle follow / unfollow for authors.
    MVT Flow:
    1. Enforces authentication via @login_required.
    2. Validates author exists and is NOT the requesting user (strictly prevents self-following).
    3. Toggles Follow relationship in database.
    4. Supports standard redirect and AJAX JSON responses.
    """
    from django.shortcuts import get_object_or_404
    from django.http import JsonResponse, HttpResponseBadRequest
    from .models import Follow

    target_author = get_object_or_404(User, id=author_id)

    # Backend-level self-follow prevention
    if request.user.id == target_author.id:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
            return JsonResponse({'success': False, 'error': 'You cannot follow yourself.'}, status=400)
        messages.error(request, "You cannot follow your own profile.")
        return redirect(request.META.get('HTTP_REFERER', 'blogs:blog_list'))

    follow_record = Follow.objects.filter(follower=request.user, following=target_author).first()

    if follow_record:
        follow_record.delete()
        is_following = False
        msg = f"You unfollowed {target_author.get_full_name() or target_author.username}."
    else:
        Follow.objects.create(follower=request.user, following=target_author)
        is_following = True
        msg = f"You are now following {target_author.get_full_name() or target_author.username}."

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == 'application/json':
        followers_count = Follow.objects.filter(following=target_author).count()
        return JsonResponse({
            'success': True,
            'is_following': is_following,
            'followers_count': followers_count,
            'message': msg
        })

    messages.success(request, msg)
    return redirect(request.META.get('HTTP_REFERER', 'blogs:blog_list'))

