from rest_framework import serializers
from .models import CandidateProfile, Resume, Skill, Education, Experience, Certification


class CertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Certification
        fields = ('id', 'name', 'issuer', 'year')


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ('id', 'name')


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = ('id', 'degree', 'institution', 'year')


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = ('id', 'title', 'company', 'duration', 'description')


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ('id', 'file', 'uploaded_at', 'is_active')


class CandidateProfileSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)
    education = EducationSerializer(many=True, read_only=True)
    experience = ExperienceSerializer(many=True, read_only=True)
    resumes = ResumeSerializer(many=True, read_only=True)
    certifications = CertificationSerializer(many=True, read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = CandidateProfile
        fields = ('id', 'username', 'email', 'headline', 'bio', 'location', 'linkedin', 'github', 'avatar', 'skills', 'education', 'experience', 'certifications', 'resumes', 'updated_at')


class CandidateProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateProfile
        fields = ('headline', 'bio', 'location', 'linkedin', 'github', 'avatar')
