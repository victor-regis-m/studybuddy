from django.forms import ModelForm, Form
from .models import Room, Message, User, Profile


class RoomForm(ModelForm):
    class Meta:
        model = Room
        fields = '__all__'
        exclude = ['host', 'participants']


class MessageForm(ModelForm):
    class Meta:
        model = Message
        fields = '__all__'


class UserForm(ModelForm):
    class Meta:
        model = User
        fields = ['username']


class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        exclude = ['user']