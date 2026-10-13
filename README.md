# Mapa Quests Free — Desktop v1.8

Aplicativo desktop em Python + Tkinter. Abre em janela própria, sem navegador, Node.js ou servidor local. Não usa timers, threads ou consultas automáticas em segundo plano durante o uso normal.

## Executar no VS Code (Windows)
1. Instale Python 3.11+ e marque **Add Python to PATH** durante a instalação.
2. Extraia o ZIP.
3. No VS Code, abra a pasta `Mapa_Quests_Free_Desktop_v1_8`.
4. Abra **Terminal → Novo Terminal** e execute:
   ```powershell
   python main.py
   ```
   Se necessário, tente `py main.py`.

## Validar catálogo e testar a lógica
```powershell
python validate_catalog.py
python -m unittest test_logic.py -v
```
O validador verifica tipos, campos, nomes duplicados, status, coordenadas ilustrativas e URLs declaradas. Para uma tentativa de verificar as respostas HTTP das URLs (não valida o conteúdo da página), rode opcionalmente:
```powershell
python validate_catalog.py --check-links
```
A consulta online pode ser afetada por rede, bloqueios ou respostas do servidor. Não é necessária para abrir o aplicativo.

## Gerar um EXE Windows
No Windows, dentro do terminal do VS Code:
```powershell
python -m pip install --upgrade pip
python -m pip install pyinstaller
python -m PyInstaller --noconfirm --clean --windowed --onefile --name "MapaQuestsFree" --add-data "quests.json;." --add-data "mapa_3d.html;." --add-data "quests_data.js;." --hidden-import mapa_3d_launcher main.py
```
O executável ficará em `dist\MapaQuestsFree.exe`. O EXE precisa ser compilado no Windows.

## O que mudou na v1.8
- **Catálogo completo por padrão:** o level do jogador já não esconde automaticamente quests de níveis mais altos. Ative `Limitar catálogo ao meu level` se quiser esse filtro.
- A preferência do filtro por level é salva junto do level e das quests concluídas.
- Busca ampliada para incluir pré-requisitos, localização, habilidades e Pokémon necessários.
- Fichas exibem Pokémon e habilidades necessários em campos separados; exportação CSV inclui `abilities_required` e `source_note`.
- Carregamento do catálogo mais resiliente a nomes duplicados por diferença de maiúsculas/minúsculas e a campos de lista malformados.
- Validador reforçado: rejeita booleanos como level, confere listas, coordenadas e coerência dos status. Opção de auditoria HTTP é explícita e opcional.
- Notas de fonte atualizadas para as seis quests Premium e para Boost Free com páginas individuais consultadas nesta revisão.
- Mantidos o perfil local, as abas individuais, o fechamento de abas, a exportação CSV e o mapa conceitual.

## Onde o progresso é salvo
O arquivo fica em `~/.mapa_quests_free/progress.json` (no Windows, normalmente `%USERPROFILE%\.mapa_quests_free\progress.json`). Contém level, preferência de filtro e nomes de quests concluídas. Não é enviado a nenhum servidor. O formato antigo de lista de quests concluídas continua sendo lido.

## Fontes e limitações
- Índice geral: https://wiki.otponline.com/Quests
- Boost Free: https://wiki.otponline.com/Boost_Free — página individual informa level 250+, Pokémon com Surf e VIP: Não.
- A Lost Melody, Burned, Boost Hell, Milotic, Remembrance e Porta 999 foram conferidas individualmente e têm requisito Premium/VIP documentado nas respectivas páginas. Continuam fora das recomendações Free.
- **Somente Boost Free** está marcada como Free confirmada. As outras 57 entradas permanecem pendentes ou excluídas como Premium. A presença no índice geral não basta para confirmar acesso Free.
- Localizações, requisitos e recompensas de muitas quests ainda precisam de validação individual. O mapa e seus marcadores são conceituais/ilustrativos, não coordenadas oficiais.
- Os testes automatizados são testes offline de lógica e armazenamento. A interface visual ainda precisa ser testada num Windows real e o `.exe` não foi compilado nesta revisão.

Projeto comunitário não oficial, sem afiliação com os responsáveis pelo otPokémon.


## v1.8 — visualizador 3D e auditoria do índice
- Adicionado `mapa_3d.html`: visualizador interativo Three.js/WebGL em janela desktop opcional via pywebview.
- Marcadores 3D animados por status, ilhas conceituais, órbita por arraste, zoom e ficha de detalhes por quest.
- Instale a janela desktop 3D com `python -m pip install pywebview`. No Windows pode ser necessário o WebView2 Runtime. A biblioteca Three.js é carregada via CDN, portanto requer internet. Sem pywebview o app principal continua funcionando e informa como ativar o 3D.
- Níveis/recompensas alinhados com o índice geral da Wiki consultado em 12/10/2026; consulte `auditoria_wiki.json`. Isso não comprova acesso Free/Premium nem todos os requisitos. Quests pendentes continuam pendentes.
- O mapa 3D é conceitual e não representa coordenadas oficiais.


## v1.8 — correções e estabilidade
- Corrigida a classificação da entrada `999`: a página individual Porta 999 informa requisito VIP; agora é excluída do fluxo Free.
- Páginas individuais com evidência explícita foram registradas no `auditoria_wiki.json`: Boost Free, A Lost Melody, Boost Hell, Burned, Milotic, Remembrance e Porta 999.
- O visualizador 3D agora roda em processo separado (`mapa_3d_launcher.py`), evitando bloquear a janela principal do Tkinter enquanto o mapa está aberto.
- O renderizador usa `renderer.setAnimationLoop()` e libera o loop e recursos gráficos ao fechar a janela, seguindo a recomendação da documentação Three.js.
- O mapa permanece conceitual. A verificação de URL ou a leitura do índice geral não substitui a validação de requisitos de cada quest.
- Dependências para 3D: `python -m pip install pywebview`. O mapa carrega Three.js por CDN e precisa de internet.

## v1.9 — mapa por região
- Mapas 2D e 3D agora posicionam cada quest dentro da ilha da sua região (layout compartilhado em `map_layout.py`). Depois de editar `quests.json`, rode `python map_layout.py` para recalcular as posições e regenerar `quests_data.js`.
- Mapa 2D: tooltip, marcadores de concluídas e de quests acima do level, clique na ilha filtra a região e legenda real.
- Mapa 3D: ilhas por região, filtros que afetam os marcadores, hover, foco de câmera e progresso do jogador.
- Mapa 3D funciona no EXE, abrindo via `--mapa-3d`.
- Correções de scroll no macOS e Linux.
