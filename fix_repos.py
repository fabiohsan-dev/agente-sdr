"""
Corrige todos os repositórios para Supabase 2.28+:
- Queries de LEITURA: .table().select("*").eq().execute()  (select obrigatório no início)
- Queries de INSERT:  .table().insert().execute()           (sem select)
- Queries de UPDATE:  .table().update().eq().execute()      (sem select)
"""
import os

repos_dir = "app/repositories"
files = [f for f in os.listdir(repos_dir) if f.endswith(".py") and f != "__init__.py"]

for fname in files:
    path = os.path.join(repos_dir, fname)
    with open(path, encoding="utf-8") as f:
        content = f.read()

    # Detectar blocos do tipo:
    # .table("X")
    # .eq(...)    <-- PROBLEMA: falta .select("*") antes do .eq
    # .execute()

    # Regex para encontrar .table("X").eq( ou .table("X")\n.eq( sem .select() no meio
    # Vamos usar uma abordagem mais robusta: reescrever linha a linha

    lines = content.split("\n")
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Detectar linha que começa um bloco de query de leitura SEM select:
        # Padrão: .table("X") seguido por .eq( (sem .select( no meio)
        if stripped.startswith(".eq(") or stripped.startswith(".order(") or stripped.startswith(".limit("):
            # Verificar se a linha anterior (no acumulado) já tem .select ou .update ou .insert
            # Olhar para trás nas new_lines para verificar o contexto
            context_back = []
            j = len(new_lines) - 1
            while j >= 0 and len(context_back) < 5:
                context_back.append(new_lines[j].strip())
                j -= 1

            has_select = any(".select(" in line_ctx for line_ctx in context_back)
            has_insert = any(".insert(" in line_ctx for line_ctx in context_back)
            has_update = any(".update(" in line_ctx for line_ctx in context_back)

            if not has_select and not has_insert and not has_update:
                # É uma query de leitura sem .select() - precisamos adicionar
                # Encontrar a indentação correta
                indent = len(line) - len(line.lstrip())
                indent_str = " " * indent
                new_lines.append(f'{indent_str}.select("*")')

        new_lines.append(line)
        i += 1

    new_content = "\n".join(new_lines)

    if new_content != content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Fixed: {fname}")
    else:
        print(f"No changes needed: {fname}")

print("\nDone!")
