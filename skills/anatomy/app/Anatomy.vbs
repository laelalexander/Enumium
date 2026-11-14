' Launches Anatomy with no console window. The desktop icon points here.
Set fso = CreateObject("Scripting.FileSystemObject")
dir = fso.GetParentFolderName(WScript.ScriptFullName)
root = "C:\Anatomy"
If WScript.Arguments.Count > 0 Then root = WScript.Arguments(0)
cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & dir & "\Start-Anatomy.ps1"" -Root """ & root & """"
CreateObject("WScript.Shell").Run cmd, 0, False
