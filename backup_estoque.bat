@echo off
:: Define as pastas de origem e destino
set ORIGEM=C:\Users\gusta\projeto_estoque
set DESTINO=C:\Users\gusta\projeto_estoque\backups

:: Cria a pasta de destino caso ela não exista
if not exist "%DESTINO%" mkdir "%DESTINO%"

:: Formata a data para o nome do arquivo
set DATA=%date:/=-%

:: Copia o banco. O /Y confirma a substituição automática se o script rodar de novo no mesmo dia
copy "%ORIGEM%\estoque.db" "%DESTINO%\estoque_backup_%DATA%.db" /Y

:: Apaga backups com mais de 30 dias para economizar espaço
forfiles /p "%DESTINO%" /s /m *.db /d -30 /c "cmd /c del @path"

echo Backup realizado com sucesso em %DATA%!