from datetime import timedelta
from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.timezone import localtime
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

# models from the same app
from .models import (
    User, Profile, Post, Like, Comment,
    Message, AccountDeletionLog, Bookmark
)


# social_book/core/views.py

# Create your views here.
@login_required(login_url='signin')
def index(request):
    if request.method == 'POST':
        caption = request.POST.get('caption')
        image = request.FILES.get('image')
        if caption or image:
            Post.objects.create(
                user=request.user,
                content=caption,
                caption=caption,
                image=image,
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            messages.success(request, "Post created successfully.")
            return redirect('index')
        else:
            messages.error(request, "Caption or image is required.")

    posts = Post.objects.all().order_by('-created_at')
    for post in posts:
        post.liked_users = [like.user for like in post.likes.select_related('user')[:3]]
        post.user_liked = post.likes.filter(user=request.user).exists()
    return render(request, 'index.html', {'posts': posts})
from django.shortcuts import render

def survey_services(request):
    return render(request, 'survey_services.html')


def survey_terms(request):
    return render(request, 'survey_terms.html')

def survey_contact(request):
    return render(request, 'survey_contact.html')

def survey_whydata(request):
    return render(request, 'survey_whydata.html')


def signup(request):

    if request.method == 'POST':
        signup_username = request.POST['signup-username']#name sang html form auth
        signup_email = request.POST['signup-email']
        signup_password = request.POST['signup-password']
        signup_confirm_password = request.POST['signup-confirm-password']

        if signup_password == signup_confirm_password:
            if User.objects.filter(email=signup_email).exists():
                messages.info(request, 'Email Taken')
                return redirect ('signup')
            elif User.objects.filter(username=signup_username).exists():
                messages.info(request, 'Username Taken')
                return redirect('signup')
            else:
                user = User.objects.create_user(username=signup_username, email=signup_email, password=signup_password)#kwae data para simo html e.g {{user.username}}
                user.save()

                #log user in and redirect to settings page 
                user_login = authenticate(username=signup_username, password=signup_password)
                if user_login is not None:
                    login(request, user_login)
                else:
                    messages.error(request, 'Authentication failed. please try again')
                    return redirect('signup')



                #create a Profile object for new user
            user_model = User.objects.get(username=signup_username)
            Profile.objects.get_or_create(user=user_model)
            return redirect('survey')#pulihi sang first after user login

        else:
            messages.info(request, 'Password is Not Matching')
            return redirect ('signup')
    else:
            return render(request, 'signup.html')
    




def signin(request): 
    if request.method == 'POST':
        signin_username = request.POST.get('signin-username')
        signin_password = request.POST.get('signin-password')

        try:
            user_obj = User.objects.get(username=signin_username)
            user_profile, created = Profile.objects.get_or_create(user=user_obj)

            if not user_obj.is_active:
                if user_profile.deactivation_expiry and user_profile.deactivation_expiry > timezone.now():
                    time_remaining = user_profile.deactivation_expiry - timezone.now()
                    days = time_remaining.days
                    seconds_total = int(time_remaining.total_seconds())
                    hours = (seconds_total // 3600) % 24
                    minutes = (seconds_total % 3600) // 60
                    secs = seconds_total % 60

                    formatted_time = ""
                    if days > 0:
                        formatted_time += f"{days} day{'s' if days != 1 else ''}, "
                    formatted_time += f"{hours:02d}:{minutes:02d}:{secs:02d}"

                    messages.error(request, f"Your account is currently deactivated. It will be reactivated in {formatted_time}.")
                    return redirect('signin')
                elif user_profile.deactivation_expiry and user_profile.deactivation_expiry <= timezone.now():
                    user_obj.is_active = True
                    user_obj.save()
                    user_profile.deactivation_expiry = None
                    user_profile.save()
                    messages.success(request, "Your account has been automatically reactivated. Please try logging in again.")
                    return redirect('signin')
                else:
                    messages.error(request, "Your account is currently inactive. Please contact support if you believe this is an error.")
                    return redirect('signin')

        except User.DoesNotExist:
            pass

        user = authenticate(request, username=signin_username, password=signin_password)

        if user is not None:
            user_profile, created = Profile.objects.get_or_create(user=user)
            user_profile.last_login_time = timezone.now()
            user_profile.is_online = True  # ✅ Mark user as online
            user_profile.save()

            login(request, user)
            return redirect('settings')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('signin')

    return render(request, 'signin.html')


@login_required(login_url='signin')
def logout_view(request):
    try:
        user_profile = Profile.objects.get(user=request.user)
        user_profile.last_logout_time = timezone.now()
        user_profile.is_online = False  # 🔻 Mark as offline
        user_profile.save()
    except Profile.DoesNotExist:
        pass

    logout(request)
    return redirect('signin')

from django.utils import timezone
from datetime import timedelta

ONLINE_THRESHOLD = timedelta(minutes=5)

def is_user_online(profile):
    if not profile.active_status_date:
        return False
    return timezone.now() - profile.active_status_date < ONLINE_THRESHOLD
def some_view(request):
    profile = Profile.objects.get(user=request.user)
    online_status = is_user_online(profile)
    context = {'profile': profile, 'is_online': online_status}
    return render(request, 'settings.html', context)

@login_required(login_url='signin')
def delete_account(request):
    """
    Handles the deletion of the currently logged-in user's account.
    Logs the deletion event before performing the actual deletion.
    """
    if request.method != 'POST':
        # Only allow POST requests for this action
        return HttpResponse(status=405)  # Method Not Allowed

    # Get the user object that is currently logged in and requesting deletion
    user_to_delete = request.user

    # Get the reason for deletion from the POST data
    reason = request.POST.get('reason', '').strip()

    # Use a database transaction to ensure atomicity:
    # Either both the log entry is created and the user is deleted,
    # or if any error occurs, both operations are rolled back.
    with transaction.atomic():
        try:
            # 1. Log the deletion *before* deleting the account.
            # We record the username of the account being deleted.
            # The 'deleted_by' field points to the current user (who is deleting themselves).
            # Due to on_delete=models.SET_NULL on 'deleted_by', this ForeignKey will become NULL
            # after the user_to_delete.delete() call, which is expected for self-deletion.
            AccountDeletionLog.objects.create(
                deleted_account_username=user_to_delete.username,
                deleted_by=user_to_delete, # This will be the user deleting themselves
                reason=reason if reason else "User self-deleted account." # Use provided reason or a default
            )

            # 2. Log out the user before deleting their account to prevent session issues.
            # This ensures the session is cleared before the user object is gone.
            logout(request) 

            # 3. Perform the actual account deletion.
            # This will trigger CASCADE deletes for related Profile, Post, and Comment objects.
            user_to_delete.delete() 

            messages.success(request, "Your account has been successfully deleted.")
            # Redirect to the sign-in page or a generic success page
            return redirect('signin') 

        except Exception as e:
            # If an error occurs during logging or deletion, the transaction will be rolled back.
            messages.error(request, f"An error occurred while deleting your account: {e}")
            # Redirect back to the settings page or an appropriate error page
            return redirect('settings') # Assuming 'settings' is the URL for your settings page




@login_required(login_url='signin')
def deactivate_account(request):
    if request.method != 'POST':
        return HttpResponse(status=405)  # Method Not Allowed

    deactivation_period = request.POST.get('deactivation_period')
    user_profile = Profile.objects.get(user=request.user)

    # --- IMPORTANT FIX HERE: Ensure user_profile.user.is_active is modified ---
    # In your 30-day block, you had `user_profile.is_active = False`
    # It should be `user_profile.user.is_active = False` to affect Django's User model.
    if deactivation_period == '15':
        expiry_date = timezone.now() + timedelta(days=15)
        user_profile.user.is_active = False # Corrected: affecting the User model
        user_profile.deactivation_expiry = expiry_date
        user_profile.user.save() # Save the Django User model
        user_profile.save() # Save the Profile model
        formatted_expiry = expiry_date.strftime('%Y-%m-%d %H:%M:%S') + f".{int(expiry_date.microsecond / 10000):02d}"
        messages.info(request, f"Your account has been deactivated for 15 days. It will automatically reactivate on {formatted_expiry}.")
        logout(request)
        return redirect('signin')

    elif deactivation_period == '30':
        expiry_date = timezone.now() + timedelta(days=30)
        user_profile.user.is_active = False # FIX APPLIED HERE: affecting the User model
        user_profile.deactivation_expiry = expiry_date
        user_profile.user.save() # Save the Django User model
        user_profile.save() # Save the Profile model
        formatted_expiry = expiry_date.strftime('%Y-%m-%d %H:%M:%S') + f".{int(expiry_date.microsecond / 10000):02d}"
        messages.info(request, f"Your account has been deactivated for 30 days. It will automatically reactivate on {formatted_expiry}.")
        logout(request)
        return redirect('signin')

    else:
        messages.error(request, "Invalid deactivation period selected.")
        return redirect('settings')
#### delete if needed
# views.py

#-----------------------------------------------for posts-----------------------------------------------------
# Create a post from standalone page
@login_required(login_url='signin')
def create_post(request):
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            post = Post.objects.create(
                user=request.user,
                content=content,
                created_at=timezone.now(),
                updated_at=timezone.now(),
                no_of_likes=0
            )
            messages.success(request, "Post created successfully.")
            return redirect('index', post_id=post.id)
        else:
            messages.error(request, "Content cannot be empty.")
    return render(request, 'posts/index.html')

# List all posts
def post_list(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'post_list.html', {'posts': posts})

# View a single post
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all().order_by('created_at')
    return render(request, 'posts/post_detail.html', {'post': post, 'comments': comments})

@login_required(login_url='signin')
def add_comment(request, post_id):
    # This view will just validate CSRF and return OK
    if request.method == 'POST':
        return JsonResponse({'status': 'validated'})
    return JsonResponse({'error': 'Invalid request'}, status=400)
 
@login_required
@csrf_exempt
def delete_post(request, post_id):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Post not found'}, status=404)

    if post.user != request.user:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

    # ✅ Store data BEFORE deleting
    post_data = {
        'post_id': str(post.id),
        'username': post.user.username,
    }

    post.delete()

    # ✅ WebSocket broadcast
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "posts_feed",
        {
            "type": "broadcast_post_delete",
            **post_data,
        }
    )

    return JsonResponse({'status': 'success', **post_data})



@csrf_exempt
@require_POST
def create_post_from_index(request):
    caption = request.POST.get("caption")
    image = request.FILES.get("image")

    post = Post.objects.create(user=request.user, caption=caption, image=image)

    # Render the post HTML using Django template
    post_html = render_to_string("posts/post_single.html", {
        "post": post,
        "user": request.user,  # Needed for {% if user == post.user %}
    })

    # Notify WebSocket group with rendered HTML
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "posts_feed",
        {
            "type": "new_post",
            "html": post_html,
        }
    )

    return JsonResponse({"status": "success"})


