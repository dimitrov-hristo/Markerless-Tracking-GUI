Set WshShell = CreateObject("WScript.Shell")
WshShell.Run chr(34) & "C:\Path\To\Current\Directory\batch_executable.bat" & Chr(34), 0
Set WshShell = Nothing
