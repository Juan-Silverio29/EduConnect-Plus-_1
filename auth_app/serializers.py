# auth_app/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import PerfilUsuario

class RegisterSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    rol = serializers.CharField(write_only=True, required=False)
    institucion = serializers.CharField(write_only=True, required=False)
    alias = serializers.CharField(write_only=True, required=False, allow_blank=True, allow_null=True)
    semestre = serializers.CharField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name',
                  'password1', 'password2', 'rol', 'institucion', 'alias', 'semestre']

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return data

    def create(self, validated_data):
        rol = validated_data.pop('rol', 'estudiante')
        institucion = validated_data.pop('institucion', None)
        alias = validated_data.pop('alias', None)
        semestre = validated_data.pop('semestre', None)
        password = validated_data.pop('password1')
        validated_data.pop('password2', None)

        user = User(**validated_data)
        user.set_password(password)
        user.is_staff = rol == "profesor"
        user.save()

        PerfilUsuario.objects.create(
            user=user,
            institucion=institucion,
            alias=alias,
            semestre=semestre,
            foto_perfil="img/default_user.png"
        )

        return user