#LIKE REACT POST ---------------------------------------------------------------------------------


@login_required
def like_post(request, post_id):
    post = Post.objects.get(id=post_id)
    user = request.user

    like, created = Like.objects.get_or_create(user=user, post=post)

    if not created:
        like.delete()

    post.no_of_likes = post.likes.count()
    post.save()

    recent_likers = post.likes.select_related('user__profile').order_by('-id')[:3]
    liker_data = [
        {
            'username': liker.user.username,
            'profile_img': liker.user.profile.profileimg.url
        }
        for liker in recent_likers
    ]

    # WebSocket Broadcast (fix UUID serialization issue)
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'post_{str(post.id)}',  # Ensure post.id is a string
        {
            'type': 'send_like_update',
            'post_id': str(post.id),  # Convert UUID to string
            'likes_count': post.no_of_likes,
            'recent_likers': liker_data
        }
    )

    return JsonResponse({
        'status': 'liked' if created else 'unliked',
        'likes_count': post.no_of_likes,
        'recent_likers': liker_data
    })


# views.py
# views.py
# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Count, Q  # Add Count and Q
from .models import Profile, Post, FriendRequest, UserSurvey, Comment, Bookmark  # Add missing models
from django.contrib.auth.models import User


from django.contrib import messages
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation
from .models import Profile
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_http_methods
from datetime import date

