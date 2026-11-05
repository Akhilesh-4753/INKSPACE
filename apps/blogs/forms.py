import re
import bleach
from django import forms
from django.core.exceptions import ValidationError
from .models import Blog, CategoryChoices, BlogStatus

# Whitelist of safe HTML tags and attributes for the Rich Text Editor
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'b', 'em', 'i', 'u',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'blockquote', 'a', 'code', 'pre',
    'span', 'hr'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'code': ['class'],
    'pre': ['class'],
    'span': ['class'],
}

ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']

class BlogForm(forms.ModelForm):
    """
    ModelForm for creating and editing blog posts.
    Maps directly to the Blog model and attaches Bootstrap 5 CSS classes.
    """
    class Meta:
        model = Blog
        fields = ['title', 'description', 'category', 'content', 'cover_image', 'status']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control form-control-lg font-serif',
                'placeholder': 'Enter a catchy title for your blog',
                'id': 'id_title',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Write a short summary (max 200 characters)',
                'id': 'id_description',
                'maxlength': '250',
            }),
            'category': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_category',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control font-sans',
                'rows': 14,
                'placeholder': 'Start writing your blog here...',
                'id': 'id_content',
            }),
            'cover_image': forms.FileInput(attrs={
                'class': 'form-control',
                'id': 'id_cover_image',
                'accept': 'image/*',
            }),
            'status': forms.RadioSelect(attrs={
                'class': 'form-check-input',
                'id': 'id_status',
            }),
        }

    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if len(title) < 5:
            raise ValidationError("Blog title must be at least 5 characters long.")
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        if len(description) < 15:
            raise ValidationError("Please provide a meaningful description of at least 15 characters.")
        if len(description) > 250:
            raise ValidationError("Description cannot exceed 250 characters.")
        return description

    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        if not content:
            raise ValidationError("Blog content is required.")

        # Sanitize HTML to prevent XSS attacks while preserving formatting
        cleaned_html = bleach.clean(
            content,
            tags=ALLOWED_TAGS,
            attributes=ALLOWED_ATTRIBUTES,
            protocols=ALLOWED_PROTOCOLS,
            strip=True
        )

        # Check visible text length (ignoring HTML tags)
        plain_text = re.sub(r'<[^>]*>', '', cleaned_html).strip()
        if len(plain_text) < 30:
            raise ValidationError("Blog content is too short. Please write at least 30 characters.")

        return cleaned_html

class ContactForm(forms.Form):
    """
    Contact form for INKSPACE platform inquiries and feedback.
    """
    name = forms.CharField(
        max_length=120,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your full name',
            'id': 'contact_name',
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'name@example.com',
            'id': 'contact_email',
        })
    )
    subject = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subject of your message',
            'id': 'contact_subject',
        })
    )
    message = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'form-control font-sans',
            'rows': 5,
            'placeholder': 'How can we help you?',
            'id': 'contact_message',
        })
    )

    def clean_message(self):
        msg = self.cleaned_data.get('message', '').strip()
        if len(msg) < 10:
            raise ValidationError("Message is too short. Please provide at least 10 characters.")
        return msg

