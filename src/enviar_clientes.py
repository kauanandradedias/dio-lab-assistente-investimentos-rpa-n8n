"""RPA simples: lê clientes de um CSV e envia para o Webhook do N8N.

Uso:
    export N8N_WEBHOOK_URL="https://SEU-N8N/webhook-test/clientes"   # ou /webhook/clientes (produção)
    python src/enviar_clientes.py data/clientes_exemplo.csv

Colunas esperadas no CSV: nome, email, perfil, saldo
Perfis aceitos: conservador, moderado, arrojado
"""
import csv
import json
import os
import sys
import time

import requests

TENTATIVAS = 3
ESPERA_SEGUNDOS = 2
TIMEOUT_SEGUNDOS = 120  # o N8N só responde depois de enviar todos os e-mails


def ler_clientes(caminho_csv):
    clientes = []
    with open(caminho_csv, newline="", encoding="utf-8") as arquivo:
        for linha in csv.DictReader(arquivo):
            saldo = (linha.get("saldo") or "").replace(",", ".").strip()
            clientes.append(
                {
                    "nome": (linha.get("nome") or "").strip(),
                    "email": (linha.get("email") or "").strip(),
                    "perfil": (linha.get("perfil") or "moderado").strip().lower(),
                    "saldo": float(saldo) if saldo else None,
                }
            )
    return clientes


def enviar_para_n8n(url, clientes):
    carga = {"clientes": clientes}
    for tentativa in range(1, TENTATIVAS + 1):
        try:
            resposta = requests.post(url, json=carga, timeout=TIMEOUT_SEGUNDOS)
            if resposta.status_code < 500:
                return resposta
            print(f"Tentativa {tentativa}: servidor respondeu {resposta.status_code}")
        except requests.RequestException as erro:
            print(f"Tentativa {tentativa}: falha de conexão ({erro})")
        time.sleep(ESPERA_SEGUNDOS * tentativa)
    raise SystemExit("Não foi possível chamar o webhook do N8N após várias tentativas.")


def main():
    url = os.environ.get("N8N_WEBHOOK_URL")
    if not url:
        raise SystemExit("Defina a variável de ambiente N8N_WEBHOOK_URL com a URL do webhook.")
    caminho = sys.argv[1] if len(sys.argv) > 1 else "data/clientes_exemplo.csv"

    clientes = ler_clientes(caminho)
    print(f"{len(clientes)} cliente(s) lido(s) de {caminho}")

    resposta = enviar_para_n8n(url, clientes)
    print(f"Status: {resposta.status_code}")
    try:
        print(json.dumps(resposta.json(), indent=2, ensure_ascii=False))
    except ValueError:
        print(resposta.text)


if __name__ == "__main__":
    main()
