"""
Script para gerar segredos internos do projeto.

Este script gera chaves seguras para uso interno da aplicação.
NÃO gera chaves de serviços externos (OpenAI, Supabase, etc.).

Uso:
    python infra/scripts/generate_secrets.py

Ou:
    python -c "import secrets; print(secrets.token_urlsafe(32))"
"""

import secrets
import hashlib
import os
from pathlib import Path


def generate_secret_key(length: int = 32) -> str:
    """Gera uma chave secreta segura usando URL-safe base64."""
    return secrets.token_urlsafe(length)


def generate_encryption_key() -> str:
    """Gera uma chave de encriptação (32 bytes para Fernet)."""
    # Fernet requer 32 bytes url-safe base64-encoded
    return secrets.token_urlsafe(32)


def generate_hash_secret() -> str:
    """Gera um secret para hashing."""
    return secrets.token_hex(32)


def generate_all_secrets() -> dict:
    """Gera todos os segredos internos necessários."""
    return {
        "APP_SECRET_KEY": generate_secret_key(32),
        "SESSION_SECRET": generate_secret_key(32),
        "WEBHOOK_SECRET": generate_secret_key(32),
        "ENCRYPTION_KEY": generate_encryption_key(),
    }


def check_env_file() -> Path:
    """Verifica se arquivo .env existe."""
    project_root = Path(__file__).parent.parent.parent
    env_file = project_root / ".env"
    return env_file


def update_env_file(secrets: dict) -> None:
    """Atualiza o arquivo .env com os segredos gerados."""
    env_file = check_env_file()
    
    if not env_file.exists():
        print(f"Arquivo .env não encontrado em {env_file}")
        print("Copie .env.example para .env primeiro:")
        print("  copy .env.example .env")
        return
    
    # Ler conteúdo atual
    content = env_file.read_text(encoding="utf-8")
    
    # Atualizar segredos
    lines = content.splitlines()
    updated_lines = []
    
    for line in lines:
        updated = False
        for key, value in secrets.items():
            if line.startswith(f"{key}="):
                # Manter valor se já estiver preenchido e não for placeholder
                current_value = line.split("=", 1)[1].strip()
                if current_value and current_value not in ["", '""', "''"]:
                    updated_lines.append(line)
                    updated = True
                    break
        
        if not updated:
            updated_lines.append(line)
    
    # Adicionar segredos que não existem no arquivo
    existing_keys = [line.split("=")[0] for line in lines if "=" in line]
    
    for key, value in secrets.items():
        if key not in existing_keys:
            updated_lines.append(f"{key}={value}")
    
    # Escrever arquivo atualizado
    env_file.write_text("\n".join(updated_lines), encoding="utf-8")
    print(f"Segredos atualizados em {env_file}")


def print_secrets(secrets: dict) -> None:
    """Imprime os segredos gerados (apenas para referência)."""
    print("\n" + "=" * 60)
    print("SEGREDOS GERADOS")
    print("=" * 60)
    print("\nAdicione estas linhas ao seu arquivo .env:\n")
    
    for key, value in secrets.items():
        print(f"{key}={value}")
    
    print("\n" + "=" * 60)
    print("IMPORTANTE: Mantenha estes segredos em segurança!")
    print("NÃO os compartilhe ou os coloque no repositório Git.")
    print("=" * 60 + "\n")


def main():
    """Função principal."""
    print("=" * 60)
    print("GERADOR DE SEGREDOS - SDR AGENT")
    print("=" * 60)
    
    # Gerar segredos
    secrets = generate_all_secrets()
    
    # Imprimir para referência
    print_secrets(secrets)
    
    # Modo silencioso se executado via script batch com redirecionamento
    import sys
    if not sys.stdin.isatty():
        # Execução não-interativa, apenas atualiza .env
        print("\nModo não-interativo: atualizando .env automaticamente...")
        update_env_file(secrets)
        print("\n✅ Segredos atualizados no arquivo .env")
        return
    
    # Perguntar se deve atualizar .env
    try:
        response = input("Deseja atualizar o arquivo .env automaticamente? (s/n): ")
        
        if response.lower() in ["s", "sim", "y", "yes"]:
            update_env_file(secrets)
            print("\n✅ Segredos atualizados no arquivo .env")
        else:
            print("\n⚠️ Copie manualmente os segredos acima para seu arquivo .env")
    except (EOFError, KeyboardInterrupt):
        # Se não houver input disponível (execução automática)
        print("\n⚠️ Modo não-interativo: copie manualmente os segredos para .env")
    
    print("\nPróximos passos:")
    print("1. Configure as chaves externas (OpenAI, Supabase, etc.)")
    print("2. Execute: infra\\scripts\\run_api.bat")
    print("3. Execute: infra\\scripts\\run_playground.bat")


if __name__ == "__main__":
    main()
