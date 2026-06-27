from django import forms
from PIL import Image
from .models import Submission, SubmissionImage

ALLOWED_FORMATS = {'JPEG', 'PNG', 'TIFF', 'WEBP'}
MAX_SIZE_MB = 50
MAX_PIXELS = 60_000_000  # 60 MP; blocks decompression bombs while allowing large scientific images


class PersonForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = [
            'first_name', 'last_name', 'email', 'institution',
            'position', 'research_field', 'orcid',
            'copyright_confirmed', 'usage_rights_granted', 'terms_accepted',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'placeholder': 'First name', 'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last name', 'autocomplete': 'family-name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'your@email.ac.at', 'autocomplete': 'email'}),
            'institution': forms.TextInput(attrs={'placeholder': 'University / Research Institute'}),
            'research_field': forms.TextInput(attrs={'placeholder': 'e.g. Molecular Biology, Urban Planning'}),
            'orcid': forms.TextInput(attrs={'placeholder': '0000-0000-0000-0000 (optional)'}),
        }
        labels = {
            'copyright_confirmed': 'I confirm I am the sole copyright holder of all submitted images.',
            'usage_rights_granted': 'I grant WWTF the right to use these images for science communication, press, and publications (non-commercial, with attribution).',
            'terms_accepted': 'I accept the competition terms and conditions.',
        }

    def clean_email(self):
        email = self.cleaned_data['email'].lower().strip()
        if Submission.objects.filter(email=email).exists():
            raise forms.ValidationError('A submission with this email address already exists.')
        return email

    def clean_copyright_confirmed(self):
        if not self.cleaned_data.get('copyright_confirmed'):
            raise forms.ValidationError('You must confirm copyright ownership.')
        return True

    def clean_usage_rights_granted(self):
        if not self.cleaned_data.get('usage_rights_granted'):
            raise forms.ValidationError('You must grant usage rights to proceed.')
        return True

    def clean_terms_accepted(self):
        if not self.cleaned_data.get('terms_accepted'):
            raise forms.ValidationError('You must accept the terms and conditions.')
        return True


class ImageForm(forms.Form):
    file = forms.ImageField(required=False, widget=forms.FileInput(attrs={'accept': 'image/jpeg,image/png,image/tiff,image/webp'}))
    title = forms.CharField(max_length=200, required=False, widget=forms.TextInput(attrs={'placeholder': 'Image title'}))
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'What does this image show?'}),
    )
    method = forms.CharField(
        max_length=300, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g. Confocal microscopy, oil painting, aerial photography'}),
    )
    scientific_context = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Additional scientific background (optional)'}),
    )

    def clean(self):
        data = super().clean()
        has_file = bool(data.get('file'))
        has_title = bool(data.get('title', '').strip())
        # If any field filled in, require all required fields
        any_filled = has_file or has_title or data.get('description') or data.get('method')
        if any_filled:
            if not has_file:
                self.add_error('file', 'Please upload an image file.')
            if not has_title:
                self.add_error('title', 'Please provide a title for this image.')
            if not data.get('description', '').strip():
                self.add_error('description', 'Please describe what the image shows.')
            if not data.get('method', '').strip():
                self.add_error('method', 'Please describe how this image was created.')
        return data

    def clean_file(self):
        f = self.cleaned_data.get('file')
        if not f:
            return f

        if f.size > MAX_SIZE_MB * 1024 * 1024:
            raise forms.ValidationError(f'File too large. Maximum size is {MAX_SIZE_MB} MB.')

        # Do NOT trust f.content_type (client-supplied). Verify via Pillow.
        try:
            f.seek(0)
            img = Image.open(f)
            fmt = (img.format or '').upper()
            width, height = img.size
            img.verify()  # detects corrupt/truncated files; read attrs first as verify() invalidates the object
        except Exception:
            raise forms.ValidationError('Unsupported or corrupt image file. Use JPEG, PNG, TIFF, or WebP.')
        finally:
            f.seek(0)  # reset so Django can save the file

        if fmt not in ALLOWED_FORMATS:
            raise forms.ValidationError('Unsupported format. Use JPEG, PNG, TIFF, or WebP.')
        if width * height > MAX_PIXELS:
            raise forms.ValidationError('Image resolution too large (max 60 megapixels).')
        return f
