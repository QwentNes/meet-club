from allauth.account.forms import SignupForm
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit
from django import forms
from .models import UserProfile, ProfileImage, CoverImage

# Форма регистрации
class UserSignUpForm(SignupForm):
    first_name = forms.CharField(max_length=200, label='Имя')
    last_name = forms.CharField(max_length=200, label='Фамилия')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].label = 'Электронная почта'
        self.fields['username'].label = 'Имя пользователя'
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Подтверждение пароля'
        self.helper = FormHelper()
        self.helper.form_class = 'mt-3'
        self.helper.layout = Layout(
            Div(
                Div('first_name', css_class='col'),
                Div('last_name', css_class='col'),
                css_class='form-row',
            ),
            Div('email'),
            Div('username'),
            Div('password1'),
            Div('password2'),
            Submit('submit', 'Зарегистрироваться', css_class='w-100 btn btn-primary'),
        )

# Форма профиля пользователя
class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        exclude = ['id', 'user', 'friends', 'followers']
        labels = {
            'other_name': 'Другое имя',
            'phone': 'Телефон',
            # Добавьте другие поля модели UserProfile
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

# Форма редактирования данных пользователя
class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username']
        labels = {
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Электронная почта',
            'username': 'Имя пользователя',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

# Форма настроек профиля
class UserProfileSettingsForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['other_name', 'phone']
        labels = {
            'other_name': 'Другое имя',
            'phone': 'Телефон',
        }

# Форма изображения профиля
class UserProfileImageForm(forms.ModelForm):
    class Meta:
        model = ProfileImage
        fields = ['profile_image']
        labels = {
            'profile_image': 'Изображение профиля',
        }

# Форма обложки профиля
class UserCoverImageForm(forms.ModelForm):
    class Meta:
        model = CoverImage
        fields = ['cover_image']
        labels = {
            'cover_image': 'Обложка',
        }