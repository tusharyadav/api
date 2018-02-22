from rest_framework import generics
from rest_framework.response import Response
#from rest_framework import authentication, permissions


from rest_framework.views import APIView
from django.shortcuts import render, HttpResponse, Http404

import logging
import json
logging.basicConfig()
logger = logging.getLogger(__name__)

	
##
#	sanitize: method to remove special characters from word
#	params:
#		word : word to sanitize 
##
def sanitize(word):
	import re
	s = ""
	r = re.compile("[a-zA-Z]")
	for c in word:
		if r.match(c):
			s = s+c
	return s.lower()


##
#
##
def find_common_set(file, set_final):
	a = f.readlines()
	set1 = set()			
	for line in a:
		words = line.rstrip().split(' ')
		for word in words:
			set1.add(sanitize(word))
	if set_final:
		return set_final.intersection(set1)
	else:
		return set1


##
#	returns formatted error message
#
##
def ErrorResponse(message):
	error = { "ERROR": message }
	return HttpResponse(json.dumps(error))


##
#
##
def ValidateInput(file_name):
	if not file_name:
		logger.error("Filenames are not given")
		return ErrorResponse("file_name is a required parameter")

	file_names = file_name.split(',')

	if len(file_names) <3:
		logger.error("Minimum number of files are 3, ",len(file_names)," Given")
		return ErrorResponse("Minimum number of files are 3")

	return file_names



##
#
##
def GetCommonWords(file_names):
	set_final = set()
	for f_name in file_names:
		try:
			with open(f_name,'r') as f:
				set_final = find_common_set(f, set_final)
				
		except IOError as e:
			logger.error("I/O error({0}): {1}".format(e.errno, e.strerror))
			raise Http404

	return list(set_final)


 
##
#
##
class CommonWords(generics.ListAPIView):

	def get(self, request):
		
		file_name = request.GET.get("file_name",None)

		file_names = ValidateInput(file_name)

		common_words = GetCommonWords(file_names)

		return HttpResponse(json.dumps(common_words))

