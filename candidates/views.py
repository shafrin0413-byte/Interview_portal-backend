class ResumeUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        profile = get_or_create_profile(request.user)

        # Get uploaded file
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": "No file provided."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate extension
        ext = os.path.splitext(file.name)[1].lower()
        if ext not in [".pdf", ".docx"]:
            return Response(
                {"error": "Only PDF and DOCX files are allowed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Deactivate previous resumes
        Resume.objects.filter(candidate=profile).update(is_active=False)

        # Save new resume
        resume = Resume.objects.create(
            candidate=profile,
            file=file,
            is_active=True
        )

        # Parse resume and update profile data
        try:
            file_path = os.path.join(settings.MEDIA_ROOT, resume.file.name)
            parsed = parse_resume(file_path)

            Skill.objects.filter(candidate=profile).delete()
            Education.objects.filter(candidate=profile).delete()
            Experience.objects.filter(candidate=profile).delete()
            Certification.objects.filter(candidate=profile).delete()

            Skill.objects.bulk_create([
                Skill(candidate=profile, name=s)
                for s in parsed.get("skills", [])
            ])

            Education.objects.bulk_create([
                Education(candidate=profile, **e)
                for e in parsed.get("education", [])
            ])

            Experience.objects.bulk_create([
                Experience(candidate=profile, **e)
                for e in parsed.get("experience", [])
            ])

            Certification.objects.bulk_create([
                Certification(candidate=profile, **c)
                for c in parsed.get("certifications", [])
            ])

        except Exception as e:
            print("Resume parsing error:", str(e))

        return Response(
            CandidateProfileSerializer(profile).data,
            status=status.HTTP_201_CREATED
        )