from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .api.serializers import UserRegistrationSerializer, PatientRegistrationSerializer, DoctorRegistrationSerializer, AppointmentSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .api.serializers import CustomTokenObtainPairSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from rest_framework.filters import SearchFilter
from registration.models import User, Appointment, Notification
from .utils import send_email_and_notification
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode  
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_decode
from django.core.exceptions import ObjectDoesNotExist
import json
from django.conf import settings 
# Create your views here.

class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'User registered successfully!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PatientRegistrationView(APIView):
    def post(self, request):
        serializer = PatientRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Patient registered successfully!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DoctorRegistrationView(APIView):
    def post(self, request):
    # Convert QueryDict to a standard Python dictionary
        data = request.data.dict()  # Converts all key-value pairs to a mutable dictionary

        # Parse the `user` field if it's a JSON string
        if isinstance(data.get('user'), str):
            try:
                userdata = json.loads(data['user'])
                data['user'] = userdata
                print(type(data['user']))
                print(data['user'])
            except json.JSONDecodeError:
                return Response({'error': 'Invalid user data format'}, status=status.HTTP_400_BAD_REQUEST)

        # Debugging logs
        print("Processed Data:", data)

        # Pass processed data to the serializer
        serializer = DoctorRegistrationSerializer(data=data)
        print("Initial Data:", serializer.initial_data)

        if serializer.is_valid():
            serializer.save()
            print(serializer.data)
            return Response({'message': 'Doctor registered successfully!'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "You are authenticated!"})
    
from rest_framework_simplejwt.tokens import RefreshToken

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Successfully logged out."}, status=200)
        except Exception as e:
            return Response({"error": "Invalid token."}, status=400)
        
class UnregisteredUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role not in ['doctor', 'patient']:
            return Response({
                "message": "You need to register as a doctor or patient to access the system.",
                "actions": {
                    "register_as_patient": "/register/patient/",
                    "register_as_doctor": "/register/doctor/",
                    "logout": "/logout/"
                }
            }, status=403)
        return Response({"message": "Welcome to the system!"})
    
