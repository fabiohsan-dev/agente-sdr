"""Testar parser de mensagens."""

from app.services.message_parser import parse_message, parse_for_chatwoot

print("=" * 60)
print("TESTE DO PARSER DE MENSAGENS")
print("=" * 60)
print()

# Teste 1: Formato correto
print("Teste 1: Formato com separador \\\\")
texto1 = "Faaaaala João, muito bom te ver por aqui!\\\\[MEDIA:AUDIO_PADRAO]"
result1 = parse_message(texto1)
print(f"  Entrada: {repr(texto1)}")
print(f"  Texto: {result1['text']}")
print(f"  Mídia: {result1['media']}")
print()

# Teste 2: Com espaço
print("Teste 2: Com espaço")
texto2 = "Faaaaala! Muito bom te ver por aqui! \\\\ [MEDIA:AUDIO_PADRAO]"
result2 = parse_message(texto2)
print(f"  Entrada: {repr(texto2)}")
print(f"  Texto: {result2['text']}")
print(f"  Mídia: {result2['media']}")
print()

# Teste 3: Formato Chatwoot
print("Teste 3: Formato Chatwoot")
texto3 = "Olá!\\\\[MEDIA:AUDIO_PADRAO]"
result3 = parse_for_chatwoot(texto3)
print(f"  Entrada: {repr(texto3)}")
print(f"  Content: {result3['content']}")
print(f"  Media: {result3['media']}")
print(f"  Private: {result3['private']}")
print()

print("=" * 60)
