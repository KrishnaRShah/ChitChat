from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['firstName', 'lastName', 'userName', 'password']

    def create(self, validated_data):
        #Since we're not using Django's create_user method
        user = User.objects.create(**validated_data)
        user.set_password(validated_data['password'])  # This is important for password hashing
        user.save()
        return user
