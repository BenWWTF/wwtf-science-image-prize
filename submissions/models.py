import uuid
from django.db import models


class Submission(models.Model):
    POSITION_CHOICES = [
        ('master', "Master's Student"),
        ('phd', 'PhD Student'),
        ('postdoc', 'Postdoc / Research Fellow'),
        ('assistant_prof', 'Assistant Professor'),
        ('associate_prof', 'Associate Professor'),
        ('full_prof', 'Full Professor'),
        ('researcher', 'Senior / Principal Researcher'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    institution = models.CharField(max_length=300)
    position = models.CharField(max_length=20, choices=POSITION_CHOICES)
    research_field = models.CharField(max_length=200, help_text='e.g. Molecular Biology, Urban Planning, History of Art')
    orcid = models.CharField(max_length=30, blank=True)

    copyright_confirmed = models.BooleanField(default=False)
    usage_rights_granted = models.BooleanField(default=False)
    terms_accepted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.first_name} {self.last_name} ({self.email})'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'


def image_upload_path(instance, filename):
    return f'submissions/{instance.submission.id}/{filename}'


class SubmissionImage(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='images')
    order = models.PositiveSmallIntegerField()
    file = models.ImageField(upload_to=image_upload_path)
    title = models.CharField(max_length=200)
    description = models.TextField(help_text='What does this image show?')
    method = models.CharField(max_length=300, help_text='How was this image created? (microscopy, illustration, photography, etc.)')
    scientific_context = models.TextField(blank=True, help_text='Additional scientific background (optional)')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'Image {self.order}: {self.title}'
