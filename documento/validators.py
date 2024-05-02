# validators.py no seu aplicativo Django
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _

class CustomPasswordValidator:
    def validate(self, password, user=None):
        if not any(char.isdigit() for char in password):
            raise ValidationError(_('A senha deve conter pelo menos um número.'), code='password_no_number')
        if not any(char.isupper() for char in password):
            raise ValidationError(_('A senha deve conter pelo menos uma letra maiúscula.'), code='password_no_upper')
        if not any(char in '!@#$%^&*()_+=' for char in password):
            raise ValidationError(_('A senha deve conter pelo menos um caractere especial.'), code='password_no_special')

    def get_help_text(self):
        return _(
            "Sua senha deve conter pelo menos um número, uma letra maiúscula e um caractere especial."
        )
