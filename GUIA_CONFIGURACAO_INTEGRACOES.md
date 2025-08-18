# 🔧 Guia de Configuração - Integrações Google Drive e WhatsApp Business

## 📋 Índice
- [1. Configuração Google Drive](#1-configuração-google-drive)
- [2. Configuração WhatsApp Business](#2-configuração-whatsapp-business)
- [3. Verificação das Configurações](#3-verificação-das-configurações)
- [4. Solução de Problemas](#4-solução-de-problemas)

---

## 1. 📂 Configuração Google Drive

### 1.1 Criar Projeto no Google Cloud Console

1. **Acesse o Google Cloud Console:**
   - Vá para: https://console.cloud.google.com/
   - Faça login com sua conta Google

2. **Criar um novo projeto:**
   ```
   ➤ Clique em "Select a project" (canto superior esquerdo)
   ➤ Clique em "NEW PROJECT"
   ➤ Nome do projeto: "GB-Advocacia-Sistema"
   ➤ Clique em "CREATE"
   ```

### 1.2 Habilitar APIs Necessárias

1. **Habilitar Google Drive API:**
   ```
   ➤ No menu lateral: APIs & Services > Library
   ➤ Pesquise por "Google Drive API"
   ➤ Clique em "Google Drive API"
   ➤ Clique em "ENABLE"
   ```

2. **Habilitar Google Docs API:**
   ```
   ➤ Pesquise por "Google Docs API"
   ➤ Clique em "Google Docs API" 
   ➤ Clique em "ENABLE"
   ```

### 1.3 Criar Credenciais OAuth 2.0

1. **Configurar tela de consentimento OAuth:**
   ```
   ➤ APIs & Services > OAuth consent screen
   ➤ Escolha "External" 
   ➤ Clique "CREATE"
   
   Preencha os campos obrigatórios:
   ➤ App name: "Sistema GB Advocacia"
   ➤ User support email: seu-email@gbadvocacia.com
   ➤ Developer contact: seu-email@gbadvocacia.com
   ➤ Clique "SAVE AND CONTINUE"
   
   Em Scopes:
   ➤ Clique "ADD OR REMOVE SCOPES"
   ➤ Adicione os escopos:
     - https://www.googleapis.com/auth/drive
     - https://www.googleapis.com/auth/documents
   ➤ Clique "UPDATE" e depois "SAVE AND CONTINUE"
   ```

2. **Criar credenciais OAuth:**
   ```
   ➤ APIs & Services > Credentials
   ➤ Clique "+ CREATE CREDENTIALS"
   ➤ Escolha "OAuth client ID"
   ➤ Application type: "Web application"
   ➤ Name: "GB Advocacia Web Client"
   
   Authorized redirect URIs:
   ➤ Clique "ADD URI"
   ➤ Adicione: http://localhost:8080/callback
   ➤ Clique "CREATE"
   ```

3. **Baixar arquivo de credenciais:**
   ```
   ➤ Clique no botão de download (JSON) ao lado das credenciais criadas
   ➤ Salve o arquivo como "google_credentials.json"
   ➤ Copie este arquivo para: /app/backend/google_credentials.json
   ```

### 1.4 Autorizar a Aplicação

1. **No sistema, faça login como administrador:**
   - Usuário: `admin`
   - Senha: `admin123`

2. **Acesse a configuração do Google Drive:**
   ```
   ➤ No sistema, vá para aba "Documentos" (se disponível para admin)
   ➤ Ou acesse diretamente: GET /api/google-drive/auth-url
   ➤ O sistema retornará uma URL de autorização
   ```

3. **Autorizar no Google:**
   ```
   ➤ Abra a URL fornecida pelo sistema
   ➤ Faça login na conta Google do escritório
   ➤ Aceite as permissões solicitadas
   ➤ Copie o código de autorização retornado
   ➤ Use o código no endpoint: POST /api/google-drive/authorize
   ```

### 1.5 Estrutura de Pastas no Google Drive

Crie a seguinte estrutura no seu Google Drive:

```
📁 GB Advocacia - Documentos/
├── 📁 Templates/
│   └── 📄 Template Procuração (documento base para procurações)
├── 📁 Cliente - [Nome do Cliente 1]/
├── 📁 Cliente - [Nome do Cliente 2]/
└── ...
```

---

## 2. 📱 Configuração WhatsApp Business

### 2.1 Obter Acesso à WhatsApp Business API

**OPÇÃO A - WhatsApp Business API Oficial (Recomendado):**

1. **Criar conta Meta for Developers:**
   - Acesse: https://developers.facebook.com/
   - Crie uma conta ou faça login

2. **Criar aplicativo WhatsApp:**
   ```
   ➤ Clique "Create App"
   ➤ Escolha "Business"
   ➤ Nome do app: "GB Advocacia System"
   ➤ Email de contato: seu-email@gbadvocacia.com
   ➤ Clique "Create App"
   ```

3. **Configurar WhatsApp Business:**
   ```
   ➤ No painel do app, adicione produto "WhatsApp"
   ➤ Clique "Set up" no WhatsApp Business API
   ➤ Siga o processo de verificação do número
   ➤ Anote o Phone Number ID e Access Token
   ```

**OPÇÃO B - Provedor Terceirizado (Mais Simples):**

Use serviços como:
- **Twilio WhatsApp API** (https://www.twilio.com/whatsapp)
- **360Dialog** (https://www.360dialog.com/)
- **Maytapi** (https://maytapi.com/)

### 2.2 Configurar Variáveis de Ambiente

Edite o arquivo `/app/backend/.env`:

```env
# WhatsApp Business Configuration
WHATSAPP_ENABLED=true
WHATSAPP_API_URL=https://graph.facebook.com/v17.0
WHATSAPP_TOKEN=SEU_ACCESS_TOKEN_AQUI
WHATSAPP_PHONE_ID=SEU_PHONE_NUMBER_ID_AQUI
WHATSAPP_VERIFY_TOKEN=SEU_VERIFY_TOKEN_AQUI

# Configuração do webhook (se necessário)
WHATSAPP_WEBHOOK_URL=https://seu-dominio.com/api/whatsapp/webhook
```

### 2.3 Configurar Webhook (Opcional)

Se quiser receber notificações de entrega/leitura:

1. **No Meta for Developers:**
   ```
   ➤ WhatsApp > Configuration
   ➤ Webhook URL: https://seu-dominio.com/api/whatsapp/webhook
   ➤ Verify Token: o mesmo configurado no .env
   ➤ Subscribe to: messages, message_deliveries, message_reads
   ```

### 2.4 Testar Configuração

1. **Reinicie o backend:**
   ```bash
   sudo supervisorctl restart backend
   ```

2. **Teste via API:**
   ```bash
   # Verificar status
   curl -X GET "https://seu-dominio.com/api/whatsapp/status" \
        -H "Authorization: Bearer SEU_TOKEN"

   # Enviar mensagem de teste
   curl -X POST "https://seu-dominio.com/api/whatsapp/send-message" \
        -H "Authorization: Bearer SEU_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
          "phone_number": "+5554999999999",
          "message": "Teste do sistema GB Advocacia"
        }'
   ```

---

## 3. ✅ Verificação das Configurações

### 3.1 Verificar Google Drive

1. **Via Interface do Sistema:**
   ```
   ➤ Login como admin (admin/admin123)
   ➤ Acesse aba "Documentos" 
   ➤ Verifique status: "Google Drive integration is ready"
   ```

2. **Testar Geração de Procuração:**
   ```
   ➤ Vá para um cliente
   ➤ Clique "Gerar Procuração"
   ➤ Verifique se o documento é criado no Google Drive
   ```

### 3.2 Verificar WhatsApp

1. **Via Interface do Sistema:**
   ```
   ➤ Login como admin
   ➤ Acesse aba "WhatsApp"
   ➤ Verifique status: "running" e mode: "production"
   ```

2. **Testar Envio de Mensagem:**
   ```
   ➤ Na aba WhatsApp, envie uma mensagem de teste
   ➤ Verifique se recebe no celular
   ```

3. **Testar Lembrete de Pagamento:**
   ```
   ➤ Na aba "Financeiro"
   ➤ Clique no botão WhatsApp ao lado de uma transação pendente
   ➤ Verifique se o cliente recebe a mensagem
   ```

---

## 4. 🔧 Solução de Problemas

### 4.1 Problemas com Google Drive

**❌ Erro: "Google credentials file not found"**
- **Solução:** Certifique-se que o arquivo `google_credentials.json` está em `/app/backend/`

**❌ Erro: "Failed to generate authorization URL"**
- **Solução:** 
  1. Verifique se as APIs estão habilitadas no Google Cloud Console
  2. Confirme se os redirect URIs estão corretos
  3. Verifique se o arquivo de credenciais não está corrompido

**❌ Erro: "Access denied to Google Drive"**
- **Solução:**
  1. Refaça o processo de autorização OAuth
  2. Verifique se a conta Google tem permissões adequadas
  3. Confirme se os escopos estão corretos

### 4.2 Problemas com WhatsApp

**❌ Mensagens não são enviadas (mode: simulation)**
- **Solução:** Altere `WHATSAPP_ENABLED=true` no arquivo `.env`

**❌ Erro de autenticação WhatsApp**
- **Solução:**
  1. Verifique se o `WHATSAPP_TOKEN` está correto
  2. Confirme se o `WHATSAPP_PHONE_ID` está correto
  3. Teste o token diretamente na API do WhatsApp

**❌ Número não está registrado para WhatsApp Business**
- **Solução:**
  1. Complete o processo de verificação no Meta for Developers
  2. Aguarde aprovação (pode levar até 24h)
  3. Verifique se o número está no formato correto (+5554999999999)

### 4.3 Logs para Diagnóstico

**Ver logs do backend:**
```bash
tail -f /var/log/supervisor/backend.*.log
```

**Ver logs específicos do WhatsApp/Google Drive:**
```bash
# Os logs aparecem com prefixos como:
# "Error generating Google Drive auth URL"
# "Error sending WhatsApp message"
```

---

## 5. 📞 Suporte

Se encontrar problemas durante a configuração:

1. **Verifique os logs do sistema**
2. **Teste as APIs individualmente**  
3. **Consulte a documentação oficial:**
   - Google Drive API: https://developers.google.com/drive
   - WhatsApp Business API: https://developers.facebook.com/docs/whatsapp

4. **Contato técnico:** 
   - Email: suporte@gbadvocacia.com
   - Telefone: +55 54 99710-2525

---

## 🎯 Resumo dos Arquivos Importantes

```
/app/backend/
├── .env                          # Configurações WhatsApp/Google Drive  
├── google_credentials.json       # Credenciais Google (criar)
├── token.json                    # Token OAuth (gerado automaticamente)
└── google_credentials_example.json # Exemplo de configuração

Logs:
├── /var/log/supervisor/backend.*.log # Logs do sistema
```

**🚀 Após seguir este guia, suas integrações estarão funcionais em produção!**