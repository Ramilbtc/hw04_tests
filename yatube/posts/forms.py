from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from .models import Post


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = {'text', 'group'}
        labels = {
            'text': _('Введите текст)))))'),
        }
        help_texts = {
            'text': _('Текст нового поста'),
            'group': _('Группа, к которой будет относиться пост'),
        }
