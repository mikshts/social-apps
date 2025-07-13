from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model

from .models import Profile, Post, Comment, AccountDeletionLog, Like, UserSurvey

User = get_user_model()

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    
    list_display = (
        'get_user_id', 'user', 'get_email', 'location', 'age', 'relation',
        'gender', 'height', 'weight', 'birthday', 'bio', 'profileimg',
        'is_active', 'online_status', 'deactivation_expiry', 'active_status_date'
    )
    list_filter = ('relation', 'is_active', 'is_online', 'location', 'gender')
    search_fields = ('user__username', 'user__email', 'location')
    readonly_fields = ('deactivation_expiry', 'active_status_date')

    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'profileimg', 'bio', 'location')
        }),
        ('Personal Details', {
            'fields': ('age', 'relation', 'gender', 'height', 'weight', 'birthday')
        }),
        ('Account Control', {
            'fields': ('is_active', 'is_online', 'deactivation_expiry', 'active_status_date')
        }),
    )

    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'

    def online_status(self, obj):
        return '🟢 Online' if obj.is_online else '⚪ Offline'
    online_status.short_description = 'Online Status'
    
    def get_user_id(self, obj):
        return obj.user.id
    get_user_id.short_description = 'User ID'
    #surveys
    def survey_traits(self, obj):
        if hasattr(obj.user, 'survey') and obj.user.survey.traits:
            return ', '.join(obj.user.survey.traits)
        return 'No survey'
    survey_traits.short_description = "Traits"

    def survey_love_language(self, obj):
        if hasattr(obj.user, 'survey') and obj.user.survey.love_language:
            return ', '.join(obj.user.survey.love_language)
        return 'No survey'
    survey_love_language.short_description = "Love Language"

    def survey_hobbies(self, obj):
        if hasattr(obj.user, 'survey') and obj.user.survey.hobbies:
            return ', '.join(obj.user.survey.hobbies)
        return 'No survey'
    survey_hobbies.short_description = "Hobbies"


# ========== Post Admin ==========
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'content')
    list_display = ('get_user_id', 'user', 'content', 'created_at', 'updated_at', 'no_of_likes')

    def get_user_id(self, obj):
        return obj.user.id
    get_user_id.short_description = 'User ID'


# ========== Comment Admin ==========
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_filter = ('created_at',)
    search_fields = ('user__username', 'text')
    list_display = ('get_user_id', 'user', 'post', 'text', 'created_at')

    def get_user_id(self, obj):
        return obj.user.id
    get_user_id.short_description = 'User ID'


# ========== Like Admin ==========
@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_filter = ('liked_at',)
    search_fields = ('user__username', 'post__content')  # Assuming 'content' is the correct field, not 'caption'
    list_display = ('get_user_id', 'user', 'post', 'liked_at')

    def get_user_id(self, obj):
        return obj.user.id
    get_user_id.short_description = 'User ID'


# ========== Custom User Admin with Deletion Logging ==========
class CustomUserAdmin(UserAdmin):
    def delete_model(self, request, obj):
        if isinstance(obj, User):
            AccountDeletionLog.objects.create(
                deleted_account_username=obj.username,
                deleted_by=request.user,
                reason="Deleted via Django Admin interface"
            )
        super().delete_model(request, obj)


# Unregister default User admin and register the custom one
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, CustomUserAdmin)


# ========== Account Deletion Log Admin ==========
@admin.register(AccountDeletionLog)
class AccountDeletionLogAdmin(admin.ModelAdmin):
    list_display = ('deleted_account_username', 'deleted_by', 'deletion_timestamp', 'reason')
    list_filter = ('deleted_by', 'deletion_timestamp')
    search_fields = ('deleted_account_username', 'reason')
    readonly_fields = ('deleted_account_username', 'deleted_by', 'deletion_timestamp', 'reason')
    date_hierarchy = 'deletion_timestamp'

from .models import Message # Import your Message model

# Register your models here.

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_filter = ('timestamp', 'sender', 'receiver')
    search_fields = ('content', 'sender__username', 'receiver__username')
    readonly_fields = ('timestamp',) # Make timestamp read-only in the admin
    date_hierarchy = 'timestamp' # Add a date-based drilldown navigation
    list_display = ('get_sender_id', 'sender', 'get_receiver_id', 'receiver', 'timestamp', 'content')

    def get_sender_id(self, obj):
        return obj.sender.id
    get_sender_id.short_description = 'Sender ID'

    def get_receiver_id(self, obj):
        return obj.receiver.id
    get_receiver_id.short_description = 'Receiver ID'


# ========== User Survey Admin ==========
@admin.register(UserSurvey)
class UserSurveyAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'created_at',
        'get_gender', 'get_looking_for', 'get_age_range',
        'get_goal', 'get_meet', 'get_smoke', 'get_drink',
        'get_children', 'get_hobbies', 'get_traits', 'get_love_language'
    )

    def get_gender(self, obj):
        return ', '.join(obj.gender) if obj.gender else '-'
    get_gender.short_description = "Gender"

    def get_looking_for(self, obj):
        return ', '.join(obj.looking_for) if obj.looking_for else '-'
    get_looking_for.short_description = "Looking For"

    def get_age_range(self, obj):
        return ', '.join(obj.age_range) if obj.age_range else '-'
    get_age_range.short_description = "Age Range"

    def get_goal(self, obj):
        return ', '.join(obj.goal) if obj.goal else '-'
    get_goal.short_description = "Goal"

    def get_meet(self, obj):
        return ', '.join(obj.meet) if obj.meet else '-'
    get_meet.short_description = "Meet"

    def get_smoke(self, obj):
        return 'Yes' if obj.smoke else 'No'
    get_smoke.short_description = "Smoke"

    def get_drink(self, obj):
        return 'Yes' if obj.drink else 'No'
    get_drink.short_description = "Drink"

    def get_children(self, obj):
        return 'Yes' if obj.children else 'No'
    get_children.short_description = "Children"

    def get_hobbies(self, obj):
        return ', '.join(obj.hobbies) if obj.hobbies else '-'
    get_hobbies.short_description = "Hobbies"

    def get_traits(self, obj):
        return ', '.join(obj.traits) if obj.traits else '-'
    get_traits.short_description = "Traits"

    def get_love_language(self, obj):
        return ', '.join(obj.love_language) if obj.love_language else '-'
    get_love_language.short_description = "Love Language"

