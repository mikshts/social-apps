from django.urls import path
from . import views
from .views import profile_view, chat_view

urlpatterns = [
    # Messages
    path('', views.index, name='index'),
    path('settings/', profile_view, name='profile_view'),
    path('chat/<int:receiver_id>/', chat_view, name='chat'),
    path('recent-messages/', views.recent_messages, name='recent_messages'),
    path('swipe-story/', views.swipe_story, name='swipe_story'),


    # Friend requests (simplified)
    path('friend-request/send/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('friend-request/respond/<int:request_id>/', views.respond_friend_request, name='respond_friend_request'),  
    path('friend-request/cancel/<int:user_id>/', views.cancel_friend_request, name='cancel_friend_request'),
    path('friend-request/unfriend/<int:user_id>/', views.unfriend, name='unfriend'),
    path('friends/', views.friends_list, name='friends_list'),
    path('toggle-follow/<int:user_id>/', views.toggle_follow, name='toggle_follow'),

    # Auth
    path('signin/', views.signin, name='signin'),
    path('signup/', views.signup, name='signup'),
    path('forgotpass/', views.forgotpass, name='forgotpass'),
    path('settings/', views.settings, name='settings'),

    # Legal
    path('logout/', views.logout_view, name='logout_view'),
    path('delete_account/', views.delete_account, name='delete_account'),
    path('deactivate/', views.deactivate_account, name='deactivate_account'),
    path('about/', views.about, name='about'),
    path('terms/', views.terms, name='terms'),
    path('help/', views.help, name='help'),
    path('services/', views.services, name='services'),

    # Sidebars / Extra Pages
    path('analaytics/', views.analytics, name='analytics'),
    path('explore/', views.explore, name='explore'),
    path('toggle_bookmark/', views.toggle_bookmark, name='toggle_bookmark'),
    path('bookmarks/', views.bookmark_list, name='bookmarks'),

    # Navigation and search
    path('search-users/', views.search_users, name='search-users'),
    
    # Post-related
    path('profile/change-cover/', views.change_cover, name='change_cover'),
    path('post_list/', views.post_list, name='post_list'),
    path('post/<uuid:post_id>/', views.post_detail, name='post_detail'),
    path('post/create/', views.create_post, name='create_post'),
    path('post/<uuid:post_id>/delete/', views.delete_post, name='delete_post'),
    path("post/modal/create/", views.create_post_from_index, name="create_post_from_index"),
    path('post/<uuid:post_id>/comment/', views.add_comment, name='add_comment'),
    path('like/<uuid:post_id>/', views.like_post, name='like-post'),
    path('post_detail_modal/<uuid:post_id>/', views.post_detail_modal, name='post_detail_modal'),

    # Public profile
    path('profile/', views.profile, name='profile'),
    path('profile/<str:username>/', views.public_profile, name='public_profile'),

    # Survey pages
    path('survey/services/', views.survey_services, name='survey_services'),
    path('survey/terms/', views.survey_terms, name='survey_terms'),
    path('survey/contact/', views.survey_contact, name='survey_contact'),
    path('survey/whydata/', views.survey_whydata, name='survey_whydata'),   
    path('survey/', views.survey, name='survey'),

    #for chat
    path('chat_templates/', views.chat_templates, name='chat_templates'),

]