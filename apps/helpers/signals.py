from django.core.cache import cache
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save, pre_delete, post_delete

from accounts.models import User



#@receiver(post_save, sender=News)
def post_save_news(sender, instance, created, **kwargs):
    # Esta função será chamada após salvar uma notícia.
    # Se uma notícia é criada ou atualizada, você pode atualizar o cache.

    # Verifique se o objeto News tem uma empresa associada
    if instance.company:
        # Use o ID da empresa como parte da chave de cache para empresas específicas
        cache_key = f'all_news_{instance.company.id}'
        # Exemplo:
        print(f'CACHE ATUALIZADO PARA EMPRESA {instance.company}')
        cache.set(cache_key, News.objects.filter(company=instance.company), 7200)


#@receiver(post_delete, sender=News)
def post_delete_news(sender, instance, **kwargs):
    # Esta função será chamada após excluir uma notícia.
    # Você pode atualizar o cache, se necessário.

    # Verifique se o objeto News tem uma empresa associada
    if instance.company:
        # Use o ID da empresa como parte da chave de cache para empresas específicas
        cache_key = f'all_news_{instance.company.id}'
        # Exemplo:
        print(f'CACHE ATUALIZADO APÓS REMOÇÃO DA NOTÍCIA PARA EMPRESA {instance.company}')
        cache.set(cache_key, News.objects.filter(company=instance.company), 7200)


#@receiver(post_save, sender=User)
def post_save_create_collaborator_receiver(sender, instance, created, **kwargs):
    if created:
        print('Signal: Creating collaborator')
        collaborator = Collaborator.objects.create(user=instance)
        print('Collaborator created:', collaborator)
    else:
        print('Signal: Updating collaborator')
        try:
            collaborator = Collaborator.objects.get(user=instance)
            # Realize as atualizações necessárias no objeto colaborador
            collaborator.save()
        except Collaborator.DoesNotExist:
            print('Collaborator does not exist. Creating...')
            collaborator = Collaborator.objects.create(user=instance)
            print('Collaborator created:', collaborator)
