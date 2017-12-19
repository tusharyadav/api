# from django.conf import settings
# from rest_framework.views import APIView
# from rest_framework.response import Response

# class TwitterAPIView(APIView):
#     def get(self, request,*args , **kwargs):

#         print "testing" 
#         return Response({})
#         # return Response(serializer.data)

import django_filters
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import authentication, permissions
from django.contrib.auth.models import User
from rest_framework import serializers

class UserFilter(django_filters.FilterSet):
	class Meta:
		model=User
		fields = ('first_name','email',)

class UserSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
	
class ListUsers(generics.ListAPIView):
	queryset = User.objects.all()	
	serializer_class = UserSerializer
	filter_class = UserFilter

