from rest_framework import serializers
from .models import Ad, ExchangeProposal
from django.contrib.auth.models import User


class AdSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Ad
        fields = ['ad_id', 'user', 'title', 'description', 'image_url', 'category', 'condition', 'created_at']
        read_only_fields = ['ad_id', 'user', 'created_at']
        

class ExchangeProposalSerializer(serializers.ModelSerializer):
    ad_sender = AdSerializer(read_only=True)
    ad_receiver = AdSerializer(read_only=True)
    ad_sender_id = serializers.PrimaryKeyRelatedField(queryset=Ad.objects.all(), source='ad_sender', write_only=True)
    ad_receiver_id = serializers.PrimaryKeyRelatedField(queryset=Ad.objects.all(), source='ad_receiver', write_only=True)

    def validate(self, data):
        ad_sender = data.get('ad_sender')
        ad_receiver = data.get('ad_receiver')
        
        if ad_sender and ad_receiver:
            if ad_sender == ad_receiver:
                raise serializers.ValidationError("Нельзя обмениваться с самим собой!")
            request = self.context.get('request')
            if request and ad_sender.user != request.user:
                raise serializers.ValidationError("Вы можете предлагать только свои объявления!")
        
        return data

    class Meta:
        model = ExchangeProposal
        fields = ['exchange_id', 'ad_sender', 'ad_receiver', 'ad_sender_id', 'ad_receiver_id', 'comment', 'status', 'created_at']
        read_only_fields = ['exchange_id', 'created_at', 'ad_sender', 'ad_receiver']
        

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True}
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user
        