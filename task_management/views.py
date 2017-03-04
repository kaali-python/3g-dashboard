from django.shortcuts import render, get_object_or_404, redirect, HttpResponse
from django.contrib.auth.models import User, Permission
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.http import Http404

import json

from .forms import UserLoginForm, TaskAssignForm
from .models import Task
from content_uploader.models import Uploader, MyUser
from course_management.models import Course, Subject, Chapter, Topic, ModuleData
from classes.models import ClassCategory


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


def get_uploaders(request):
    admin_id = request.user.id
    uploader_list = []
    for uploader in MyUser.objects.filter(owner=admin_id):
        uploader_permissions = []
        uploader_module_permissions = Permission.objects.filter(content_type_id__model='moduledata', user=uploader.id)
        for module_permission in uploader_module_permissions:
            uploader_permissions.append(ModuleData.objects.get(code=module_permission.name))
        uploader_list.append({'uploader': uploader, 'permissions': uploader_permissions})
    print(uploader_list)
    return render(request, 'select_uploader.html', {'uploader_list': uploader_list})


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


def assign_task(request, uploader_id):
    """
    To assign task to the uploader by the admin.
    :param request:
    :param uploader_id:
    :return:
    """
    form = TaskAssignForm(request.POST or None)
    if form.is_valid():
        task = form.save(commit=False)
        task.status = 'PENDING'
        task.assign_to_id = Uploader.objects.values_list('id', flat=True).get(user_id=uploader_id)
        task.assigned_by_id = request.user.id
        task.module_permission = ModuleData.objects.get(code=request.POST.get('module_permission'))
        task.save()
        return redirect('task_management:dashboard')
    else:
        print('ERROR !!!!!!')
        print(form.errors)

    uploader_data = MyUser.objects.get(id=uploader_id)
    class_data = ClassCategory.objects.filter()

    return render(request, 'assign_task.html', {'form': form, 'class_data': class_data,
                                                'uploader': uploader_data})


def permissions(request, uploader_id):
    """
    Get the permissions allotted to the user.
    :param request:
    :param uploader_id:
    :return:
    """
    subject_content = []
    chapter_content = []
    topic_content = []
    module_content = []
    course_data = []

    uploader_id = int(uploader_id)

    # course_perms = Permission.objects.filter(content_type_id__model='course', user=uploader_id)
    # for course in course_perms:
    #     course_data.append(Course.objects.values('title', 'code', 'class_category_id').get(code=course.name))
    # for course in course_data:
    #     course['code'] = str(course['code'])
    #     course['class_category_id'] = str(course['class_category_id'])
    #
    # subject_perms = Permission.objects.filter(content_type_id__model='subject', user=uploader_id)
    # for subject in subject_perms:
    #     subject_content.append(Subject.objects.values('title', 'code', 'course_id').get(code=subject.name))
    # for subject in subject_content:
    #     subject['code'] = str(subject['code'])
    #     subject['course_id'] = str(subject['course_id'])
    #
    # chapter_perms = Permission.objects.filter(content_type_id__model='chapter', user=uploader_id)
    # for chapter in chapter_perms:
    #     chapter_content.append(Chapter.objects.values('title', 'code', 'subject_id').get(code=chapter.name))
    # for chapter in chapter_content:
    #     chapter['code'] = str(chapter['code'])
    #     chapter['subject_id'] = str(chapter['subject_id'])
    #
    # topic_perms = Permission.objects.filter(content_type_id__model='topic', user=uploader_id)
    # for topic in topic_perms:
    #     topic_content.append(Topic.objects.values('title', 'code', 'chapter_id').get(code=topic.name))
    # for topic in topic_content:
    #     topic['code'] = str(topic['code'])
    #     topic['chapter_id'] = str(topic['chapter_id'])

    topic_perms = []
    for module in module_content:
        topic_perms.append(Topic.objects.values('title', 'code', 'chapter_id').get(code=module.topic_id))
    # for

    module_perms = Permission.objects.filter(content_type_id__model='moduledata', user=uploader_id)
    for module in module_perms:
        module_content.append(ModuleData.objects.values('title', 'code', 'topic_id').get(code=module.name))
    for module in module_content:
        module['code'] = str(module['code'])
        module['topic_id'] = str(module['topic_id'])

    perms = {'course_permissions': course_data, 'subject_permissions': subject_content, 'chapter_permissions': chapter_content,
             'topic_permissions': topic_content, 'module_permissions': module_content}

    print('Ajax call success !!!')
    return HttpResponse(json.dumps(perms))


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
        task.status = 'PENDING'
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


def task_complete(request, task_id):
    """
    To change the status of the task to completed, by the uploader.
    :param request:
    :param task_id:
    :return:
    """
    if request.user.is_active:

        task = get_object_or_404(Task, pk=task_id)
        print(task.status)
        task.status = 'UNDER REVIEW'
        print(task.status)
        task.save()
        return redirect('task_management:dashboard')
    else:
        raise Http404


def upload_task_data(request, task_id):
    """
    Open view for uploading data
    :param request:
    :param task_id:
    :return:
    """
    if request.user.is_active:
        task = get_object_or_404(Task, pk=task_id)
        return render(request, 'detail.html', {'task': task})