# Helper functions moved ABOVE the view
def validate_age(value):
    if not value:
        return None, []
    try:
        age = int(value)
        if not (13 <= age <= 120):
            return None, ["Age must be between 13 and 120."]
        return age, []
    except ValueError:
        return None, ["Age must be a valid number."]

def validate_height(value):
    if not value:
        return None, []
    try:
        height = Decimal(value)
        if not (1 <= height <= 10):
            return None, ["Height must be between 1 and 10 feet."]
        return height, []
    except (ValueError, InvalidOperation):
        return None, ["Height must be a valid decimal number."]

def validate_weight(value):
    if not value:
        return None, []
    try:
        weight = Decimal(value)
        if not (30 <= weight <= 500):
            return None, ["Weight must be between 30 and 500 kg."]
        return weight, []
    except (ValueError, InvalidOperation):
        return None, ["Weight must be a valid number in kg."]

def validate_birthday(value):
    if not value:
        return None, []
    try:
        birthday = parse_date(value)
        today = date.today()
        
        if not birthday:
            return None, ["Invalid birthday format. Use YYYY-MM-DD."]
        if birthday > today:
            return None, ["Birthday cannot be in the future."]
        
        age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
        if age < 13:
            return None, ["You must be at least 13 years old."]
        if age > 120:
            return None, ["Please enter a valid birthday."]
            
        return birthday, []
    except Exception:
        return None, ["Invalid birthday format."]

