from django.shortcuts import render, redirect
from django.db.models import Count, Q
from .models import Room, Topic, User, Message, Profile
from .form import RoomForm, UserForm, ProfileForm
from functools import reduce
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse


def logout_view(request):
    logout(request)
    return redirect('home')


def login_page(request):
    page = 'login'
    context = {'page': page}
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print(username)
        try:
            user = User.objects.get(username=username)
        except:
            messages.error(request, 'User does not exist')
        user = authenticate(request, username=username, password=password)
        request.profile = Profile.objects.get(user=user)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'base/login_register.html', context)


def register(request):
    form_user = UserCreationForm()
    form_profile = ProfileForm()
    context = {'form_user': form_user, 'form_profile': form_profile}
    if request.method == 'POST':
        form_user = UserCreationForm(request.POST)
        if User.objects.filter(username=form_user['username'].value()).exists():
            messages.error(request, 'Username already in use')
            return redirect('register')
        if form_user.is_valid():
            u = form_user.save()
            form_profile = ProfileForm(request.POST, request.FILES)
            if form_profile.is_valid():
                p = form_profile.save(commit=False)
                p.user = u
                p.save()
                return redirect('login')
            else:
                User.objects.filter(id=u.id).delete()
                messages.error(request, 'An error occurred during registration')
        else:
            messages.error(request, 'An error occurred during registration')
    return render(request, 'base/login_register.html', context)


def home(request):
    q = request.GET.get('q') if request.GET.get('q') is not None else ''
    rooms = Room.objects.filter(Q(topic__name__icontains=q) | Q(name__icontains=q) | Q(description__icontains=q))
    current_room_count = rooms.count()
    topic_count = Topic.objects.values('name').annotate(count=Count('room'))
    all_count = reduce(lambda _, x: _ + x['count'], topic_count, 0)
    recent_messages = Message.objects.filter(Q(room__topic__name__icontains=q))[:5]
    context = {'rooms': rooms, 'topic_count': topic_count, 'all_count': all_count,
               'current_room_count': current_room_count, 'recent_messages': recent_messages}
    return render(request, 'base/home.html', context)


def room(request, pk):
    def handle_post(request):
        editing_id = request.POST.get('message_id')
        if editing_id is not None:
            edited_message = Message.objects.get(id=editing_id)
            edited_message.body = request.POST.get('body')
            edited_message.edited = True
            edited_message.save()
        else:
            sent_message = Message.objects.create(
                user=request.user,
                room=rooms,
                body=request.POST.get('body'),
                edited=False
            )
            rooms.participants.add(request.user)
            sent_message.save()
        return redirect('room', rooms.id)

    rooms = Room.objects.get(id=pk)
    is_owner = rooms.host == request.user
    participants = rooms.participants.all()
    context = {'room': rooms, 'is_owner': is_owner, 'participants': participants}
    if request.method == 'POST':
        handle_post(request)
    elif request.method == 'GET':
        try:
            editing_message = Message.objects.get(id=request.GET.get('e'))
            context['editing_message'] = editing_message
        except:
            pass
    room_messages = rooms.message_set.all().order_by('-created')
    context['room_messages'] = room_messages
    return render(request, 'base/room.html', context)


def user_profile(request, pk):
    user = User.objects.get(id=pk)
    q = request.GET.get('q') if request.GET.get('q') is not None else ''
    rooms = user.room_set.filter(Q(topic__name__icontains=q) | Q(name__icontains=q) | Q(description__icontains=q),
                                 host=user)
    recent_messages = user.message_set.all()[:5]
    topic_count = Topic.objects.filter(room__host=user).values('name').annotate(count=Count('room'))
    all_count = reduce(lambda _, x: _ + x['count'], topic_count, 0)
    context = {'user': user, 'rooms': rooms, 'recent_messages': recent_messages, 'topic_count': topic_count,
               'all_count': all_count, 'pk': pk}
    return render(request, 'base/profile.html', context)


@login_required(login_url='login')
def create_room(request):
    form = RoomForm()
    topics = Topic.objects.all()
    context = {'form': form, 'topics': topics}
    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        print('Name is ')
        print(topic_name)
        topic, created = Topic.objects.get_or_create(name=topic_name)
        Room.objects.create(
            host=request.user,
            name=request.POST.get('name'),
            topic=topic,
            description=request.POST.get('description')
        )
        return redirect('home')
    return render(request, 'base/room_form.html', context)


@login_required(login_url='login')
def update_room(request, pk):
    rooms = Room.objects.get(id=pk)
    topics = Topic.objects.all()
    if rooms.host == request.user:
        form = RoomForm(instance=rooms)
        context = {'form': form, 'topics': topics, 'rooms': rooms}
        if request.method == 'POST':
            topic_name = request.POST.get('topic')
            print('Name is ')
            print(topic_name)
            topic, created = Topic.objects.get_or_create(name=topic_name)
            rooms.name = request.POST.get('name')
            rooms.topic = topic
            rooms.description = request.POST.get('description')
            rooms.save()
            return redirect('home')
        return render(request, 'base/room_form.html', context)
    else:
        return HttpResponse("You don't have permission to perform this action")


@login_required(login_url='login')
def delete_room(request, pk):
    room = Room.objects.get(id=pk)
    if room.host == request.user:
        if request.method == 'POST':
            room.delete()
            return redirect('home')
        return render(request, 'base/delete.html', {'obj': room})
    else:
        return HttpResponse("You don't have permission to perform this action")


@login_required(login_url='login')
def delete_message(request, pk):
    message = Message.objects.get(id=pk)
    if message.user == request.user:
        if request.method == 'POST':
            message.delete()
            return redirect('room', message.room.id)
        return render(request, 'base/delete.html', {'obj': message})
    else:
        return HttpResponse("You don't have permission to perform this action")


@login_required(login_url='login')
def update_user(request):
    user = request.user
    profile = Profile.objects.get(user=user)
    form_user = UserForm(instance=user)
    form_profile = ProfileForm(instance=profile)
    if request.method == 'POST':
        form_user = UserForm(request.POST, instance=user)
        form_profile = ProfileForm(request.POST, request.FILES, instance=profile)
        if form_user.is_valid() and form_profile.is_valid():
            form_user.save()
            form_profile.save()
            return redirect('user-profile', pk=user.id)
    return render(request, 'base/update_user.html', {'form_user': form_user, 'form_profile': form_profile})


def topics_page(request):
    q = request.GET.get('q') if request.GET.get('q') is not None else ''
    topics = Topic.objects.filter(name__icontains=q)
    topic_count = topics.values('name').annotate(count=Count('room'))
    all_count = reduce(lambda _, x: _ + x['count'], topic_count, 0)
    context = {'topic_count': topic_count, 'all_count': all_count}
    return render(request, 'base/topics.html', context)


def activity_page(request):
    q = request.GET.get('q') if request.GET.get('q') is not None else ''
    recent_messages = Message.objects.filter(Q(room__topic__name__icontains=q))[0:4]
    return render(request, 'base/activity.html', {'recent_messages': recent_messages})

