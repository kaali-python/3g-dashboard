from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User, Permission
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.http import Http404
from django.db.models import Q

from .forms import UserLoginForm, TaskAssignForm
from .models import Task
from content_uploader.models import Uploader
from classes.models import MyUser


def login_user(request):
    """
    To login the user and get all the tasks of the user.
    :param request:
    :return: The list of tasks allotted to the user.
    """
    if request.method == 'POST':

        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user.is_active:
                login(request, user)
                return redirect('task_management:dashboard')

            else:
                return render(request, 'login.html', {'error_message': 'Account disabled'})

    else:
        return render(request, 'login.html')


def logout_user(request):
    """
    To logout the user and redirect to the login page.
    :param request:
    :return:
    """
    logout(request)
    return redirect('task_management:login')


def uploader_dashboard(request):
    """
    Dashboard for the uploader.
    :param request:
    :return:
    """
    uploader = Uploader.objects.filter(user_id=request.user.id).values_list('id', flat=True).get()
    tasks = Task.objects.filter(assign_to_id=uploader)
    return render(request, 'dashboard.html', {'tasks': tasks})


def dashboard(request):
    """
    Dashboard for the admin.
    :param request:
    :return:
    """
    if request.user.is_staff:
        tasks = Task.objects.filter(assigned_by_id=request.user.id)
        return render(request, 'admin_dashboard.html', {'tasks': tasks})
    else:
        tasks = Task.objects.filter(assign_to_id__user_id=request.user.id)
        return render(request, 'dashboard.html', {'tasks': tasks})


def assign_task(request):
    """
    To assign task to the uploader by the admin.
    :param request:
    :return:
    """
    form = TaskAssignForm(request.POST or None)

    if form.is_valid():
        task = form.save(commit=False)
        task.status = 'ASSIGN'
        task.assign_to_id = request.POST.get('assign_to')
        task.assigned_by_id = request.user.id
        task.save()
        return redirect('task_management:dashboard')
    else:
        print(form)
        # form = TaskAssignForm()

    uploader_list = Uploader.objects.filter(user__owner=request.user.id)
    perms = permissions(request.user.id)
    return render(request, 'assign_task.html', {'form': form, 'uploaders': uploader_list, 'permissions': perms})


def permissions(user_id):
    """
    Get the permissions allotted to the user.
    :param user_id:
    :return:
    """
    perms = {}
    board_perms = Permission.objects.filter(content_type_id__model='boardcategory', user=user_id, )
    course_perms = Permission.objects.filter(content_type_id__model='course', user=user_id, name__contains='crud')

    return perms


def edit_task(request, task_id):
    """
    To edit the task.
    :param request:
    :param task_id:
    :return:
    """
    task = get_object_or_404(Task, pk=task_id)
    form = TaskAssignForm(request.POST or None, instance=task)
    if form.is_valid():
        task = form.save(commit=False)
        task.status = 'ASSIGN'
        task.assign_to_id = request.POST.get('assign_to')
        task.assigned_by_id = request.user.id
        form.save()
        return redirect('task_management:dashboard')
    uploader_list = Uploader.objects.filter(user__owner=request.user.id)
    return render(request, 'assign_task.html', {'form': form, 'uploaders': uploader_list})


def delete_task(request, task_id):
    """
    To delete a task, can only be done by the admin or super-admin.
    :param request:
    :param task_id:
    :return:
    """
    if request.user.is_staff or request.user.is_superuser:
        task = get_object_or_404(Task, pk=task_id)
        task.delete()
        return redirect('task_management:dashboard')
    else:
        raise Http404
