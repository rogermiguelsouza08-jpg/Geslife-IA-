"""
GES Life IA - Terminal de Portaria (Fase 5)
-----------------------------------------------
Este script roda o reconhecimento facial direto de uma câmera, contínuo,
falando pela caixa de som do PC — sem precisar abrir navegador. É o modo
pensado pra rodar 24h num computador ligado na câmera da portaria.

COMO USAR

  Com a webcam do computador (índice 0 é normalmente a primeira/única webcam):
      python portaria_standalone.py --fonte 0

  Com uma câmera IP / Intelbras via RTSP:
      python portaria_standalone.py --rtsp "rtsp://usuario:senha@192.168.0.50:554/stream1"

  Pra descobrir a URL RTSP da sua câmera Intelbras, normalmente segue o padrão:
      rtsp://usuario:senha@IP_DA_CAMERA:554/cam/realmonitor?channel=1&subtype=0
  (o IP, usuário e senha você configura no app/software da própria Intelbras
  usada pra instalar a câmera, ex: iNVD, Intelbras Cloud, ou o menu da câmera)

  Pra sair, pressione a tecla "q" com a janela da câmera em foco,
  ou feche o terminal.

O QUE ESSE SCRIPT FAZ

  1. Abre o vídeo da câmera continuamente
  2. A cada 1 segundo, procura um rosto no frame atual
  3. Se reconhecer alguém já cadastrado, gera a fala de orientação e
     FALA de verdade pela caixa de som do PC (voz offline, sem internet)
  4. Salva o registro no mesmo banco de dados usado pelo painel web
  5. Espera um tempo (cooldown) antes de falar de novo com a mesma pessoa,
     pra não ficar repetindo a mensagem toda hora
"""

import argparse
import time
import sys

import cv2
import pyttsx3

from app import face_service, ia, crud, schemas
from app.database import SessionLocal

COOLDOWN_SEGUNDOS = 20       # tempo mínimo entre duas falas pra mesma pessoa
INTERVALO_ANALISE_SEGUNDOS = 1.0  # de quanto em quanto tempo analisa um frame


def falar(engine, texto):
    print(f"🔊 IA fala: {texto}")
    if engine is None:
        return
    try:
        engine.say(texto)
        engine.runAndWait()
    except Exception as e:
        print(f"[aviso] não consegui usar a voz do sistema ({e}). "
              f"A mensagem acima foi gerada normalmente, só não foi falada em áudio.")


def iniciar_motor_de_voz():
    try:
        return pyttsx3.init()
    except Exception as e:
        print(f"[aviso] não foi possível iniciar o motor de voz do sistema ({e}).")
        print("        O reconhecimento vai continuar funcionando normalmente,")
        print("        só sem falar em áudio — as mensagens aparecem no terminal.")
        return None


def main():
    parser = argparse.ArgumentParser(description="GES Life IA - Terminal de portaria (reconhecimento contínuo)")
    parser.add_argument("--fonte", type=int, default=None, help="Índice da webcam (ex: 0)")
    parser.add_argument("--rtsp", type=str, default=None, help="URL RTSP da câmera IP/Intelbras")
    parser.add_argument("--sem-janela", action="store_true", help="Não mostra a janela de vídeo (só roda em segundo plano)")
    args = parser.parse_args()

    if args.rtsp:
        fonte = args.rtsp
    elif args.fonte is not None:
        fonte = args.fonte
    else:
        fonte = 0  # padrão: primeira webcam

    print(f"Conectando na fonte de vídeo: {fonte}")
    captura = cv2.VideoCapture(fonte)

    if not captura.isOpened():
        print("❌ Não consegui abrir essa câmera/fonte de vídeo. Verifique:")
        print("   - Se o índice da webcam está certo (tente 0, 1, 2...)")
        print("   - Se a URL RTSP está certa e a câmera está na mesma rede")
        sys.exit(1)

    print("✅ Câmera conectada. Iniciando reconhecimento contínuo...")
    print("   Pressione 'q' na janela de vídeo para sair (ou Ctrl+C no terminal).\n")

    engine = iniciar_motor_de_voz()
    db = SessionLocal()

    ultima_fala = {}   # nome da pessoa -> timestamp da última vez que falamos com ela
    ultima_analise = 0.0

    try:
        while True:
            ok, frame = captura.read()
            if not ok:
                print("⚠️  Sinal de vídeo perdido. Tentando reconectar...")
                time.sleep(2)
                captura.release()
                captura = cv2.VideoCapture(fonte)
                continue

            agora = time.time()

            if agora - ultima_analise >= INTERVALO_ANALISE_SEGUNDOS:
                ultima_analise = agora
                resultado = face_service.reconhecer(frame)

                if resultado["reconhecido"]:
                    nome = resultado["nome"]
                    ultima_vez = ultima_fala.get(nome, 0)

                    if agora - ultima_vez >= COOLDOWN_SEGUNDOS:
                        mensagem = ia.gerar_mensagem_orientacao(db, nome, resultado["apartamento"])

                        registro = schemas.RegistroAcessoCreate(
                            nome_pessoa=nome,
                            tipo_pessoa=resultado["tipo"],
                            apartamento_destino=resultado["apartamento"],
                            metodo="reconhecimento_facial",
                        )
                        crud.criar_registro(db, registro, mensagem_falada=mensagem)

                        falar(engine, mensagem)
                        ultima_fala[nome] = agora

            if not args.sem_janela:
                cv2.imshow("GES Life IA - Portaria (pressione 'q' para sair)", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

    except KeyboardInterrupt:
        print("\nEncerrando...")
    finally:
        captura.release()
        cv2.destroyAllWindows()
        db.close()


if __name__ == "__main__":
    main()
