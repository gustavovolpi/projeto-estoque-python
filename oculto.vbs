Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "C:\Users\gusta\projeto_estoque\iniciar_estoque.bat" & Chr(34), 0
Set WshShell = Nothing