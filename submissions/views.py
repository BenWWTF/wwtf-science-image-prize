from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
import logging

from .forms import PersonForm, ImageForm
from .models import SubmissionImage

logger = logging.getLogger(__name__)


def home(request):
    return render(request, 'submissions/home.html')


def submit(request):
    image_forms = [ImageForm(prefix='img' + str(i)) for i in range(3)]

    if request.method == 'POST':
        person_form = PersonForm(request.POST)
        image_forms = [ImageForm(request.POST, request.FILES, prefix='img' + str(i)) for i in range(3)]

        valid_person = person_form.is_valid()
        valid_images = all(f.is_valid() for f in image_forms)

        if valid_person and valid_images:
            valid_image_data = [f.cleaned_data for f in image_forms if f.cleaned_data.get('file')]
            if not valid_image_data:
                messages.error(request, 'Please upload at least one image.')
            else:
                submission = person_form.save(commit=False)
                submission.ip_address = request.META.get('REMOTE_ADDR')
                submission.save()

                for order, data in enumerate(valid_image_data, start=1):
                    SubmissionImage.objects.create(
                        submission=submission,
                        order=order,
                        file=data['file'],
                        title=data['title'],
                        description=data['description'],
                        method=data['method'],
                        scientific_context=data.get('scientific_context', ''),
                    )

                _send_notification(submission)
                return redirect('success')

    else:
        person_form = PersonForm()

    return render(request, 'submissions/submit.html', {
        'person_form': person_form,
        'image_forms': image_forms,
    })


def success(request):
    return render(request, 'submissions/success.html')


def _send_notification(submission):
    count = submission.images.count()
    plural = 's' if count != 1 else ''
    subject = 'New submission: ' + submission.full_name + ' (' + str(count) + ' image' + plural + ')'
    body = (
        'New submission received\n\n'
        'Name: ' + submission.full_name + '\n'
        'Email: ' + submission.email + '\n'
        'Institution: ' + submission.institution + '\n'
        'Position: ' + submission.get_position_display() + '\n'
        'Research field: ' + submission.research_field + '\n'
        'ORCID: ' + (submission.orcid or '-') + '\n'
        'Images submitted: ' + str(count) + '\n\n'
        'Review in admin: http://100.112.136.40:8082/admin/submissions/submission/' + str(submission.id) + '/change/'
    )
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [settings.ADMIN_EMAIL])
    except Exception as e:
        logger.error('Failed to send notification email: %s', e)
