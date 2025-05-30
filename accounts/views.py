from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q
from django.views.generic import TemplateView, View, ListView, DetailView
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import update_session_auth_hash
from allauth.account.views import SignupView
from allauth.account.forms import ChangePasswordForm
from django.contrib.auth.forms import PasswordChangeForm
from accounts.forms import (
	UserSignUpForm,
	UserProfileForm,
	UserForm,
	UserProfileSettingsForm,
	UserProfileImageForm,
	UserCoverImageForm
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from posts.models import Post, PostImage
from accounts.utils import get_all_photos, get_friend_request_object, get_user_post_feeds, get_all_post_photos, filter_user_queryset
from posts.decorators import AjaxRequiredOnlyMixin
from accounts.models import UserProfile, FriendRequest

# Create your views here.

class UserSignUpView(SignupView):
	form_class = UserSignUpForm

user_signup_view = UserSignUpView.as_view()

class ProfilePostView(LoginRequiredMixin, TemplateView):
	template_name = 'accounts/profile_post.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data()
		user = get_object_or_404(User, pk=kwargs['user_pk'])
		context['posts'] = get_user_post_feeds(self.request, kwargs['user_pk'])
		context['recent_photos'] = get_all_photos(self.request, user.pk)[:6]
		context['user'] = user
		context['page'] = 'profile_post'
		context['userprofile_form'] = UserProfileForm(instance=user.userprofile)
		context['user_form'] = UserForm(instance=user)
		return context

profile_post_view = ProfilePostView.as_view()

class ProfileAboutView(LoginRequiredMixin, TemplateView):
	template_name = 'accounts/profile_about.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data()
		user = get_object_or_404(User, pk=kwargs['user_pk'])
		context['user'] = user
		context['page'] = 'profile_about'
		context['userprofile_form'] = UserProfileForm(instance=user.userprofile)
		context['user_form'] = UserForm(instance=user)
		# print(user.userprofile._meta.get_fields())
		field_dict = {}
		icon_classes = {'marital_status': 'fa fa-heart', 'birth_date': 'fa fa-calendar', 'occupation': 'fa fa-briefcase', 'location': 'fa fa-map-marker-alt', 'date_joined': 'fa fa-calendar', 'email': 'fa fa-envelope'}
		field_notes = {'marital_status': 'Статус', 'birth_date': 'День рождения', 'occupation': 'Занятость', 'location': 'Живет в', 'date_joined': 'Присоединился', 'email': 'Email'}
		for field in user.userprofile._meta.fields:
			if field.name in ('marital_status', 'birth_date', 'occupation', 'location'):
				field_dict[field.name] = {
					'icon_class': icon_classes[field.name],
					'field_note': field_notes[field.name],
					'field_value': getattr(user.userprofile, field.name),
					'model_name': 'userprofile',
				}
		for field in user._meta.fields:
			if field.name in ('date_joined', 'email',):
				field_dict[field.name] = {
					'icon_class': icon_classes[field.name],
					'field_note': field_notes[field.name],
					'field_value': getattr(user, field.name),
					'model_name': 'user',
				}
		context['field_dict'] = field_dict
		return context

profile_about_view = ProfileAboutView.as_view()

class ProfilePhotosView(LoginRequiredMixin, TemplateView):
	template_name = 'accounts/profile_photos.html'

	def get_context_data(self, *args, **kwargs):
		context = super().get_context_data(*args, **kwargs)
		user = User.objects.get(pk=kwargs['user_pk'])
		context['user'] = user
		context['post_photos'] = get_all_post_photos(self.request, kwargs['user_pk'])
		context['page'] = 'profile_photos'
		return context

profile_photos_view = ProfilePhotosView.as_view()

class UpdateUserProfileDataView(UserPassesTestMixin, LoginRequiredMixin, View):
	def dispatch(self, request, *args, **kwargs):
		self.user = get_object_or_404(User, pk=kwargs['user_pk'])
		return super().dispatch(request, *args, **kwargs)

	def post(self, request, *args, **kwargs):
		form = UserProfileForm(
			request.POST,
			instance=self.user.userprofile
		)
		if form.is_valid():
			form.save()
		return redirect(request.META.get('HTTP_REFERER'))

	def test_func(self):
		return self.request.user == self.user 

update_user_profile_data_view = UpdateUserProfileDataView.as_view()

class UpdateUserDataView(UserPassesTestMixin, LoginRequiredMixin, View):
	def dispatch(self, request, *args, **kwargs):
		self.user = get_object_or_404(User, pk=kwargs['user_pk'])
		return super().dispatch(request, *args, **kwargs)

	def post(self, request, *args, **kwargs):
		form = UserForm(
			request.POST,
			instance=self.user,
		)
		if form.is_valid():
			form.save()
		return redirect(request.META.get('HTTP_REFERER'))

	def test_func(self):
		return self.request.user == self.user 

update_user_data_view = UpdateUserDataView.as_view()

class UserSettingsView(LoginRequiredMixin, TemplateView):
	template_name = 'accounts/settings.html'

	def get_context_data(self, *args, **kwargs):
		context = super().get_context_data(*args, **kwargs)
		context['profile_form'] = UserProfileSettingsForm(instance=self.request.user.userprofile)
		context['user_form'] = UserForm(instance=self.request.user)
		context['password_form'] = PasswordChangeForm(self.request.user)
		return context

	def post(self, request, *args, **kwargs):
		data = request.POST
		user_form = UserForm(data, instance=request.user)
		profile_form = UserProfileSettingsForm(data, instance=request.user.userprofile) 
		password_form = PasswordChangeForm(request.user, data)
		if 'user-profile-form' in data:
			if user_form.is_valid() and profile_form.is_valid():
				user_form.save()
				profile_form.save()
				messages.success(request, 'Profile updated successfully')
				return redirect('user_settings')
		elif 'password-form' in data:
			if password_form.is_valid():
				user = password_form.save()
				update_session_auth_hash(request, user)
				messages.success(request, 'Your password was changed successfully')
				return redirect('user_settings')
			else:
				messages.error(request, 'An error occured from your input')
		return self.render_to_response({'user_form': user_form, 'profile_form': profile_form, 'password_form': password_form,})

user_settings_view = UserSettingsView.as_view()

class UpdateUserProfileView(UserPassesTestMixin, LoginRequiredMixin, TemplateView):
	template_name = 'accounts/profile-edit.html'

	def dispatch(self, request, *args, **kwargs):
		self.user = User.objects.get(pk=kwargs['user_pk'])
		return super().dispatch(request, *args, **kwargs)

	def post(self, request, *args, **kwargs):
		user_form = UserForm(request.POST, instance=self.user)
		profile_form = UserProfileForm(request.POST, instance=self.user.userprofile)
		profile_image_form = UserProfileImageForm(request.POST, request.FILES)
		cover_image_form = UserCoverImageForm(request.POST, request.FILES)

		if user_form.is_valid() and profile_form.is_valid() and profile_image_form.is_valid() and cover_image_form.is_valid():
			user_form.save()
			user_profile = profile_form.save()
			if request.FILES.get('profile_image'):
				profile_image = profile_image_form.save(commit=False)
				profile_image.userprofile = user_profile
				profile_image.save()
			if request.FILES.get('cover_image'):
				cover_image = cover_image_form.save(commit=False)
				cover_image.userprofile = user_profile
				cover_image.save()
			messages.success(request, 'Your Profile Has Been Updated Successfully')
			return redirect(request.META.get('HTTP_REFERER'))
		return self.render_to_response({
			'user_form': user_form,
			'profile_form': profile_form,
			'profile_image_form': profile_image_form,
			'cover_image_form': cover_image_form,
		})

	def get_context_data(self, *args, **kwargs):
		context = super().get_context_data(*args, **kwargs)
		context['user'] = self.user
		context['user_form'] = UserForm(instance=self.user)
		context['profile_form'] = UserProfileForm(instance=self.user.userprofile)
		context['profile_image_form'] = UserProfileImageForm()
		context['cover_image_form'] = UserCoverImageForm()
		return context 

	def test_func(self):
		return self.request.user == self.user

update_user_profile_view = UpdateUserProfileView.as_view()

class FollowView(AjaxRequiredOnlyMixin, View):
	def post(self, request, *args, **kwargs):
		if not request.user.is_authenticated:
			return JsonResponse({'status': 'not logged in'})
		userprofile = User.objects.get(pk=kwargs['user_pk']).userprofile
		user = request.user
		if user in userprofile.followers.all():
			userprofile.followers.remove(user)
			action = 'unfollow'
		else:
			userprofile.followers.add(user)
			action = 'follow'

		return JsonResponse(
			{
				'status': 'ok',
				'action': action,
				'num_of_followers': userprofile.followers.all().count(),
			}
		)

follow_view = FollowView.as_view()

class FollowListView(LoginRequiredMixin, View):
	def get(self, request, *args, **kwargs):
		user = User.objects.get(pk=kwargs['user_pk'])
		if kwargs['follow_type'] == 'followers':
			template_name = 'accounts/user_followers_list.html'
			page = 'followers'
		elif kwargs['follow_type'] == 'following':
			template_name = 'accounts/user_following_list.html'
			page = 'following'
		context = {'user': user, 'page': page,}
		return render(request, template_name, context)

follow_list_view = FollowListView.as_view()

class SendFriendRequestView(LoginRequiredMixin, UserPassesTestMixin, View):
	def post(self, request, *args, **kwargs):
		to_user = User.objects.get(pk=kwargs['to_user_pk'])
		obj, created = FriendRequest.objects.get_or_create(
			from_user=request.user, to_user=to_user
		)
		if not created:
			messages.warning(request, 'Friend Request Already Sent')
		
		return redirect(request.META.get('HTTP_REFERER'))

	def test_func(self):
		to_user = User.objects.get(pk=self.kwargs['to_user_pk'])
		return self.request.user != to_user and to_user not in self.request.user.userprofile.friends.all()

send_friend_request_view = SendFriendRequestView.as_view()

class DeleteFriendRequestView(LoginRequiredMixin, UserPassesTestMixin, View):
	def post(self, request, *args, **kwargs):
		get_friend_request_object(
			to_user_pk=kwargs['to_user_pk'], from_user_pk=kwargs['from_user_pk']
		).delete()
		messages.error(request, 'Friend Request Deleted')
		return redirect(request.META.get('HTTP_REFERER'))

	def test_func(self):
		friend_request = get_friend_request_object(
			to_user_pk=self.kwargs['to_user_pk'], from_user_pk=self.kwargs['from_user_pk']
		)
		return self.request.user == friend_request.from_user or self.request.user == friend_request.to_user

delete_friend_request_view = DeleteFriendRequestView.as_view()

class AcceptFriendRequestView(UserPassesTestMixin, LoginRequiredMixin, View):
	def dispatch(self, request, *args, **kwargs):
		self.friend_request = get_friend_request_object(
			to_user_pk=request.user.pk, from_user_pk=kwargs['from_user_pk']
		)
		self.to_user, self.from_user = self.friend_request.to_user, self.friend_request.from_user
		return super().dispatch(request, *args, **kwargs)
	def post(self, request, *args, **kwargs):
		self.to_user.userprofile.friends.add(self.from_user)
		self.from_user.userprofile.friends.add(self.to_user)
		self.friend_request.delete()
		return redirect(request.META.get('HTTP_REFERER'))

	def test_func(self):
		return self.request.user == self.to_user

accept_friend_request_view = AcceptFriendRequestView.as_view()

class FriendRequestListView(LoginRequiredMixin, TemplateView):
	template_name = 'accounts/friend_request_list.html'

	def get_context_data(self, *args, **kwargs):
		context = super().get_context_data(*args, **kwargs)
		fr_users = FriendRequest.objects.filter(
			to_user=self.request.user
		).values_list('from_user', flat=True)
		context['friend_request_from_users'] = [User.objects.get(pk=pk) for pk in fr_users]
		context['page'] = 'friend_request_list'
		return context

friend_request_list_view = FriendRequestListView.as_view()

class FriendListView(LoginRequiredMixin, TemplateView):
	template_name = 'accounts/friend_list.html'

	def get_context_data(self, *args, **kwargs):
		context = super().get_context_data(*args, **kwargs)
		user = User.objects.get(pk=kwargs['user_pk'])
		search_friend = self.request.GET.get('search_friend', '')
		context['friends'] = filter_user_queryset(user.userprofile.friends.all(), search_friend)
		context['user'] = user
		context['page'] = 'profile_friends'
		return context

friend_list_view = FriendListView.as_view()

class RemoveFriendView(LoginRequiredMixin, View):
	def get(self, request, *args, **kwargs):
		friend = User.objects.get(pk=kwargs['user_pk'])
		friend_name = friend.userprofile.full_name
		request.user.userprofile.friends.remove(friend)
		friend.userprofile.friends.remove(request.user)
		messages.error(request, f'You have removed {friend_name} as your friend')
		return redirect(request.META.get('HTTP_REFERER'))

remove_friend_view = RemoveFriendView.as_view()

class UserSearchView(LoginRequiredMixin, ListView):
	template_name = 'accounts/user_search.html'

	def get_queryset(self):
		query = self.request.GET.get('query', '')
		users = User.objects.all()
		queryset = filter_user_queryset(users, query)
		return queryset

user_search_view = UserSearchView.as_view()

class UserGroupList(LoginRequiredMixin, DetailView):
	model = User
	template_name = 'accounts/profile_groups.html'

	def get_context_data(self, *args, **kwargs):
		context = super().get_context_data(*args, **kwargs)
		context['page'] = 'profile_groups'
		return context

user_group_list = UserGroupList.as_view()

def about_program_view(request):
    context = {
        'version': '1.0.0',
        'authors': [
            'Королев Егор Алексеевич',
            'Фомин Артем Михайлович',
            'Цымбалов Владислав Анатольевич',
            'Заельская Наталья Александровна',
        ],
        'license': '''Социальная сеть MeetClub распространяется под лицензией MIT. 
        Вы можете свободно использовать, модифицировать и распространять программное обеспечение 
        при условии сохранения информации об авторских правах. Авторы не несут ответственности 
        за любые последствия использования данного ПО. Коммерческое использование допускается 
        только с письменного согласия правообладателей.'''
    }
    return render(request, 'accounts/about_program.html', context)