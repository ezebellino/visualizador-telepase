Option Explicit

Dim fso, shell, scriptDir, projectRoot, pythonwPath, appPath, command

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
projectRoot = fso.GetParentFolderName(scriptDir)
pythonwPath = fso.BuildPath(fso.BuildPath(projectRoot, "Sistema_Python"), "pythonw.exe")
appPath = fso.BuildPath(projectRoot, "app.py")

If Not fso.FileExists(pythonwPath) Then
    MsgBox "No se encontro pythonw.exe en Sistema_Python.", vbCritical, "Visualizador Telepase"
    WScript.Quit 1
End If

If Not fso.FileExists(appPath) Then
    MsgBox "No se encontro app.py en la carpeta del proyecto.", vbCritical, "Visualizador Telepase"
    WScript.Quit 1
End If

command = """" & pythonwPath & """" _
    & " -m streamlit run " & """" & appPath & """" _
    & " --server.headless=true --server.port=8501 --server.address=127.0.0.1"

shell.CurrentDirectory = projectRoot
shell.Run command, 0, False

WScript.Sleep 3000
shell.Run "http://localhost:8501", 1, False
