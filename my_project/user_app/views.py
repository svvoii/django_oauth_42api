from django.shortcuts import render


def profile(request):
	return render(request, 'user_app/profile.html')

