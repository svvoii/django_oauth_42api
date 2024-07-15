# django_oauth_42api

This tutorial shows how to setup custom oauth2 provider with `django-allauth` using 42 API as an example.  

## 0. Prerequisites

- Python 3.8
- Pipeenv

*Creating new directory for the project and virtual environment:*

```bash
mkdir django_oauth_42api
cd django_oauth_42api
pipenv shell
pipenv install django
pipenv install django-allauth
```

*Additional packages:*

```bash
pipenv install requests
pipenv install PyJWT
pipenv install cryptography
```


## 1. Create Django project

```bash
django-admin startproject my_project
cd my_project
```


## 2. Create Django apps

```bash
python manage.py startapp user_app
```
*This app will render the `profile.html` template.*  
*In your project it might be the app where the user management is done.*  

*And the following app will be responsible for the custom oauth2 provider, in our case 42 API:*  

```bash
python manage.py startapp oauth2_provider_42
```



## 3. Adding necessary settings

*In `my_project/settings.py` adding the following settings:*

```python
INSTALLED_APPS = [
	...
	# adding this to manage the sites in the admin panel
	'django.contrib.sites',

	# allauth apps
	'allauth',
	'allauth.account',
	'allauth.socialaccount',

	# our custom app
	'user_app',
	'oauth2_provider_42',
]

MIDDLEWARE = [
	...
	# adding the following from allauth
	'allauth.account.middleware.AccountMiddleware',
]

...
...
# django-allauth settings:

AUTHENTICATION_BACKENDS = [
	'django.contrib.auth.backends.ModelBackend',
	'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True

# this will show the email verification text in the console (for testing)
# In production this should be changed to a real email backend to send the verification email to the user
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```


## 4. Adding urls

*This is how the `my_project/urls.py` file shall look like:*

```python
from django.contrib import admin
from django.urls import path, include
from user_app import views


urlpatterns = [
	path('admin/', admin.site.urls),
	path('accounts/', include('allauth.urls')), # this will include all the urls provided by django-allauth
	path('accounts/profile/', views.profile, name='profile'), # this is the profile page after the user is authenticated
]
```


## 5. Adding profile template

*Creating the following directories: `my_project/user_app/templates/user_app/` and adding the `profile.html` file in it with the following content:*

```html
<h1>Logged in as: {{ request.user.username }}</h1>

<a href="{% url 'account_logout' %}">Logout</a>
```


## 6. Adding views

*In `user_app/views.py` adding the following view:*

```python
from django.shortcuts import render

def profile(request):
	return render(request, 'user_app/profile.html')
```


## 7. Adding custom oauth2 provider

*In `oauth2_provider_42` app creating `provider.py` file with the following content:*

*In `oauth2_provider_42/provider.py` file:*

```python
from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider

from .views import OAuth2Adapter42


class Account42(ProviderAccount):
	pass


class Provider42(OAuth2Provider):
	id = '42'
	name = '42 OAuth2'
	account_class = Account42
	oauth2_adapter_class = OAuth2Adapter42


	def extract_uid(self, data):
		# print(f"\textract_uid: {data}") # DEBUG # to see the data that is being extracted
		return str(data['id'])


	def extract_common_fields(self, data):
		return dict(
			email=data.get('email'),
			username=data.get('login'),
			name=data.get('name'),
			user_id=data.get('user_id')
    	)

	# This is not necessary since the default scope is 'public'. Can be customized though.
	# def get_default_scope(self):
	# 	return ['public']


provider_classes = [Provider42]

```


## 8. Adding custom oauth2 adapter

*In `oauth2_provider_42/views.py` adding the following content:*

```python
from allauth.socialaccount import app_settings
from allauth.socialaccount.adapter import get_adapter
from allauth.socialaccount.providers.oauth2.views import OAuth2Adapter, OAuth2CallbackView, OAuth2LoginView


class OAuth2Adapter42(OAuth2Adapter):
	provider_id = '42'
	oauth2_base_url_42 = 'https://api.intra.42.fr/v2'

	access_token_url = "{0}/oauth/token".format(oauth2_base_url_42)
	authorize_url = "{0}/oauth/authorize".format(oauth2_base_url_42)
	profile_url = "{0}/me".format(oauth2_base_url_42)

	def complete_login(self, request, app, token, **kwargs):
		headers = {
			'Authorization': 'Bearer {0}'.format(token.token)
		}
		response = (
			get_adapter().get_requests_session().get(self.profile_url, headers=headers)
		)
		extra_data = response.json()

		return self.get_provider().sociallogin_from_response(request, extra_data)


oauth2_login = OAuth2LoginView.adapter_view(OAuth2Adapter42)
oauth2_callback = OAuth2CallbackView.adapter_view(OAuth2Adapter42)

```


## 9. Adding urls

*In `oauth2_provider_42` app creating `urls.py` file with the following content:*

*In `oauth2_provider_42/urls.py` file:*

```python
from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns
from .provider import Provider42


urlpatterns = default_urlpatterns(Provider42)
```


## 10. Migrating the database

```bash
python manage.py migrate
```


## 11. Creating superuser

```bash
python manage.py createsuperuser
```

*Running the server.*

```bash
python manage.py runserver
```

*Login to the admin panel at `http://127.0.0.1:8000/admin/`.*  



## 12. Adding the custom provider in the admin panel

*Next step is to add the custom provider in the admin panel.*  
*To do that, go to --> `Social applications` --> `Add social application`.*  

*Fill in the following fields:*

- `Provider: 42 OAuth2`
- `Name: 42`
- `Client id: YOUR_CLIENT_ID`
- `Secret key: YOUR_SECRET`
- `Sites:` --> Choose the site you are working on (in our case it is `example.com`) the left side `Available sites` and move it to the right side `Chosen sites` by clicking the arrow pointing to the right.  

*Save the changes.*

**NOTE 1:** *To register a new application in 42 API, follow the link: [42 intra, applications](https://profile.intra.42.fr/oauth/applications) and click on `Register a new application`.*  


**NOTE 2:** *..use this : `http://127.0.0.1:8000/accounts/42/login/callback/` as the `Callback URL`.*  


*At this point, the custom provider should be added in the admin panel and the user should be able to login with 42 credentials by clicking on the `42 OAuth2` button on this page: `http://127.0.0.1/accounts/login/`.*  



## 13. Adding authentication with social account

*To add the authentication with social account, for example `Google`, simply add the respective provider in the `INSTALLED_APPS` in `settings.py` file.*

```python
INSTALLED_APPS = [
	...
	'allauth.socialaccount.providers.google',
	...
]
```

*And repeat the step 12 to add the respective provider in the admin panel with proper `Provider`, `Client id` and `Secret key` values.*  


**NOTE:** *For more providers, check the documentation: [django-allauth](https://docs.allauth.org/en/latest/installation/quickstart.html)*  


Simolar tutorial on `How to setup 3rd party authentication to sign in to the django app with google account.` can be found [in this repository](https://github.com/svvoii/django_oauth_google).  

