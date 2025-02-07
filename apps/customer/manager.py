from django.contrib.auth.models import BaseUserManager


# 🔹 Criando um gerenciador de usuários personalizado
class CustomerManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """Cria e retorna um usuário normal com email e senha."""
        if not email:
            raise ValueError("O email deve ser fornecido")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Cria e retorna um superusuário com permissões administrativas."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superusuário precisa ter is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superusuário precisa ter is_superuser=True")

        return self.create_user(email, password, **extra_fields)