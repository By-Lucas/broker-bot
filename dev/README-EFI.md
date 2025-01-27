## Solução para Problemas com OpenSSL e Certificados `.p12`

### Problema

Ao tentar converter um arquivo `.p12` para `.pem` usando o OpenSSL, pode ocorrer um erro devido a espaços ou caracteres especiais no nome do arquivo. Além disso, o uso incorreto do parâmetro `-password` pode causar problemas.

### Soluções

#### 1. **Renomear o Arquivo**

- Renomeie o arquivo para remover espaços e caracteres especiais, facilitando o uso no terminal.

```bash
mv "homologacao-379507-TK Nexus 2.p12" homologacao-379507-TK_Nexus_2.p12
```

- Em seguida, execute o comando:

```bash
openssl pkcs12 -in homologacao-379507-TK_Nexus_2.p12 -out certificado.pem -nodes
```

#### 2. Usar Aspas Corretas para o Nome do Arquivo
- Se você quiser manter o nome original do arquivo, envolva-o em aspas duplas para que o terminal interprete corretamente os espaços:

```bash
openssl pkcs12 -in "homologacao-379507-TK Nexus 2.p12" -out certificado.pem -nodes
```

- Se o arquivo .p12 tiver uma senha, use o seguinte formato:

```bash
openssl pkcs12 -in "homologacao-379507-TK Nexus 2.p12" -out certificado.pem -nodes -password pass:"SENHA_AQUI"
```

#### 3. Verificar o Parâmetro -password
- O parâmetro -password deve ser passado corretamente se o arquivo .p12 exigir uma senha. A sintaxe é:

```bash
-password pass:your_password_here
```

- Se a senha for em branco, você pode omitir o parâmetro -password ou deixar apenas pass::

```bash
openssl pkcs12 -in "homologacao-379507-TK Nexus 2.p12" -out certificado.pem -nodes -pas
```

### Conclusão

**Seguindo essas etapas, você deve ser capaz de converter o arquivo .p12 para .pem sem problemas, mesmo que o nome do arquivo contenha espaços ou caracteres especiais.**

*Este conteúdo explica como resolver o problema de forma clara e organizada, e pode ser facilmente adicionado ao seu documento `.md`.*
