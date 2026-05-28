"""
╔══════════════════════════════════════════════════════════════╗
║     🚀  PUSH AUTOMÁTICO PARA O GITHUB                       ║
║     Projeto Inteligência Comercial                          ║
║     Felipe Huff | github.com/felipehuff610                  ║
╚══════════════════════════════════════════════════════════════╝

Como usar:
    python enviar_github.py

O script vai:
  1. Verificar se o Git está instalado
  2. Inicializar o repositório local (se ainda não existir)
  3. Conectar ao seu repo remoto no GitHub
  4. Adicionar todos os arquivos respeitando o .gitignore
  5. Fazer commit com mensagem automática ou personalizada
  6. Fazer o push pra branch main

Pré-requisitos:
  - Git instalado (https://git-scm.com/downloads)
  - Conta GitHub configurada (git config --global user.email ...)
  - Repositório criado no GitHub: Projeto_Inteligencia_Comercial
    (crie em: https://github.com/new)
"""

import os
import subprocess
import sys
from datetime import datetime


# ── configurações ──────────────────────────────────────────────────────────────

GITHUB_USER = "felipehuff610"
REPO_NAME   = "Projeto_Inteligencia_Comercial"
REPO_URL    = f"https://github.com/{GITHUB_USER}/{REPO_NAME}.git"
BRANCH      = "main"

# diretório raiz do projeto (onde este script está)
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))


# ── funções auxiliares ─────────────────────────────────────────────────────────

def cor(texto: str, codigo: str) -> str:
    """Colore o texto no terminal (funciona no Windows 10+ e Linux/Mac)."""
    cores = {
        "verde":    "\033[92m",
        "amarelo":  "\033[93m",
        "vermelho": "\033[91m",
        "ciano":    "\033[96m",
        "bold":     "\033[1m",
        "reset":    "\033[0m",
    }
    return f"{cores.get(codigo, '')}{texto}{cores['reset']}"


def linha(char: str = "─", tamanho: int = 60) -> None:
    print(char * tamanho)


def titulo(texto: str) -> None:
    linha()
    print(cor(f"  {texto}", "bold"))
    linha()


def ok(msg: str) -> None:
    print(cor(f"  ✓  {msg}", "verde"))


def info(msg: str) -> None:
    print(cor(f"  →  {msg}", "ciano"))


def aviso(msg: str) -> None:
    print(cor(f"  ⚠  {msg}", "amarelo"))


def erro(msg: str) -> None:
    print(cor(f"  ✗  {msg}", "vermelho"))


def rodar(comando: list[str], capturar: bool = False) -> subprocess.CompletedProcess:
    """Executa um comando shell e retorna o resultado."""
    resultado = subprocess.run(
        comando,
        cwd=PROJECT_DIR,
        capture_output=capturar,
        text=True,
    )
    return resultado


def git(*args, capturar: bool = False) -> subprocess.CompletedProcess:
    return rodar(["git"] + list(args), capturar=capturar)


# ── verificações ───────────────────────────────────────────────────────────────

def verificar_git() -> bool:
    """Checa se o Git está instalado e acessível."""
    resultado = rodar(["git", "--version"], capturar=True)
    if resultado.returncode == 0:
        versao = resultado.stdout.strip()
        ok(f"Git encontrado: {versao}")
        return True
    else:
        erro("Git não encontrado!")
        print()
        print("  Instale o Git em: https://git-scm.com/downloads")
        print("  Depois reinicie este script.")
        return False


def verificar_config_git() -> bool:
    """Verifica se nome e e-mail estão configurados no Git."""
    nome  = rodar(["git", "config", "--global", "user.name"],  capturar=True).stdout.strip()
    email = rodar(["git", "config", "--global", "user.email"], capturar=True).stdout.strip()

    if nome and email:
        ok(f"Identidade Git: {nome} <{email}>")
        return True
    else:
        erro("Identidade Git não configurada!")
        print()
        print("  Execute estes dois comandos e rode o script novamente:")
        print(cor('    git config --global user.name  "Felipe Huff"',       "ciano"))
        print(cor('    git config --global user.email "seu@email.com"',     "ciano"))
        return False


# ── operações Git ──────────────────────────────────────────────────────────────

def inicializar_repo() -> None:
    """Inicializa o repositório Git se ainda não existir."""
    git_dir = os.path.join(PROJECT_DIR, ".git")

    if os.path.isdir(git_dir):
        ok("Repositório Git já inicializado")
    else:
        info("Inicializando repositório Git...")
        git("init")
        git("checkout", "-b", BRANCH)
        ok("Repositório inicializado")