def validate_location(value):
    value = value.strip()
    if len(value) > 100:
        return None, ["Location must be 100 characters or less."]
    return value, []

def validate_relation(value):
    if value and value not in dict(Profile.RELATIONSHIP_CHOICES):
        return None, ["Invalid relationship status selected."]
    return value, []

def validate_gender(value):
    if value and value not in dict(Profile.GENDER_CHOICES):
        return None, ["Invalid gender selected."]
    return value, []

def validate_bio(value):
    value = value.strip()
    if len(value) > 1000:
        return None, ["Bio must be 1000 characters or less."]
    return value, []

def process_profile_image(request, profile, errors):
    if 'profile_img' not in request.FILES:
        return
    
    img = request.FILES['profile_img']
    if img.size > 5 * 1024 * 1024:
        errors['profile_img'].append("Profile image must be less than 5MB.")
    
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
    if img.content_type not in allowed_types:
        errors['profile_img'].append("Profile image must be JPEG, PNG, or GIF format.")
    
    if not errors['profile_img']:
        profile.profileimg = img

def get_current_values(profile):
    return {
        'location': profile.location or '',
        'relation': profile.relation or '',
        'gender': profile.gender or '',
        'bio': profile.bio or '',
        'age': profile.age or '',
        'height': profile.height or '',
        'weight': profile.weight or '',
        'birthday': profile.birthday.isoformat() if profile.birthday else '',
        'profile_img_url': profile.profileimg.url if profile.profileimg else '',
    }

@login_required
@require_http_methods(["GET", "POST"])
def profile_view(request):
    user = request.user
    profile, created = Profile.objects.get_or_create(user=user)
    errors = {field: [] for field in [
        'location', 'relation', 'gender', 'bio', 
        'age', 'height', 'weight', 'birthday', 'profile_img'
    ]}
    
    if request.method == 'POST':
        # Process all fields
        field_validators = {
            'location': validate_location,
            'relation': validate_relation,
            'gender': validate_gender,
            'bio': validate_bio,
            'age': validate_age,
            'height': validate_height,
            'weight': validate_weight,
            'birthday': validate_birthday,
        }
        
        for field, validator in field_validators.items():
            value = request.POST.get(field, '').strip()
            processed, field_errors = validator(value)
            if field_errors:
                errors[field].extend(field_errors)
            else:
                setattr(profile, field, processed)
        
        # Handle profile image
        process_profile_image(request, profile, errors)
        
        # Validate and save if no errors
        if not any(errors.values()):
            try:
                profile.full_clean()
                profile.save()
                messages.success(request, "Profile updated successfully!")
                return redirect('profile')
            except ValidationError as e:
                for field, errs in e.message_dict.items():
                    if field in errors:
                        errors[field].extend(errs)
                messages.error(request, "Please correct the errors below.")
        
        # Show all errors to user
        for field_errs in errors.values():
            for err in field_errs:
                messages.error(request, err)

    context = {
        'current_values': get_current_values(profile),
        'errors': {k: v[0] if v else '' for k, v in errors.items()},
        'relationship_choices': Profile.RELATIONSHIP_CHOICES,
        'gender_choices': Profile.GENDER_CHOICES,
    }
    return render(request, 'settings.html', context)


