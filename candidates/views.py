from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.conf import settings
import os

from .models import CandidateProfile, Resume, Skill, Education, Experience, Certification
from .serializers import CandidateProfileSerializer, CandidateProfileUpdateSerializer, ResumeSerializer
from .utils import parse_resume
from ai_features.models import ResumeAnalysis


def get_or_create_profile(user):
    profile, _ = CandidateProfile.objects.get_or_create(user=user)
    return profile


class CandidateProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        profile = get_or_create_profile(request.user)
        return Response(CandidateProfileSerializer(profile).data)

    def patch(self, request):
        profile = get_or_create_profile(request.user)
        serializer = CandidateProfileUpdateSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(CandidateProfileSerializer(profile).data)


class ResumeUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        profile = get_or_create_profile(request.user)
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ['.pdf', '.docx']:
            return Response({'error': 'Only PDF and DOCX files are allowed.'}, status=status.HTTP_400_BAD_REQUEST)

        # Deactivate previous resumes
        class ResumeUploadView(APIView):
    def post(self, request):

        try:
            file = request.FILES['resume']
            ...
        except Exception as e:
            return Response({"error": str(e)})

        resume = Resume.objects.create(candidate=profile, file=file)

        # Parse and save extracted data
        file_path = os.path.join(settings.MEDIA_ROOT, resume.file.name)
        try:
            parsed = parse_resume(file_path)

            Skill.objects.filter(candidate=profile).delete()
            Education.objects.filter(candidate=profile).delete()
            Experience.objects.filter(candidate=profile).delete()
            Certification.objects.filter(candidate=profile).delete()

            Skill.objects.bulk_create([Skill(candidate=profile, name=s) for s in parsed['skills']])
            Education.objects.bulk_create([Education(candidate=profile, **e) for e in parsed['education']])
            Experience.objects.bulk_create([Experience(candidate=profile, **e) for e in parsed['experience']])
            Certification.objects.bulk_create([Certification(candidate=profile, **c) for c in parsed['certifications']])
        except Exception:
            pass  # Parsing failed but resume is saved

        return Response(CandidateProfileSerializer(profile).data, status=status.HTTP_201_CREATED)


class ResumeDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        profile = get_or_create_profile(request.user)
        resume = profile.resumes.filter(pk=pk).first()
        if not resume:
            return Response(status=status.HTTP_404_NOT_FOUND)
        resume.file.delete(save=False)
        resume.delete()
        Skill.objects.filter(candidate=profile).delete()
        Education.objects.filter(candidate=profile).delete()
        Experience.objects.filter(candidate=profile).delete()
        Certification.objects.filter(candidate=profile).delete()
        ResumeAnalysis.objects.filter(candidate=profile).delete()
        return Response(CandidateProfileSerializer(profile).data)


class DeleteCandidateAvatarView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        profile = get_or_create_profile(request.user)
        if profile.avatar:
            profile.avatar.delete(save=True)
        return Response(CandidateProfileSerializer(profile).data)


class SkillsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        profile = get_or_create_profile(request.user)
        name = request.data.get('name', '').strip()
        if not name:
            return Response({'error': 'Skill name required.'}, status=status.HTTP_400_BAD_REQUEST)
        skill, created = profile.skills.get_or_create(name=name)
        return Response({'id': skill.id, 'name': skill.name}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    def delete(self, request, pk):
        profile = get_or_create_profile(request.user)
        profile.skills.filter(pk=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