def configurar_remote() -> None:
    """Adiciona ou atualiza o remote 'origin'."""
    resultado = git("remote", "get-url", "origin", capturar=True)

    if resultado.returncode == 0:
        url_atual = resultado.stdout.strip()
        if url_atual != REPO_URL:
            aviso(f"Remote atual: {url_atual}")
            info(f"Atualizando para: {REPO_URL}")
            git("remote", "set-url", "origin", REPO_URL)
        ok(f"Remote configurado: {REPO_URL}")
    else:
        info(f"Adicionando remote origin: {REPO_URL}")
        git("remote", "add", "origin", REPO_URL)
        ok("Remote adicionado")


def listar_arquivos_staging() -> list[str]:
    """Retorna a lista de arquivos que serão enviados."""
    resultado = git("status", "--short", capturar=True)
    linhas = [l for l in resultado.stdout.strip().split("\n") if l.strip()]
    return linhas


def fazer_commit(mensagem: str) -> bool:
    """Adiciona todos os arquivos e faz o commit."""
    info("Adicionando arquivos ao staging...")
    git("add", ".")

    arquivos = listar_arquivos_staging()
    if not arquivos:
        aviso("Nenhuma alteração detectada — nada a commitar.")
        return False

    print()
    info(f"{len(arquivos)} arquivo(s) no commit:")
    for arq in arquivos[:15]:  # mostra no máximo 15
        print(f"     {arq}")
    if len(arquivos) > 15:
        print(f"     ... e mais {len(arquivos) - 15} arquivo(s)")

    print()
    resultado = git("commit", "-m", mensagem)
    if resultado.returncode == 0:
        ok(f'Commit criado: "{mensagem}"')
        return True
    else:
        # pode ser que não tenha nada novo depois do add
        aviso("Nada novo pra commitar (tudo já estava salvo).")
        return False


def fazer_push() -> bool:
    """Faz o push pra branch main."""
    info(f"Enviando para github.com/{GITHUB_USER}/{REPO_NAME}...")
    print()
    print(cor("  (o GitHub pode pedir seu usuário e token de acesso)", "amarelo"))
    print(cor("  → Token: GitHub → Settings → Developer Settings → Personal Access Tokens", "amarelo"))
    print()

    resultado = git("push", "-u", "origin", BRANCH)

    if resultado.returncode == 0:
        ok("Push concluído com sucesso!")
        return True
    else:
        erro("Falha no push.")
        print()
        print("  Possíveis causas:")
        print("  1. Repositório não existe no GitHub — crie em: https://github.com/new")
        print("     Nome: Projeto_Inteligencia_Comercial")
        print("  2. Token de acesso inválido ou expirado")
        print("     Gere um novo em: https://github.com/settings/tokens")
        print("  3. Conflito de histórico — rode manualmente:")
        print(cor("       git push --force-with-lease origin main", "ciano"))
        return False


# ── interface principal ────────────────────────────────────────────────────────

def main() -> None:
    os.system("")  # habilita cores ANSI no Windows

    print()
    print(cor("╔══════════════════════════════════════════════════════════════╗", "bold"))
    print(cor("║     🚀  PUSH AUTOMÁTICO — INTELIGÊNCIA COMERCIAL            ║", "bold"))
    print(cor("║     github.com/felipehuff610                                ║", "bold"))
    print(cor("╚══════════════════════════════════════════════════════════════╝", "bold"))
    print()

    # ── 1. verificações ──────────────────────────────────────────────────────
    titulo("1/5  Verificações de ambiente")

    if not verificar_git():
        sys.exit(1)

    if not verificar_config_git():
        sys.exit(1)

    # ── 2. init repo ─────────────────────────────────────────────────────────
    titulo("2/5  Repositório Git local")
    inicializar_repo()

    # ── 3. remote ────────────────────────────────────────────────────────────
    titulo("3/5  Conexão com GitHub")
    configurar_remote()

    # ── 4. mensagem do commit ─────────────────────────────────────────────────
    titulo("4/5  Mensagem do commit")

    msg_padrao = f"feat: atualização do projeto — {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    print(f"  Mensagem padrão: {cor(msg_padrao, 'ciano')}")
    print()

    resposta = input("  Usar essa mensagem? [Enter = sim | ou digite outra]: ").strip()
    mensagem_commit = resposta if resposta else msg_padrao
    print()

    # ── 5. commit + push ──────────────────────────────────────────────────────
    titulo("5/5  Commit & Push")

    houve_commit = fazer_commit(mensagem_commit)
    print()
    sucesso = fazer_push()

    # ── resultado final ───────────────────────────────────────────────────────
    print()
    linha("═")
    if sucesso:
        print()
        print(cor(f"  ✅  Projeto no ar!", "verde"))
        print(f"  🔗  https://github.com/{GITHUB_USER}/{REPO_NAME}")
        print()
    else:
        print()
        print(cor("  ❌  Algo deu errado. Veja as mensagens acima.", "vermelho"))
        print()
    linha("═")
    print()


if __name__ == "__main__":
    main()
