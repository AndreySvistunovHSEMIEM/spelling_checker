; Установщик для Orfocode
#define MyAppName "Orfocode"
#define MyAppVersion "0.1"
#define MyAppPublisher "Rothgust"
#define MyAppExeName "Orfocode.exe"

[Setup]
AppId={{846A69CD-FFE3-4A39-A7F3-49A9974E6DBF}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={commonpf32}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=.\Output
OutputBaseFilename=Orfocode_Setup
SetupIconFile=app_icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

; ВСЕГДА ДЛЯ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ (как в большинстве программ)
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=commandline

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; Flags: checkedonce

[Files]
; Копируем все файлы из директории сборки
Source: "dist\Orfocode\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{group}\Удалить {#MyAppName}"; Filename: "{uninstallexe}"; IconFilename: "{uninstallexe}"; Comment: "Удалить {#MyAppName}"

[Code]
// Функция для создания директории данных в AppData
function AppDataPath(): string;
begin
  Result := ExpandConstant('{userappdata}\Orfocode');
end;

// Функция для перемещения данных пользователя в AppData
procedure MoveUserDataToAppData();
var
  SourcePath, DestPath: string;
  ResultCode: Integer;
begin
  // Создаем директорию AppData
  if not DirExists(AppDataPath()) then
  begin
    if not ForceDirectories(AppDataPath()) then
    begin
      MsgBox('Не удалось создать директорию: ' + AppDataPath(), mbError, MB_OK);
      Exit;
    end;
  end;

  // Перемещаем JSON файлы из _internal\core
  SourcePath := ExpandConstant('{app}\_internal\core\words.json');
  if FileExists(SourcePath) then
  begin
    DestPath := AppDataPath() + '\words.json';
    // Копируем только если файл еще не существует в AppData
    if not FileExists(DestPath) then
      FileCopy(SourcePath, DestPath, False);
    // Удаляем исходный файл из Program Files
    DeleteFile(SourcePath);
  end;

  SourcePath := ExpandConstant('{app}\_internal\core\progress.json');
  if FileExists(SourcePath) then
  begin
    DestPath := AppDataPath() + '\progress.json';
    if not FileExists(DestPath) then
      FileCopy(SourcePath, DestPath, False);
    DeleteFile(SourcePath);
  end;

  SourcePath := ExpandConstant('{app}\_internal\core\settings.json');
  if FileExists(SourcePath) then
  begin
    DestPath := AppDataPath() + '\settings.json';
    if not FileExists(DestPath) then
      FileCopy(SourcePath, DestPath, False);
    DeleteFile(SourcePath);
  end;

  // Перемещаем папку images из _internal\core
  SourcePath := ExpandConstant('{app}\_internal\core\images');
  if DirExists(SourcePath) then
  begin
    DestPath := AppDataPath() + '\images';
    // Копируем только если папка не существует в AppData
    if not DirExists(DestPath) then
    begin
      if not ForceDirectories(DestPath) then
      begin
        MsgBox('Не удалось создать директорию: ' + DestPath, mbError, MB_OK);
        Exit;
      end;
      // Копируем содержимое папки
      Exec(ExpandConstant('{sys}\xcopy.exe'), '"' + SourcePath + '" "' + DestPath + '" /E /I /Y', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end;
    // Удаляем исходную папку с содержимым
    DelTree(SourcePath, True, True, True);
  end;

  // Перемещаем папку audio из _internal\core
  SourcePath := ExpandConstant('{app}\_internal\core\audio');
  if DirExists(SourcePath) then
  begin
    DestPath := AppDataPath() + '\audio';
    if not DirExists(DestPath) then
    begin
      if not ForceDirectories(DestPath) then
      begin
        MsgBox('Не удалось создать директорию: ' + DestPath, mbError, MB_OK);
        Exit;
      end;
      // Копируем содержимое папки
      Exec(ExpandConstant('{sys}\xcopy.exe'), '"' + SourcePath + '" "' + DestPath + '" /E /I /Y', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    end;
    // Удаляем исходную папку с содержимым
    DelTree(SourcePath, True, True, True);
  end;
end;

// Функция удаления приложения - удаляем и AppData
function InitializeUninstall(): Boolean;
begin
  Result := True;
end;

// Дополнительная функция для обработки удаления данных пользователя
procedure UninstallUserData();
var
  Response: Integer;
begin
  // Спрашиваем пользователя, хочет ли он удалить данные прогресса и настроек
  Response := MsgBox('Удалить ваш прогресс и настройки?' + #13#10 + '(Пройденные слова, статистика ошибок)', mbConfirmation, MB_YESNO);
  if Response = IDYES then
  begin
    // Удаляем папку AppData при деинсталляции
    if DirExists(AppDataPath()) then
    begin
      DelTree(AppDataPath(), True, True, True);
    end;
  end
  else
  begin
    // Если пользователь выбрал "Нет", удаляем только исполняемый файл и основные файлы установки, оставляя progress.json и settings.json
    if DirExists(AppDataPath()) then
    begin
      // Удаляем все файлы в папке AppData, кроме progress.json и settings.json
      DeleteFile(AppDataPath() + '\words.json');
      // Удаляем папку images, если она есть, но оставляем файлы progress.json и settings.json
      if DirExists(AppDataPath() + '\images') then
        DelTree(AppDataPath() + '\images', True, True, True);
      if DirExists(AppDataPath() + '\audio') then
        DelTree(AppDataPath() + '\audio', True, True, True);
    end;
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  case CurUninstallStep of
    usUninstall: begin
      // Вызываем функцию удаления пользовательских данных
      UninstallUserData();
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    MoveUserDataToAppData();
  end;
end;

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Запустить {#MyAppName}"; Flags: nowait postinstall skipifsilent