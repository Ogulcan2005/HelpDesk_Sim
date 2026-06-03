from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from .models import ClassGroup


# -----------------------
# LOGIN
# -----------------------
def user_login(request):

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)

        if user:
            login(request, user)
            return redirect("home")

        return render(request, "accounts/login.html", {
            "error": "Invalid credentials"
        })

    return render(request, "accounts/login.html")


# -----------------------
# REGISTER
# -----------------------
def register(request):

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")

        if password != password2:
            return render(request, "accounts/register.html", {
                "message": "Passwords do not match"
            })

        if User.objects.filter(username=email).exists():
            return render(request, "accounts/register.html", {
                "message": "Account already exists"
            })

        User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        return render(request, "accounts/register.html", {
            "message": "Account created successfully"
        })

    return render(request, "accounts/register.html")


# -----------------------
# HOME (CLASS LIST)
# -----------------------
@login_required
def home(request):

    groups = ClassGroup.objects.all()

    return render(request, "accounts/class_list.html", {
        "groups": groups
    })


# -----------------------
# CLASS DETAIL
# -----------------------
@login_required
def class_detail(request, pk):

    group = get_object_or_404(ClassGroup, pk=pk)

    return render(request, "accounts/class_detail.html", {
        "group": group,
        "students": group.students.all(),
        "teachers": group.teachers.all()
    })


# -----------------------
# LOGOUT
# -----------------------
def user_logout(request):
    logout(request)
    return redirect("login")


# -----------------------
# ADMIN ONLY
# -----------------------
@staff_member_required
def admin_only(request):
    return render(request, "accounts/admin_only.html")