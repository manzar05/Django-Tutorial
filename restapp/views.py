from .models import *
from .serializers import *
from django.http import HttpResponse
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view,permission_classes
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from django.contrib.auth.hashers import make_password
from datetime import datetime,timedelta,timezone
import jwt
from django.core.exceptions import ValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
# Custom Services Import
from django.utils.http import urlsafe_base64_decode
from django.conf import settings
from django.utils.encoding import force_text
from restapp.services.email_service import send_verification_email

DOMAIN_URL='127.0.0.1:8000'
COMPANY='Manzar Organization'


# Override default Class for token generation
class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        serializer=UserSerializerWithToken(self.user).data
        for k,v in serializer.items():
            data[k]=v       
        return data
    

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class=MyTokenObtainPairSerializer

@api_view(['GET'])
def home(request):
    data = {
        "message":"Successs"
    }
    return Response(data,status=status.HTTP_200_OK)


@api_view(['POST'])
def registerUser(request):
    data = request.data
    try:
        # Retrieve fields individually with default values or raise specific exceptions
        first_name = data.get('fname')
        if not first_name:
            raise DRFValidationError({'fname': 'First name is required.'})
        
        last_name = data.get('lname')
        if not last_name:
            raise DRFValidationError({'lname': 'Last name is required.'})
        
        username = data.get('email')
        if not username:
            raise DRFValidationError({'username': 'Username (email) is required.'})
        
        email = data.get('email')
        if not email:
            raise DRFValidationError({'email': 'Email is required.'})
        
        password = data.get('password')
        if not password:
            raise DRFValidationError({'password': 'Password is required.'})

        # Create user with validated fields
        user = MyUserTable.objects.create(
            first_name=first_name,
            last_name=last_name,
            username=username,
            email=email,
            password=make_password(password),
            is_active=False
        )
        email = send_verification_email(user)
        email.content_subtype = "html"  # Set content type to HTML
        email.send()
        print("Activation email sent to:", user)
        
        # Serialize user data
        serialize = UserSerializerWithToken(user, many=False).data
        return Response(serialize, status=status.HTTP_200_OK)
    
    except KeyError as e:
        message = {'details': f"Missing field: {str(e)}"}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)
    
    except DRFValidationError as e:
        # Handle field-specific validation errors
        return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
    
    except ValidationError as e:
        # Handle Django model validation errors
        message = {'details': str(e)}
        return Response(message, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        # Catch-all for any other exceptions
        message = {'details': f"User Already exist with this Email ID:{email}"}
        print(e)
        return Response(message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
@api_view(["GET"])
def activateAccount(request, uidb64, token):
    """
    Activates a user's account upon verifying a token from an email link.
    Parameters:
    - request: The HTTP GET request object.
    - uidb64 (str): Base64 encoded user ID to identify the user in the database.
    - token (str): JWT token that contains user-specific data for verification, including an expiration timestamp.

    Returns:
    - JSON response with details of the outcome:
      - "Account activated successfully!" if token is valid and account is activated.
      - "Verification link has expired. New verification link sent." if the token is expired.
      - "Invalid token!" if the token is invalid or doesn't match the user.

    Usage:
    - Include this function as a URL endpoint in your Django application.
    - Users receive a verification email containing a link with `uidb64` and `token` as parameters.
    - On clicking the link, they are redirected to this endpoint for account verification.

    Raises:
    - jwt.ExpiredSignatureError: If the token has expired.
    - jwt.InvalidTokenError: If the token is invalid.
    - Exception: Any other unexpected errors.
    """
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = MyUserTable.objects.get(id=uid)  # Adjust this line based on your model
        
        # Decode the token to get user ID and expiration time
        decoded_payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        
        if decoded_payload['user_id'] != user.id:
            return Response({'details': 'Invalid token!'}, status=status.HTTP_400_BAD_REQUEST)
        
        current_time = datetime.now(timezone.utc)
        expiration_time = datetime.fromtimestamp(decoded_payload['exp'], tz=timezone.utc)

        # Check if the token has expired
        if current_time > expiration_time:
            email = send_verification_email(user)
            email.content_subtype = "html"  # Set content type to HTML
            email.send()
            return Response({'details': 'Verification link has expired. New Verification Link send'}, status=status.HTTP_400_BAD_REQUEST)

        # Activate the user account
        user.is_active = True
        user.save()
        return Response({'details': 'Account activated successfully!'}, status=status.HTTP_200_OK)

    except jwt.ExpiredSignatureError:
        email = send_verification_email(user)
        email.content_subtype = "html"
        email.send()
        return Response({'details': 'Verification link has expired. New Verification Link send'}, status=status.HTTP_400_BAD_REQUEST)
    except jwt.InvalidTokenError:
        return Response({'details': 'Invalid token!'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'details': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        
