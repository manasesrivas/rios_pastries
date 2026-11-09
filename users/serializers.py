from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Ejecuta la validación por defecto para generar el access y refresh
        data = super().validate(attrs)

        first_group = self.user.groups.first()

        # Agrega los datos del usuario a la respuesta JSON
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'nombres': getattr(self.user, 'nombres', ''),
            'apellidos': getattr(self.user, 'apellidos', ''),
            'grupo': first_group.name if first_group else ''
            # Agrega cualquier otro campo que necesites de tu modelo User
        }

        return data