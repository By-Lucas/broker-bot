### copiar pasta do APIBUilderKit para fazer deploy

- EXECUTAR NO TERMINAL | CMD
```
cp -r /home/lucas/Área\ de\ trabalho/TK\ Global\ Technology/APIBuilderKit/* ./APIBuilderKit --exclude=.git

```

- OU | EXECUTAR NO TERMINAL | CMD

```
rsync -av --exclude='.git' /home/lucas/Área\ de\ trabalho/TK\ Global\ Technology/APIBuilderKit/ ./APIBuilderKit/
```


### Gerar um SSH-RSA E ADICIOANAN NO AMBIENTE DE PRODUÃO
```
ssh-keygen -m PEM -t rsa -b 4096 -C "email@gmail.com"
```

- Exiba a chave pública para copiá-la e adicioná-la ao seu servidor ou repositório de código:
```
cat ~/.ssh/id_rsa.pub
```
```
cat ~/.ssh/id_rsa
```

- Inicie o ssh-agent
```
eval "$(ssh-agent -s)"
```

- Adicione sua chave SSH ao agente:
```
ssh-add ~/.ssh/id_rsa
```
