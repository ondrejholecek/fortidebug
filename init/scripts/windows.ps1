$skip_python_install       = $FALSE
$skip_libs_install         = $FALSE
$skip_fortidebug_install = $FALSE
$skip_shortcuts            = $FALSE

$python_version = "2.7.15"
$python_dir     = "C:\Python27"
if ($env:PROCESSOR_ARCHITECTURE -eq "AMD64") {
    $python_arch    = ".amd64"
} else {
    $python_arch    = ""
}

$fortidebug_url = "https://github.com/ondrejholecek/fortidebug/archive/master.zip"

$pdir = (Split-Path -Path (Get-Location).Path -Parent)

if (Test-Path -Path "$pdir\lib\SSHCommands.py") {
    echo "- Seems we are initiating from FortiDebug directory, disabling FortiDebug installation"
    $skip_fortidebug_install = $TRUE
    $fortidebug_dir = $pdir
} else {
    echo "- Seems we are initiating from standalone setup file, installing FortiDebug from URL"
    $skip_fortidebug_install = $FALSE
    $fortidebug_dir = "C:\FortiDebug"
}

if ( ($skip_python_install -ne $TRUE) -And (Test-Path -Path $python_dir) ) {
    echo "- Python is already installed, skipping the instalation"
    $skip_python_install = $TRUE
}

if ($skip_python_install -ne $TRUE) {
    $python_url = "https://www.python.org/ftp/python/$python_version/python-$python_version$python_arch.msi"
    $python_msi = [System.IO.Path]::GetTempFileName() | Rename-Item -NewName { $_ -replace 'tmp$', 'msi' } -PassThru

    echo "- Downloading Python from $python_url to $python_msi"
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $python_url -OutFile $python_msi

    echo "- Installing Python to C:\\Python27"
    Start-Process -Wait -FilePath msiexec -ArgumentList "/q /i $python_msi TARGETDIR=$python_dir ALLUSERS=1"
} else {
    echo "- Skipping Python installation (expecting Python already installed in $python_dir)"
}

if ($skip_libs_install -ne $TRUE) {
    echo "- Installing the Python libraries we need"
    Invoke-Expression -Command "$python_dir\Scripts\pip.exe -q install paramiko requests pytz"
} else {
    echo "- Skipping Python libraries installation"
}

if ($skip_fortidebug_install -ne $TRUE) {
    $fortidebug_zip = [System.IO.Path]::GetTempFileName() | Rename-Item -NewName { $_ -replace 'tmp$', 'zip' } -PassThru
    echo "- Downloading FortiDebug application from $fortidebug_url to $fortidebug_zip"

    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $fortidebug_url -OutFile $fortidebug_zip

    echo "- Extracting FortiDebug application to $fortidebug_dir"
    rm -r $fortidebug_dir -Force -ErrorAction Ignore
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($fortidebug_zip, $fortidebug_dir)
    $fortidebug_dir = "$fortidebug_dir\fortidebug-master"

    echo "- Delete downloaded zip file $fortidebug_zip"
    del $fortidebug_zip
} else {
    echo "- Skipping FortiDebug installation"
}

if ($skip_shortcuts -ne $TRUE) {
    echo "- Creating Desktop shortcuts"
    $sh = New-Object -ComObject ("WScript.Shell")
    
    $scat = $sh.CreateShortcut($env:USERPROFILE + "\Desktop\FortiDebug ScriptGUI.lnk")
    $scat.TargetPath = "$fortidebug_dir\auxi\scriptgui.py"
    $scat.WorkingDirectory = "$fortidebug_dir\auxi"
    $scat.Save()

    $scat = $sh.CreateShortcut($env:USERPROFILE + "\Desktop\FortiDebug Utilities.lnk")
    $scat.TargetPath = "cmd.exe"
    $scat.WorkingDirectory = "$fortidebug_dir\utilities"
    $scat.Save()

} else {
    echo "- Skipping shortcuts creation"
}

if (!$skip_python_install) {
    echo "- Deleting downloaded Python msi file $python_msi"
    del $python_msi
} 