# core/views.py

@login_required
def chat_view(request, receiver_id):
    receiver = get_object_or_404(User, id=receiver_id)

    # Fetch past messages between the current user and the receiver
    # This queries messages where:
    # (sender is current_user AND receiver is target_receiver) OR
    # (sender is target_receiver AND receiver is current_user)
    past_messages = Message.objects.filter(
        Q(sender=request.user, receiver=receiver) |
        Q(sender=receiver, receiver=request.user)
    ).order_by('timestamp') # Order by timestamp to display chronologically

    context = {
        'receiver': receiver,
        'past_messages': past_messages,
    }
    return render(request, 'chat.html', context)

@login_required(login_url='signin')
def settings(request):
    survey_data = None
    if request.user.is_authenticated:
        try:
            survey_data = request.user.survey  # Access the OneToOne relationship
        except:
            pass
    return render(request, 'settings.html', {'survey': survey_data})


def about(request):
    return render(request, 'about.html')

def analytics(request):
    return render(request, 'analytics.html')


def explore(request):
    return render(request, 'explore.html')

def forgotpass(request):
    return render(request, 'forgotpass.html')

def help(request):
    return render(request, 'help.html')


def services(request):
    return render(request, 'services.html')


def terms(request):
    return render(request, 'terms.html')

#===========  profile .html        views.py =============#
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from .models import Profile, Post, FriendRequest, UserSurvey
from django.contrib.auth.models import User

# views.py
@login_required
def profile(request):
    user = request.user
    profile = get_object_or_404(Profile, user=user)
    posts = Post.objects.filter(user=user).order_by('-created_at')
    survey = getattr(user, 'survey', None)
    friend_requests = FriendRequest.objects.filter(to_user=user, is_accepted=False)
    # Add friends to context
    friends = user.profile.friends.all()[:5]  # Get first 5 friends

    report_reasons = ["Spam", "Harassment", "Inappropriate Content", "Fake Profile", "Other"]
    total_likes = Post.objects.filter(user=user).aggregate(total=Count('likes'))['total'] or 0
    total_comments = Comment.objects.filter(post__user=user).count()
    total_bookmarks = Bookmark.objects.filter(post__user=user).count()
    total_visits = profile.profile_visits
    return render(request, 'profile.html', {
        'user': user,
        'profile': profile,
        'posts': posts,
        'survey': survey,
        'friend_requests': friend_requests,
        'report_reasons': report_reasons,
        'is_own_profile': True,
        'friends': friends,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'total_bookmarks': total_bookmarks,
        'total_visits': total_visits,
    })


@login_required
def change_cover(request):
    if request.method == "POST" and request.FILES.get('cover_photo'):
        request.user.profile.cover_photo = request.FILES['cover_photo']
        request.user.profile.save()
    return redirect('profile')
@login_required
def public_profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    
    if request.user == profile_user:
        return redirect('profile')

    profile = get_object_or_404(Profile, user=profile_user)
    posts = Post.objects.filter(user=profile_user).order_by('-created_at')
    survey = getattr(profile_user, 'survey', None)
    profile.profile_visits += 1
    profile.save()
    
    
    # Check friendship status
    is_friend = FriendRequest.objects.filter(
        from_user=request.user, to_user=profile_user, is_accepted=True
    ).exists() or FriendRequest.objects.filter(
        from_user=profile_user, to_user=request.user, is_accepted=True
    ).exists()

    # Get the first 5 friends of the profile_user
    friends = profile_user.profile.friends.all()[:5]
    friend_request_sent = FriendRequest.objects.filter(
        from_user=request.user,
        to_user=profile_user,
        is_accepted=False
    ).exists()

    total_likes = Post.objects.filter(user=profile_user).aggregate(total=Count('likes'))['total'] or 0
    total_comments = Comment.objects.filter(post__user=profile_user).count()
    total_bookmarks = Bookmark.objects.filter(post__user=profile_user).count()
    total_visits = profile.profile_visits

    return render(request, 'profile.html', {
        'user': profile_user,
        'profile': profile,
        'posts': posts,
        'survey': survey,
        'friend_requests': [],
        'report_reasons': ["Spam", "Harassment", "Inappropriate Content", "Fake Profile", "Other"],
        'is_own_profile': False,
        'is_friend': is_friend,
        'friends': friends,
        'friend_request_sent': friend_request_sent,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'total_bookmarks': total_bookmarks,
        'total_visits': total_visits,
    })


