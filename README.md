# patch_fix_gc

`patch_fix_gc` é um utilitário genérico para melhorar a estabilidade do Visual Studio 2022 com GitHub Copilot, atuando como pré-processador de arquivos antes da análise.

## Funcionalidades implementadas

- Sanitização de arquivos (BOM/zero-width, finais de linha, tabs, trailing spaces)
- Normalização de codificação (UTF-8, acentuação NFC, remoção de caracteres de controle inválidos)
- Quebra automática de strings longas em blocos menores (extensões de código suportadas)
- Tratamento de arquivos gerados (`.Designer.cs`, `.g.cs`, `.generated.cs`)
- Detecção de repetição de leitura de arquivo (loop de `get_file`) com log e sugestão de limpeza de cache
- Limpeza automática de temporários (`.vs/`, `bin/`, `obj/`, `.cache/`, `.tmp`, `.bak`)
- Logs inteligentes em `.patch_fix_gc/patch_fix_gc.log`
- Otimização opcional para identificar e dividir arquivos muito grandes

## Estrutura

```
/patch_fix_gc
├── patch_fix_gc.py
├── README.md
├── config.json
└── modules/
    ├── sanitize.py
    ├── split_strings.py
    ├── fix_encoding.py
    ├── optimize.py
    └── logs.py
```

## Como executar

```bash
python patch_fix_gc.py --root . --config config.json
```

## Integração no VS2022

### A) Pre-Build Event

```text
python "$(ProjectDir)\tools\patch_fix_gc.py"
```

### B) External Tools

- Title: `patch_fix_gc`
- Command: `python.exe`
- Arguments: `$(ProjectDir)\tools\patch_fix_gc.py`
- Initial Directory: `$(ProjectDir)`

### C) Task Runner Explorer

Registre a execução do script usando seu fluxo (`package.json`, `.targets` ou MSBuild customizado).