class PasswordResetRequestView(APIView):
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email address is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))

            reset_link = f"{settings.BASE_URL}/password-reset/confirm/{uidb64}/{token}/"

            # Send the reset link via email
            send_mail(
                'Password Reset Request',
                f"Click the link below to reset your password:\n\n{reset_link}",
                'your_email@example.com',
                [email],
                fail_silently=False,
            )
            return Response({'message': 'Password reset link sent to your email.'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        
class PasswordResetConfirmView(APIView):
    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
            token_generator = PasswordResetTokenGenerator()

            if not token_generator.check_token(user, token):
                return Response({'error': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)

            # Validate and set the new password
            password = request.data.get('password')
            confirm_password = request.data.get('confirm_password')

            if not password or not confirm_password:
                return Response({'error': 'Password and confirm password are required.'}, status=status.HTTP_400_BAD_REQUEST)

            if password != confirm_password:
                return Response({'error': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(password)
            user.save()

            return Response({'message': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)
        except (ValueError, User.DoesNotExist):
            return Response({'error': 'Invalid token or user.'}, status=status.HTTP_400_BAD_REQUEST)        

class AppointmentBookingView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != 'patient':
            return Response({"error": "Only patients can book appointments."}, status=status.HTTP_403_FORBIDDEN)

        serializer = AppointmentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            appointment=Appointment.objects.get(id=serializer.data.get('id'))
            # print(serializer.data)

            from .utils import send_email_and_notification
            send_email_and_notification(
                recipient=appointment.doctor,
                subject="New Appointment Created",
                message=f"You have a new appointment with {appointment.patient.username} on {appointment.date} at {appointment.time}.",
                event_type="appointment_created"
            )

            return Response(serializer.data , status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class DoctorManageAppointmentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'doctor':
            return Response({"error": "Only doctors can manage appointments."}, status=status.HTTP_403_FORBIDDEN)

        appointments = Appointment.objects.filter(doctor=request.user)
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)

    def patch(self, request, appointment_id):
        if request.user.role != 'doctor':
            return Response({"error": "Only doctors can manage appointments."}, status=status.HTTP_403_FORBIDDEN)

        try:
            appointment = Appointment.objects.get(id=appointment_id, doctor=request.user)
        except Appointment.DoesNotExist:
            return Response({"error": "Appointment not found."}, status=status.HTTP_404_NOT_FOUND)

        # Get the requested status change
        new_status = request.data.get('status')
        allowed_transitions = ['confirmed', 'canceled']  # Allowed status changes for doctors

        # Validate the new status
        if new_status not in allowed_transitions:
            return Response(
                {"error": f"Invalid status. Allowed statuses: {allowed_transitions}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Allow status change only if current status is 'pending'
        if appointment.status != 'pending':
            return Response(
                {"error": "Status can only be changed from 'pending'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update the appointment status
        appointment.status = new_status
        appointment.save()

        # Notify the patient about the status change (optional)
        if new_status == 'confirmed':
            # Logic to send a confirmation email or notification to the patient
            # Notify the patient
            from .utils import send_email_and_notification
            send_email_and_notification(
                recipient=appointment.patient,
                subject="Appointment Confirmed",
                message=f"Your appointment with Dr. {appointment.doctor.username} on {appointment.date} at {appointment.time} has been confirmed.",
                event_type="appointment_confirmed"
            )
            pass
        elif new_status == 'canceled':
            # Logic to send a cancellation email or notification to the patient
             # Notify the patient
            from .utils import send_email_and_notification
            send_email_and_notification(
                recipient=appointment.patient,
                subject="Appointment Canceled",
                message=f"Your appointment with Dr. {appointment.doctor.username} on {appointment.date} at {appointment.time} has been canceled.",
                event_type="appointment_canceled"
            )
            pass

        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PatientCompleteAppointmentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, appointment_id):
        """
        Retrieve appointment details for the patient.
        """
        if request.user.role != 'patient':
            return Response({"error": "Only patients can view appointments."}, status=status.HTTP_403_FORBIDDEN)

        try:
            # Get the appointment details for the logged-in patient
            appointment = Appointment.objects.get(id=appointment_id, patient=request.user)
        except Appointment.DoesNotExist:
            return Response({"error": "Appointment not found."}, status=status.HTTP_404_NOT_FOUND)

        # Serialize and return the appointment data
        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, appointment_id):
        if request.user.role != 'patient':
            return Response({"error": "Only patients can complete appointments."}, status=status.HTTP_403_FORBIDDEN)

        try:
            appointment = Appointment.objects.get(id=appointment_id, patient=request.user, status='confirmed')
        except Appointment.DoesNotExist:
            return Response({"error": "Appointment not found or not confirmed."}, status=status.HTTP_404_NOT_FOUND)

        appointment.status = 'completed'
        appointment.save()

        from .utils import send_email_and_notification
        send_email_and_notification(
            recipient=appointment.doctor,
            event_type="Appointment_completed",
            subject="Appointment Completed",
            message=f"The appointment with {appointment.patient.username} on {appointment.date} at {appointment.time} has been marked as completed."
        )
        
        # create_notification(
        #     recipient=appointment.doctor,
        #     event_type="appointment_completed",
        #     subject="Appointment Completed",
        #     message=f"The appointment with {appointment.patient.username} on {appointment.date} at {appointment.time} has been marked as completed."
        # )


        return Response({"message": "Appointment marked as completed."})

class DoctorUploadPrescriptionView(APIView):
    permission_classes = [IsAuthenticated]
    def patch(self, request, appointment_id):
        """
        Allows a doctor to upload a prescription for a completed appointment.
        """
        if request.user.role != 'doctor':
            return Response({"error": "Only doctors can upload prescriptions."}, status=status.HTTP_403_FORBIDDEN)

        try:
            # Ensure the appointment exists and is marked as 'completed'
            appointment = Appointment.objects.get(id=appointment_id, doctor=request.user, status='completed')
        except Appointment.DoesNotExist:
            return Response(
                {"error": "Appointment not found or not marked as completed."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get the prescription content from the request
        prescription = request.data.get('prescription')
        if not prescription:
            return Response({"error": "Prescription content is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Save the prescription to the appointment
        appointment.prescription = prescription
        appointment.save()

         # Notify the patient
        from .utils import send_email_and_notification
        send_email_and_notification(
            recipient=appointment.patient,
            subject="Prescription Uploaded",
            message=f"Dr. {appointment.doctor.username} has uploaded your prescription for the appointment on {appointment.date}.",
            event_type="prescription_uploaded"
        )

        # Serialize and return the updated appointment data
        serializer = AppointmentSerializer(appointment)
        return Response(
            {"message": "Prescription uploaded successfully.", "appointment": serializer.data},
            status=status.HTTP_200_OK
        )
    

class PatientRescheduleAppointmentView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, appointment_id):
        """
        Allows patients to reschedule an appointment with status pending, confirmed, or canceled.
        """
        if request.user.role != 'patient':
            return Response({"error": "Only patients can reschedule appointments."}, status=status.HTTP_403_FORBIDDEN)

        try:
            # Retrieve the appointment
            appointment = Appointment.objects.get(
                id=appointment_id, 
                patient=request.user, 
                status__in=['pending', 'confirmed', 'canceled']
            )
        except Appointment.DoesNotExist:
            return Response(
                {"error": "Appointment not found or cannot be rescheduled."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Validate the new date and time
        new_date = request.data.get('date')
        new_time = request.data.get('time')

        if not new_date or not new_time:
            return Response(
                {"error": "New date and time are required for rescheduling."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Ensure the new date and time are in the future
        from datetime import datetime
        new_datetime = datetime.strptime(f"{new_date} {new_time}", "%Y-%m-%d %H:%M:%S")
        if new_datetime <= datetime.now():
            return Response(
                {"error": "New date and time must be in the future."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check for conflicts with other appointments for the same doctor
        if Appointment.objects.filter(
            doctor=appointment.doctor, 
            date=new_date, 
            time=new_time
        ).exists():
            return Response(
                {"error": "The selected date and time are already booked with this doctor."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update the appointment with the new date and time
        appointment.date = new_date
        appointment.time = new_time
        appointment.status = 'pending'  # Reset status to pending after rescheduling
        appointment.save()

        from .utils import send_email_and_notification
        send_email_and_notification(
            recipient=appointment.doctor,
            event_type="appointment_rescheduled",
            subject="Appointment Rescheduled",
            message=f"The appointment with {appointment.patient.username} has been rescheduled to {new_date} at {new_time}."
        )

        # Serialize and return the updated appointment
        serializer = AppointmentSerializer(appointment)
        return Response(
            {"message": "Appointment rescheduled successfully.", "appointment": serializer.data},
            status=status.HTTP_200_OK
        )


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
        notification_data = [
            {
                "id": notification.id,
                "event_type": notification.event_type,
                "subject": notification.subject,
                "message": notification.message,
                "is_read": notification.is_read,
                "created_at": notification.created_at
            }
            for notification in notifications
        ]
        return Response(notification_data, status=status.HTTP_200_OK)

class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, notification_id):
        try:
            notification = Notification.objects.get(id=notification_id, recipient=request.user)
            notification.is_read = True
            notification.save()
            return Response({"message": "Notification marked as read."}, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({"error": "Notification not found."}, status=status.HTTP_404_NOT_FOUND)

class PatientAppointmentManagementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieve all appointments for the logged-in patient.
        """
        if request.user.role != 'patient':
            return Response({"error": "Only patients can view their appointments."}, status=status.HTTP_403_FORBIDDEN)

        appointments = Appointment.objects.filter(patient=request.user).order_by('-date', '-time')
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, appointment_id):
        """
        Allows the patient to mark a 'confirmed' appointment as 'completed'.
        """
        if request.user.role != 'patient':
            return Response({"error": "Only patients can manage their appointments."}, status=status.HTTP_403_FORBIDDEN)

        try:
            appointment = Appointment.objects.get(id=appointment_id, patient=request.user, status='confirmed')
        except ObjectDoesNotExist:
            return Response(
                {"error": "Appointment not found or it is not confirmed by doctor."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Change the appointment status to 'completed'
        appointment.status = 'completed'
        appointment.save()

        # Serialize and return the updated appointment
        serializer = AppointmentSerializer(appointment)
        return Response(
            {"message": "Appointment marked as completed.", "appointment": serializer.data},
            status=status.HTTP_200_OK
        )
    
class DoctorAppointmentManagementView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieve all appointments for the logged-in doctor.
        """
        if request.user.role != 'doctor':
            return Response({"error": "Only doctors can view their appointments."}, status=status.HTTP_403_FORBIDDEN)

        appointments = Appointment.objects.filter(doctor=request.user).order_by('-date', '-time')
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)