from rest_framework import serializers
from ..models import User, DoctorProfile, PatientProfile, Appointment
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, required=True)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password']

    def create(self, validated_data):
        # Hash the password before saving the user
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        # # Create associated profiles for doctors or patients
        # if user.role == 'doctor':
        #     DoctorProfile.objects.create(user=user)
        # elif user.role == 'patient':
        #     PatientProfile.objects.create(user=user)
        user.save()    
        return user

class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role']

class DoctorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorProfile
        fields = ['specialization', 'profile_picture', 'certificate_picture', 'license_number', 'phone']

class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProfile
        fields = ['date_of_birth', 'address', 'phone']

class UserProfileSerializer(serializers.ModelSerializer):
    doctor_profile = DoctorProfileSerializer(read_only=True)
    patient_profile = PatientProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'doctor_profile', 'patient_profile']


class PatientRegistrationSerializer(serializers.ModelSerializer):
    user = UserRegistrationSerializer()

    class Meta:
        model = PatientProfile
        fields = ['user', 'phone']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = 'patient'  # Set role to patient
        user = UserRegistrationSerializer.create(UserRegistrationSerializer(), validated_data=user_data)
        patient = PatientProfile.objects.create(user=user, **validated_data)
        return patient
    
class DoctorRegistrationSerializer(serializers.ModelSerializer):
    user = UserRegistrationSerializer()
    profile_picture = serializers.ImageField(required=True)
    certificate_picture = serializers.ImageField(required=True)

    class Meta:
        model = DoctorProfile
        fields = ['user', 'specialization', 'profile_picture', 'certificate_picture', 'license_number']

    def create(self, validated_data):
        print(validated_data)
        user_data = validated_data.pop('user')
        #print(user_data)
        user_data['role'] = 'doctor'  # Set role to doctor
        user = User.objects.create_user(**user_data)
        doctor = DoctorProfile.objects.create(user=user, **validated_data)
        return doctor



class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        # Add additional user information to the token response
        data.update({
            'user_id': self.user.id,
            'username': self.user.username,
            'role': self.user.role,
        })
        return data

class DoctorSearchSerializer(serializers.ModelSerializer):
    specialization = serializers.CharField(source='doctor_profile.specialization')

    class Meta:
        model = User
        fields = ['username', 'specialization']


class AppointmentSerializer(serializers.ModelSerializer):
    doctor_username = serializers.CharField(write_only=True)  # Accept doctor username instead of ID
    # prescription = serializers.CharField(read_only=True)  # Patients cannot modify this

    class Meta:
        model = Appointment
        fields = ['doctor_username', 'date', 'time', 'status', 'reason', 'token']
        read_only_fields = ['status', 'token', 'prescription']

    def validate(self, data):
        # Validate doctor existence
        try:
            doctor = User.objects.get(username=data['doctor_username'], role='doctor')
            data['doctor'] = doctor
        except User.DoesNotExist:
            raise serializers.ValidationError("Doctor with the given username does not exist.")

        # Ensure no double booking
        if Appointment.objects.filter(
            doctor=data['doctor'],
            date=data['date'],
            time=data['time']
        ).exists():
            raise serializers.ValidationError("This time slot is already booked.")

        return data

    def create(self, validated_data):
        validated_data.pop('doctor_username')  # Remove username after converting to the doctor instance
        validated_data['patient'] = self.context['request'].user  # Set the logged-in user as the patient
        return super().create(validated_data)
