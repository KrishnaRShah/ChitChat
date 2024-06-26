from django.contrib.auth import authenticate
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from .models import User
from .serializers import *
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import json
import logging
from functools import wraps
import time

logger = logging.getLogger(__name__)

def retry_on_failure(attempts=3, delay=1, exceptions=(Exception,)):
    """
    A decorator that retries a function if it raises an exception.

    Parameters:
    - attempts (int): The number of attempts to make before giving up. Defaults to 3.
    - delay (int): The delay between attempts in seconds. Defaults to 1.
    - exceptions (tuple): A tuple of exception classes that should trigger a retry. Defaults to (Exception,).
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal attempts  # Allows access to the 'attempts' parameter from the enclosing scope
            while attempts > 1:  # Try executing the function until attempts run out
                try:
                    return func(*args, **kwargs)  # Attempt to call the function
                except exceptions as e:  # If specified exceptions are raised, log error and retry
                    logger.error(f"Attempt failed with error: {e}. Retrying...")
                    time.sleep(delay)  # Wait for the specified delay before retrying
                    attempts -= 1  # Decrement the attempts counter
            try:
                return func(*args, **kwargs)  # Final attempt to call the function
            except exceptions as e:  # If it fails, log error and return a maintenance message
                logger.error(f"All attempts failed. Returning maintenance message. Error: {e}")
                return Response({'message': 'Server is down for Maintenance'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return wrapper
    return decorator



# Create your views here.
def chat(request):
    return render(request, 'chat/chatroom.html')


@api_view(['POST'])
@retry_on_failure(attempts=3, delay=1, exceptions=(Exception,))
def loginUser(request):
    try:
        message = json.loads(request.body)
        username = message.get('userName')
        password = message.get('password')
    except json.JSONDecodeError:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    except KeyError:
        return Response(status=status.HTTP_400_BAD_REQUEST)

    # Manually check the username and password against the database
    try:
        _ = User.objects.get(userName=username, password=password)
        # If the user is found, return a success response
        return JsonResponse({"username": username, "id":_.id, "chatroom": "global"}, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        # If the user is not found, return an unauthorized response
        return Response(status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@retry_on_failure(attempts=3, delay=1, exceptions=(Exception,))
def registerUser(request):
    # Check if the username already exists
    if User.objects.filter(userName=request.data.get('userName')).exists():
        return Response({'message': 'User already exists'}, status=status.HTTP_400_BAD_REQUEST)

    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Account Created'}, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@retry_on_failure(attempts=3, delay=1, exceptions=(Exception,))
def allMessages(request):
    try:
        messages = Message.objects.filter(chatroomId = request.data.get('chatroomId')).order_by('date')
        serializer = MessageSerializer(messages, many=True)
        # If the messages are found, return a success response
        return JsonResponse(serializer.data, status=status.HTTP_200_OK, safe=False)
    except User.DoesNotExist:
        # If the messages are not found, return an bad request response
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@retry_on_failure(attempts=3, delay=1, exceptions=(Exception,))
def createMessage(request):
    serializer = MessageSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Message Saved'}, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
