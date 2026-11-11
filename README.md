# GES Life IA — Fase 1 a 5 (versão completa)

Sistema de reconhecimento e orientação inteligente para condomínios.
Está tudo funcionando de verdade: **banco de dados + API + painel visual +
reconhecimento facial + a IA falando em voz + modo automático + terminal
standalone pra rodar 24h na portaria.**

## O que já funciona

- **Painel visual** em `http://127.0.0.1:8000/` com:
  - Dashboard com indicadores (moradores, visitantes, rotas, orientações)
  - **Câmera (reconhecimento)**: liga a webcam do seu PC, reconhece o rosto
    de quem já foi cadastrado e a IA fala (de verdade, em voz, pelo
    navegador) a orientação — igual ao exemplo do Roger/21B
  - **Modo automático**: liga e a IA fica reconhecendo sozinha, tipo um
    totem de portaria, sem precisar ficar clicando (com um intervalo de
    20s pra não ficar repetindo a fala da mesma pessoa parada na câmera)
  - Cadastro de rosto: tire uma foto da pessoa (morador ou visitante) pela
    própria câmera para ensinar a IA a reconhecê-la
  - Tela "Reconhecer / Orientar" manual (digitando o nome), pra quando não
    tiver câmera à mão
  - Cadastro de Moradores, Visitantes e Rotas
  - Histórico completo de orientações (mostra se foi por reconhecimento
    facial ou manual)
- **Terminal de portaria standalone** (`portaria_standalone.py`): roda
  fora do navegador, direto no terminal, ligado numa câmera (webcam ou
  câmera Intelbras via RTSP), reconhecendo continuamente e falando pela
  caixa de som do PC — pensado pra ficar rodando 24h num computador perto
  da portaria/catraca.

## Como funciona por baixo dos panos

- **Reconhecimento**: OpenCV (Haar Cascade acha o rosto na imagem + LBPH
  identifica de quem é). Leve, roda bem em qualquer PC/Windows.
- **Voz no painel web**: Web Speech API do navegador (grátis, offline, sem
  precisar de chave de API).
- **Voz no terminal standalone**: pyttsx3, que no Windows usa o motor de
  voz que já vem instalado no sistema (SAPI5) — também grátis e offline.

## Como usar a câmera Intelbras de verdade (RTSP)

O painel web usa a webcam do PC (mais simples de testar). Pra usar a
câmera Intelbras da portaria, use o **terminal standalone**:

```powershell
python portaria_standalone.py --rtsp "rtsp://usuario:senha@IP_DA_CAMERA:554/cam/realmonitor?channel=1&subtype=0"
```

O usuário, senha e IP você configura no próprio app/software da Intelbras
usado pra instalar a câmera. Se não tiver certeza da URL exata, me manda o
modelo da câmera Intelbras que a gente ajusta juntos.

Pra testar primeiro com a webcam do notebook antes de mexer na câmera de
verdade:
```powershell
python portaria_standalone.py --fonte 0
```
(pressione "q" com a janela de vídeo em foco pra encerrar)

## Como rodar no seu computador (Windows + VS Code)

### 1. Extrair a pasta
Extraia o `.zip` em algum lugar, ex: `C:\Projetos\geslife_ia` (pode
sobrescrever a pasta de uma versão anterior).

### 2. Abrir no VS Code
Abra a pasta `geslife_ia` no VS Code.

### 3. Abrir o terminal (PowerShell) dentro do VS Code
Menu: **Terminal > New Terminal**

### 4. Criar e ativar o ambiente virtual
```powershell
python -m venv venv
venv\Scripts\activate
```
(Se aparecer erro de permissão, rode antes: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`)

### 5. Instalar as dependências
```powershell
pip install -r requirements.txt
```

### 6. Rodar o painel web
```powershell
uvicorn app.main:app --reload
```

### 7. Testar o painel
Abra no navegador: **http://127.0.0.1:8000/**

Sugestão de teste, na ordem:

1. Vá em **Moradores** → cadastre alguém (ex: você mesmo)
2. Vá em **Rotas** → cadastre o apartamento dessa pessoa com as instruções
   (ex: "Siga reto, pegue a esquerda e pegue o elevador até o segundo andar")
3. Vá em **Câmera (reconhecimento)**:
   - Clique em **Ligar câmera** (o navegador vai pedir permissão — aceite)
   - Do lado direito, em "Cadastrar rosto de uma pessoa", selecione a
     pessoa que você cadastrou e clique em **Capturar foto e cadastrar
     rosto** (olhe pra câmera, com boa luz)
   - Do lado esquerdo, clique em **Reconhecer agora**, ou ligue o **Modo
     automático** — se tudo der certo, a tela mostra seu nome reconhecido
     e a IA **fala em voz alta** a orientação
4. Veja o **Dashboard** e o **Histórico** atualizarem automaticamente

### 8. Testar o terminal standalone (opcional, com o painel web fechado ou aberto)
```powershell
python portaria_standalone.py --fonte 0
```

**Dica se não reconhecer bem:** cadastre 2 ou 3 fotos da mesma pessoa em
ângulos/luzes um pouco diferentes (repita o passo de cadastro de rosto) —
isso melhora bastante a precisão do LBPH.

Se quiser mexer diretamente na API (sem o painel), ela continua disponível
em **http://127.0.0.1:8000/docs**.

O banco de dados (`geslife.db`) é criado automaticamente na primeira vez
que você roda o servidor, na mesma pasta do projeto, e é **o mesmo banco**
usado tanto pelo painel web quanto pelo terminal standalone.

## Estrutura de pastas

```
geslife_ia/
├── portaria_standalone.py -> terminal de portaria (câmera + voz, sem navegador)
├── app/
│   ├── main.py           -> endpoints da API + serve o painel visual
│   ├── models.py         -> as "tabelas" do banco de dados
│   ├── schemas.py        -> formato dos dados de entrada/saída
│   ├── crud.py           -> funções que leem/gravam no banco
│   ├── database.py       -> configuração da conexão com o banco
│   ├── ia.py              -> o "cérebro" que gera a frase de orientação
│   ├── face_service.py    -> reconhecimento facial (OpenCV: Haar + LBPH)
│   ├── data/               -> fotos de rosto + modelo treinado (criado sozinho)
│   └── static/             -> o painel visual (front-end)
│       ├── index.html
│       ├── style.css
│       └── script.js
├── requirements.txt
└── README.md
```

Isso é o projeto inteiro — vários arquivos organizados por função, dentro
de uma única pasta/pacote. É assim que todo sistema de verdade é feito
(inclusive o painel da SegLife que você usou de referência); não existe
"um arquivo só" pra esse tipo de sistema.

## O que ainda pode evoluir (melhorias, não obrigatório)

- Trocar o SQLite por PostgreSQL se um dia precisar atender vários
  condomínios ao mesmo tempo com muito volume de dados
- Tela de login/permissões (hoje qualquer um que abrir o painel vê tudo)
- Deixar o `portaria_standalone.py` rodando sozinho quando o Windows liga
  (usando o Agendador de Tarefas do Windows)
- Publicar o painel web num servidor/nuvem, pra acessar de qualquer lugar
  (hoje ele roda só localmente, na rede do condomínio)

Me fala qual dessas você quer priorizar quando for a hora.