# Friend request handling
@require_POST
@login_required
def decline_friend(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_request.delete()
    return redirect('profile')


# views.py
@require_POST
@login_required
def respond_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id)
    
    if friend_request.to_user != request.user:
        return JsonResponse({'status': 'unauthorized'}, status=403)

    action = request.POST.get("action")
    if action == "accept":
        friend_request.is_accepted = True
        friend_request.save()
        
        # Add to friends lists
        friend_request.from_user.profile.friends.add(friend_request.to_user.profile)
        friend_request.to_user.profile.friends.add(friend_request.from_user.profile)
        
        return JsonResponse({'status': 'accepted'})
    
    elif action == "decline":
        friend_request.delete()
        return JsonResponse({'status': 'declined'})
    
    return JsonResponse({'status': 'invalid_action'}, status=400)

@require_POST
@login_required
def send_friend_request(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    
    if to_user == request.user:
        return JsonResponse({'status': 'error', 'message': "Can't add yourself"})
    
    # Check for existing request
    existing_request = FriendRequest.objects.filter(
        from_user=request.user,
        to_user=to_user
    ).first()

    if existing_request:
        return JsonResponse({'status': 'already_sent'})
    
    FriendRequest.objects.create(from_user=request.user, to_user=to_user)
    return JsonResponse({'status': 'request_sent'})

@require_POST
@login_required
def cancel_friend_request(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    FriendRequest.objects.filter(
        from_user=request.user,
        to_user=to_user,
        is_accepted=False
    ).delete()
    return JsonResponse({'status': 'request_canceled'})

@require_POST
@login_required
def unfriend(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    
    # Remove friendship connections
    request.user.profile.friends.remove(other_user.profile)
    other_user.profile.friends.remove(request.user.profile)
    
    # Delete friend requests
    FriendRequest.objects.filter(
        Q(from_user=request.user, to_user=other_user) |
        Q(from_user=other_user, to_user=request.user)
    ).delete()
    
    return JsonResponse({'status': 'unfriended'})

# views.py
@require_POST
@login_required
def toggle_follow(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    
    if target_user == request.user:
        return JsonResponse({"status": "error", "message": "You can't follow yourself."})

    # Check if request already exists
    existing_request = FriendRequest.objects.filter(
        from_user=request.user,
        to_user=target_user
    ).first()

    if existing_request:
        # Cancel existing request
        existing_request.delete()
        return JsonResponse({"status": "unfollowed"})
    else:
        # Create new friend request
        FriendRequest.objects.create(
            from_user=request.user,
            to_user=target_user
        )
        return JsonResponse({"status": "request_sent"})

# views.py
# views.py
@login_required
def friends_list(request):
    # Get the user's friends through their profile
    friends = request.user.profile.friends.all()
    return render(request, 'friends_list.html', {
        'friends': friends,
        'is_own_profile': True  # Important for conditional rendering
    })
#=======end of friend request=================================#

def search_users(request):
    query = request.GET.get('q', '').strip()
    profiles = Profile.objects.none()

    if query:
        exact = Profile.objects.filter(user__username__iexact=query)

        starts_with = Profile.objects.filter(
            user__username__istartswith=query
        ).exclude(pk__in=exact.values_list('pk', flat=True))

        contains = Profile.objects.filter(
            user__username__icontains=query
        ).exclude(pk__in=exact.values_list('pk', flat=True)).exclude(pk__in=starts_with.values_list('pk', flat=True))

        profiles = list(exact) + list(starts_with) + list(contains)

    return render(request, 'search.html', {
        'query': query,
        'profiles': profiles,
    })

User = get_user_model()
#survey/views.py
from django.shortcuts import render, redirect
from .models import UserSurvey

@login_required(login_url='signin')
def survey(request):
    if request.method == "POST":
        # --- Page 1 ---
        gender = request.POST.getlist('gender')
        looking_for = request.POST.getlist('looking_for')
        age_range = request.POST.getlist('age_range')

        # --- Page 2 ---
        goal = request.POST.getlist('goal')
        meet = request.POST.getlist('meet')

        # --- Page 3 ---
        smoke = request.POST.getlist('smoke')
        drink = request.POST.getlist('drink')
        children = request.POST.getlist('children')
        hobbies = request.POST.getlist('hobbies')

        # --- Page 4 ---
        traits = request.POST.getlist('traits')
        love_language = request.POST.getlist('love_language')

        # Save to DB (overwrites if already exists)
        UserSurvey.objects.update_or_create(
            user=request.user,
            defaults={
                'gender': gender,
                'looking_for': looking_for,
                'age_range': age_range,
                'goal': goal,
                'meet': meet,
                'smoke': smoke,
                'drink': drink,
                'children': children,
                'hobbies': hobbies,
                'traits': traits,
                'love_language': love_language,
            }
        )

        return redirect('profile')  # ✅ Redirect to settings.html

    return render(request, 'survey.html')

#bookmarks/views.py----


@login_required
def toggle_bookmark(request):
    if request.method == 'POST':
        post_id = request.POST.get('post_id')
        post = Post.objects.get(id=post_id)
        bookmark, created = Bookmark.objects.get_or_create(user=request.user, post=post)

        if not created:
            bookmark.delete()
            return JsonResponse({'status': 'removed'})
        return JsonResponse({'status': 'added'})

    return JsonResponse({'error': 'Invalid request'}, status=400)

from django.utils.timezone import now

from django.utils.timezone import now

@login_required
def bookmark_list(request):
    bookmarks = Bookmark.objects.filter(user=request.user).select_related('post__user', 'post__user__profile')

    liked_post_ids = set(
        request.user.like_set.values_list('post_id', flat=True)
    )

    # Attach custom attributes to each bookmark
    for bookmark in bookmarks:
        bookmark.is_online = bookmark.post.user.profile.is_online
        bookmark.is_liked = bookmark.post.id in liked_post_ids

    return render(request, 'bookmarks.html', {
        'bookmarks': bookmarks,
    })


#end of bookmarks ---
def post_detail_modal(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    return render(request, 'posts/post_detail_modal.html', {'post': post})

from django.contrib.auth.decorators import login_required
from django.db.models import Max, Q
from .models import Message, Profile, User

@login_required
def message_list_view(request):
    user = request.user

    # Get the latest message per conversation partner
    latest_messages = (
        Message.objects.filter(Q(sender=user) | Q(receiver=user))
        .order_by('receiver', '-timestamp')
        .distinct('receiver')  # Works in PostgreSQL
    )

    # For SQLite/MySQL, manually filter latest message per partner:
    # Optionally, group by each user, then get the latest message using a loop if necessary.

    context = {
        'messages': latest_messages,
    }
    return render(request, 'partials/message_list.html', context)



from django.contrib.auth.decorators import login_required
from django.db.models import Q, Max
from django.contrib.auth.models import User
from django.shortcuts import render
from .models import Message

@login_required
def recent_messages(request):
    user = request.user

    # Get latest message per conversation partner
    # Step 1: Get all messages involving current user
    all_messages = Message.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).order_by('-timestamp')

    # Step 2: Track latest message per unique user pair
    seen_users = set()
    recent_conversations = []

    for msg in all_messages:
        other_user = msg.receiver if msg.sender == user else msg.sender
        if other_user.id not in seen_users:
            seen_users.add(other_user.id)
            recent_conversations.append({
                "user": other_user,
                "message": msg,
            })

    return render(request, 'partials/message_list.html', {"conversations": recent_conversations})

# Add this to your views.py

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string

@login_required
def posts_feed(request):
    offset = int(request.GET.get('offset', 0))
    limit = int(request.GET.get('limit', 10))
    posts = Post.objects.all().order_by('-created_at')[offset:offset+limit]
    posts_html = [
        render_to_string('posts/post_single.html', {'post': post, 'user': request.user})
        for post in posts
    ]
    return JsonResponse({'posts': posts_html})


from django.shortcuts import render
from .models import Post

def post_gallery(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'post_gallery.html', {'posts': posts})


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.models import User
from .models import Post, Profile

def user_profile(request, username):
    user_profile = get_object_or_404(User, username=username)
    posts = Post.objects.filter(user=user_profile).order_by('-created_at')
    return render(request, 'profile.html', {
        'user_profile': user_profile,
        'posts': posts
    })