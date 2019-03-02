#
# Script to capture changes in VM console in VMware (either vCenter or directly on ESXi)
# written by Ondrej Holecek <oholecek@fortinet.com>
#
 
#
# Comment this section out and uncomment the next one if you one to have these settings static
#
param (
   [Parameter(Mandatory=$true)][string]$VMhost,
   [Parameter(Mandatory=$true)][string]$Username,
   [Parameter(Mandatory=$false)][string]$Password = "",
   [Parameter(Mandatory=$true)][string]$VMname,
   [Parameter(Mandatory=$false)][string]$Directory = (Join-Path -Path ( [Environment]::GetFolderPath("Desktop"), $env:HOME | Where-Object {$_ -notlike ""} | Select -First 1) -ChildPath "vmware-screenshots")    
)

#
# Uncomment and configure following variables if you don't want to enter them on command line
#
#$VMhost = "vcenter.somehwere.net"
#$Username = "administrator@vsphere.local"
#$VMName = "kryten-esx09*"
#$Directory = [Environment]::GetFolderPath("Desktop") + "\vmware-screenshots"
#$Password = "xxx"

# internal powershell variable to hide progress bar
$progressPreference = 'silentlyContinue'
# ignore improvement program and certificates
Set-PowerCLIConfiguration -Scope User -ParticipateInCEIP $false -InvalidCertificateAction Ignore -Confirm:$false | Out-Null

try {
    New-Item -ItemType Directory -Force -Path $Directory | Out-Null
} catch {
    Write-Host -ForegroundColor Red "Cannot create directory $Directory"
    Exit
}

if ($Password.Length -eq 0) {
    $cred = Get-Credential -Message "Please provide admin user and password for vCenter server" -UserName $Username
} else {
    $cred = New-Object System.Management.Automation.PSCredential ($Username, (ConvertTo-SecureString $Password -AsPlainText -Force))
}

if (!(Get-Command "Connect-VIServer" -errorAction SilentlyContinue)) {
    Write-Host -ForegroundColor Red "It seems that the PowerCLI is not installed."
    Write-Host -ForegroundColor Red "Please start 'cmd' as Administrator, start 'powershell' program and enter following command:"
    Write-Host -ForegroundColor White "Install-Module -Scope AllUsers -Name VMware.PowerCLI -Force"
    Write-Host -ForegroundColor Red "... then please run this program again."
    Exit 
}

$con = Connect-VIServer -Credential $cred -Server $VMhost
if (!$con) {
    Write-Host -ForegroundColor Red "Unable to connect to vCenter/ESXi host. Check the username or password"
    Exit
}


# If this is Windows-only powershell, globally disable invalidating SSL certificates
if ($PSVersionTable.OS -eq $NULL) {
	if ("TrustAllCertsPolicy" -as [type]) {} else {
	        Add-Type "using System.Net;using System.Security.Cryptography.X509Certificates;public class TrustAllCertsPolicy : ICertificatePolicy {public bool CheckValidationResult(ServicePoint srvPoint, X509Certificate certificate, WebRequest request, int certificateProblem) {return true;}}"
	        [System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy
	}
}

$VMobj = (Get-VM -Name $VMname -ErrorAction SilentlyContinue)
if (!$VMobj) {
    Write-Host -ForegroundColor Red "The 'VMname' expression does not match any machine"
    Exit
} elseif ($VMobj.length -gt 1) {
    Write-Host -ForegroundColor Red "The 'VMname' expresion matches more than one machine:"
    foreach ($i in $VMobj) {
        Write-Host $i
    }
    Exit
}

Write-Host -ForegroundColor Cyan "Capturing changes on VM console for machine '$VMobj'"
Write-Host -ForegroundColor Cyan "Written by Ondrej Holecek <oholecek@fortinet.com>"

$lastHash = "000000000000000000000000"
$dots = 0

while ($true) {
    $startTime = Get-Date

    $VMobj = (Get-VM -Name $VMname)
    $VMid = $VMobj.ExtensionData.MoRef.Value
    $tmpName = [System.IO.Path]::GetTempFileName()
    
    if ($VMobj.PowerState -ne "PoweredOn") {
        Write-Host -ForegroundColor Red "VM is not running"
        Start-Sleep -Seconds 1
        continue
    }

	 $statusError = $false
    try {
			if ($PSVersionTable.OS -eq $NULL) {
        		Invoke-WebRequest -Uri https://$VMhost/screen?id=$VMid -Credential $Cred -OutFile $tmpName
			} else {
        		Invoke-WebRequest -Uri https://$VMhost/screen?id=$VMid -Credential $Cred -OutFile $tmpName -SkipCertificateCheck
			}
    } catch {
	 		$statusError = $true
    }

    if ($dots -eq 0) {
        Write-Host -NoNewline (Get-Date -f "yyyy-MM-dd HH:mm:ss") ": "
    }
	 if ($statusError) {
	 	  Write-Host -NoNewline "X"
	 } else {
	 	  Write-Host -NoNewline "."
	 }
    $dots += 1
    if ($dots % 10 -eq 0) { 
        Write-Host -NoNewline " " 
    }
    if ($dots -ge 60) { 
        Write-Host
        $dots = 0
    }
	 if ($statusError) { continue }

    $currentHash = (Get-FileHash -Path $tmpName -Algorithm MD5).Hash
        
    if ($lastHash -eq $currentHash) {
        Remove-Item -Path $tmpName
    } else {
        $fileName = (Join-Path -Path "$Directory" -ChildPath "$VMid-$(Get-Date -f yyyyMMdd-HHmmss.ffff).png")
        Move-Item -Path $tmpName -Destination $fileName
        Write-Host
        Write-Host "New unique screenshot saved as $fileName"
        $dots = 0
    }

    $lastHash = $currentHash

    $endTime = Get-Date
    $left = 990-(($endTime-$startTime).Milliseconds)
    if ($left -gt 0) { Start-Sleep -Milliseconds $left }
}

