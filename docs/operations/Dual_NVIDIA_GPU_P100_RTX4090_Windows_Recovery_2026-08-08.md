# Dual NVIDIA GPU Recovery: Tesla P100 + GeForce RTX 4090 on Windows

Status: Known-Good Operational Recovery Record
Date: 2026-08-08
Classification: Estate Internal
System: Gigabyte B550M DS3H AC, Windows x64
GPUs:
- NVIDIA Tesla P100-PCIE-16GB
- NVIDIA GeForce RTX 4090

## Purpose

This document records the full troubleshooting episode required to make a Tesla P100 and GeForce RTX 4090 operate simultaneously on the same Windows system.

The objective was never to make only one GPU work. The success condition was always:

- Tesla P100 operational.
- RTX 4090 operational.
- Both visible simultaneously to Windows.
- Both visible simultaneously to `nvidia-smi`.
- One coherent NVIDIA driver generation servicing both cards.

This record exists because the working configuration was non-obvious, several plausible approaches failed, and future driver updates can easily break the system again.

## Final Known-Good Configuration

The working configuration is:

- NVIDIA driver: 576.57
- Windows driver version: 32.0.15.7657
- Source package: CUDA Toolkit 12.9.1 installer
- Source installer filename: `cuda_12.9.1_576.57_windows.exe`
- Common display INF: `nv_dispui.inf`
- Windows published INF after installation: `oem3.inf`
- CUDA Toolkit installed: 12.9
- NVCC: 12.9.86
- P100 mode: TCC
- RTX 4090 mode: WDDM

Final Windows device state:

- NVIDIA Tesla P100-PCIE-16GB: `CM_PROB_NONE`
- NVIDIA GeForce RTX 4090: `CM_PROB_NONE`

Final `nvidia-smi` state:

- GPU 0: Tesla P100-PCIE-16GB, 16 GB, TCC
- GPU 1: NVIDIA GeForce RTX 4090, 24 GB, WDDM

Both devices were bound to the same driver version and the same published INF:

- P100 -> `oem3.inf` -> 32.0.15.7657
- RTX 4090 -> `oem3.inf` -> 32.0.15.7657

## Initial State

The system initially showed:

- Tesla P100 visible and working.
- RTX 4090 physically enumerated by Windows but in error state.
- `nvidia-smi` only showed the P100.
- P100 driver version: 582.78.
- RTX 4090 driver package present separately.

The 4090 error was identified as:

- `CM_PROB_FAILED_ADD`
- Windows Problem Code 31

The 4090 used service `nvlddmkm`, but failed to add successfully.

## CUDA Toolkit Installation

CUDA Toolkit 12.9 was installed successfully.

Verification:

`nvcc --version` returned:

- CUDA compilation tools, release 12.9
- V12.9.86

The toolkit executable was located at:

`C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.9\bin\nvcc.exe`

A PATH issue initially prevented `nvcc` from being found. The toolkit itself was present and valid; adding the CUDA `bin` directory and setting `CUDA_PATH` resolved the shell issue.

Important distinction:

The `CUDA Version` shown by `nvidia-smi` describes the maximum CUDA runtime level supported by the loaded driver. It is not the same thing as the installed CUDA Toolkit version.

## Early Driver Inventory

Windows Driver Store contained multiple NVIDIA display packages:

- `oem3.inf` -> 32.0.16.2002 at one stage, later 32.0.16.1088 / 610.88
- `oem10.inf` -> 32.0.15.8115
- `oem21.inf` -> 32.0.15.8278 / 582.78

The P100 was successfully bound to:

- `oem21.inf`
- 32.0.15.8278
- NVIDIA 582.78

The RTX 4090 was separately bound to a GeForce package and failed with Code 31.

## Failed Approach 1: Assume CUDA Toolkit Was the Problem

This was ruled out.

CUDA Toolkit 12.9 installed correctly and `nvcc` worked once PATH was corrected.

The failure was below CUDA, in the Windows NVIDIA display-driver / kernel-driver layer.

## Failed Approach 2: Assume the P100 Prevented the 4090 from Starting

The P100 was temporarily disabled as an A/B test.

Result:

- P100: disabled.
- RTX 4090: still `CM_PROB_FAILED_ADD`.
- NVML failed because no NVIDIA GPU had a successfully active driver.

Conclusion:

The P100 being enabled was not by itself the reason the 4090 failed.

## Failed Approach 3: Repair the 4090 with a Newer GeForce Driver Only

The stale/broken 4090 package was removed:

`pnputil /delete-driver oem3.inf /uninstall /force`

After removal and rescan, Windows showed:

- Tesla P100: OK
- Microsoft Basic Display Adapter: OK

The 4090 then received NVIDIA GeForce driver 610.88.

That successfully fixed the 4090:

- RTX 4090: `CM_PROB_NONE`
- `nvidia-smi` showed the 4090
- 24 GB VRAM visible
- WDDM active

However, the P100 then failed to start:

- Tesla P100: `CM_PROB_FAILED_START`

This was a critical result.

It demonstrated that fixing the 4090 with a newer GeForce branch did not satisfy the actual dual-GPU objective.

## Important A/B Observation

Two states were repeatedly observed:

### State A: R580 / 582.78 active

- P100: works
- RTX 4090: fails with `CM_PROB_FAILED_ADD`

### State B: GeForce 610.88 active

- RTX 4090: works
- P100: fails with `CM_PROB_FAILED_START`

This strongly suggested a driver-generation collision rather than a hardware fault.

## BIOS / PCIe Resource Investigation

The motherboard was identified as:

- Gigabyte Technology Co., Ltd.
- B550M DS3H AC
- BIOS version FA
- BIOS date 2023-04-25

Relevant BIOS settings were checked because multi-GPU systems can fail due to PCIe address-space allocation.

Settings considered:

- Above 4G Decoding
- Re-Size BAR Support
- CSM Support

Changing/confirming those settings did not resolve the dual-driver failure.

Conclusion:

PCIe resource allocation was not the primary cause in this case.

## Failed Approach 4: Match Data Center 582.78 with RTX Enterprise 582.78

A promising theory was to put both cards on the same R580 version by pairing:

- Data Center 582.78 for P100
- RTX Enterprise R580 U11 582.78 for RTX 4090

The RTX Enterprise installer was downloaded and extracted with 7-Zip.

Package:

`582.78-quadro-rtx-desktop-notebook-win10-win11-64bit-international-dch-whql.exe`

Its display INFs were searched for the 4090 hardware ID:

`DEV_2684`

Result:

- `DEV_2684` was not found.

Conclusion:

The RTX Enterprise 582.78 package did not support this GeForce RTX 4090 and was not installed.

This avoided another destructive driver change.

## Key Diagnostic Breakthrough: Inspect the CUDA 12.9.1 Bundled Driver

The installed CUDA Toolkit came from:

`C:\Users\wille\Downloads\cuda_12.9.1_576.57_windows.exe`

Rather than running the installer again, the executable was extracted with 7-Zip.

Extraction directory:

`C:\Users\wille\Downloads\CUDA-12.9.1-576.57-VERIFY`

All display INFs were searched for both device IDs.

### Tesla P100

Found in:

`Display.Driver\nv_dispui.inf`

Exact hardware line:

`%NVIDIA_DEV.15F8.118F.10DE% = Section029, PCI\VEN_10DE&DEV_15F8&SUBSYS_118F10DE`

This matched the exact P100 subsystem present in the machine.

### RTX 4090

Found in the same INF:

`Display.Driver\nv_dispui.inf`

Hardware line:

`%NVIDIA_DEV.2684% = Section080, PCI\VEN_10DE&DEV_2684`

### Same-INF Test

Both GPUs were present in the same signed INF:

`Display.Driver\nv_dispui.inf`

This was the decisive difference from the newer split packages.

The INF reported:

- Driver version: 32.0.15.7657
- Driver package version: 576.57
- Catalog: `NV_DISP.CAT`

The signed catalog file was present.

## Final Successful Transition

The system was moved from the competing newer packages to the common 576.57 package.

Safety checks were performed first:

- P100 exact subsystem support verified.
- RTX 4090 support verified.
- Driver version verified.
- NVIDIA catalog verified.

Then the competing packages were removed:

- GeForce 610.88 package
- P100 582.78 package

The single common INF from the CUDA 12.9.1 bundle was installed directly using `pnputil`.

Source INF:

`C:\Users\wille\Downloads\CUDA-12.9.1-576.57-VERIFY\Display.Driver\nv_dispui.inf`

After reboot, both devices came up successfully.

## Final Verification

Windows device state:

- Tesla P100-PCIE-16GB: OK / `CM_PROB_NONE`
- NVIDIA GeForce RTX 4090: OK / `CM_PROB_NONE`

Driver bindings:

- P100 -> `oem3.inf` -> 32.0.15.7657
- RTX 4090 -> `oem3.inf` -> 32.0.15.7657

`nvidia-smi -L`:

- GPU 0: Tesla P100-PCIE-16GB
- GPU 1: NVIDIA GeForce RTX 4090

`nvidia-smi`:

- Driver Version: 576.57
- CUDA Version: 12.9
- P100: TCC, 16 GB
- RTX 4090: WDDM, 24 GB

This satisfied the actual objective: both cards operating simultaneously.

## Root Cause

The practical root cause was incompatible or competing NVIDIA driver generations/packages on Windows.

The newer NVIDIA distribution model separated support across different package families:

- Data Center / Tesla package supported the P100.
- GeForce package supported the RTX 4090.
- RTX Enterprise package did not include the GeForce RTX 4090 hardware ID.

Installing separate newer generations resulted in whichever NVIDIA kernel driver generation became active servicing one card while the other failed.

The CUDA 12.9.1 bundled NVIDIA driver 576.57 was different: it shipped a signed common `nv_dispui.inf` that natively supported both the exact Tesla P100 and the RTX 4090.

Using that common package eliminated the split-driver conflict.

## Precautions

### Do not casually update the NVIDIA driver

The known-good version is 576.57.

A normal GeForce/NVIDIA App update may replace the shared 576.57 stack with a newer GeForce-only generation and break the P100 again.

Before any NVIDIA driver update:

1. Download or extract the candidate package first.
2. Search its display INFs for both:
   - `DEV_15F8`
   - `DEV_2684`
3. Prefer a package that contains both devices in one coherent driver distribution.
4. Verify the exact P100 subsystem when possible:
   - `DEV_15F8&SUBSYS_118F10DE`
5. Confirm signed catalog files are present.
6. Record the current working driver version and INF before changes.
7. Do not remove the known-good 576.57 package until the replacement package has been verified.

### Do not assume matching version numbers across NVIDIA product families imply compatibility

Data Center, GeForce, and RTX Enterprise packages may carry the same major branch or similar version numbers while shipping different INF coverage.

Always inspect the actual package.

### Do not infer installed CUDA Toolkit version from `nvidia-smi`

Use:

`nvcc --version`

for the installed Toolkit version.

### Preserve the source installer

Keep a copy of:

`cuda_12.9.1_576.57_windows.exe`

This is the known-good source package for the dual-GPU driver.

### Preserve the extracted known-good INF payload if practical

Known-good extracted path used during recovery:

`CUDA-12.9.1-576.57-VERIFY\Display.Driver\nv_dispui.inf`

The extracted package can be regenerated from the source installer with 7-Zip if necessary.

## Useful Diagnostic Commands

### Device state

```powershell
Get-PnpDevice -Class Display |
    Select-Object Status,FriendlyName,Problem,InstanceId |
    Format-Table -AutoSize
```

### NVIDIA visibility

```powershell
nvidia-smi -L
nvidia-smi
```

### Current driver binding

```powershell
Get-PnpDevice -Class Display |
    Where-Object { $_.FriendlyName -match "P100|4090" } |
    ForEach-Object {
        $dev = $_
        $inf = Get-PnpDeviceProperty -InstanceId $dev.InstanceId -KeyName DEVPKEY_Device_DriverInfPath -ErrorAction SilentlyContinue
        $ver = Get-PnpDeviceProperty -InstanceId $dev.InstanceId -KeyName DEVPKEY_Device_DriverVersion -ErrorAction SilentlyContinue
        [PSCustomObject]@{
            GPU = $dev.FriendlyName
            Status = $dev.Status
            Problem = $dev.Problem
            INF = $inf.Data
            Version = $ver.Data
        }
    } | Format-Table -AutoSize
```

### Search an extracted NVIDIA package for both GPUs

```powershell
$Infs = Get-ChildItem . -Recurse -Filter "*.inf"
$Infs | Select-String -Pattern "DEV_15F8|DEV_2684"
```

## Lessons Learned

1. The real objective must remain explicit throughout troubleshooting. A working 4090 alone was not success because the assignment was dual-GPU operation.
2. A newer driver is not automatically a better driver for heterogeneous NVIDIA hardware.
3. Windows can keep multiple NVIDIA packages in Driver Store while only one kernel-driver generation is effectively active.
4. Inspecting the actual INF files was more reliable than relying on product-family names or version numbers.
5. Extract-first, inspect-first is much safer than install-and-see.
6. The CUDA Toolkit installer can contain a broader NVIDIA display-driver package than the standalone product-family installers.
7. Matching both GPUs to one signed NVIDIA driver distribution resolved the conflict.
8. Preserve known-good infrastructure once it is found; do not allow automatic updates to silently destroy it.

## Recovery Summary

If this dual-GPU configuration breaks in the future, the fastest known recovery path is:

1. Confirm both devices are physically enumerated by Windows.
2. Confirm current driver bindings and error codes.
3. Do not troubleshoot CUDA Toolkit first unless `nvcc` itself is broken.
4. Avoid mixing separate modern GeForce and Data Center driver generations.
5. Use the CUDA 12.9.1 bundled NVIDIA 576.57 display driver.
6. Verify `nv_dispui.inf` contains both `DEV_15F8` and `DEV_2684`.
7. Install the common signed 576.57 package.
8. Reboot.
9. Verify both devices are `CM_PROB_NONE`.
10. Verify both appear in `nvidia-smi`.

## Known-Good Snapshot

```text
GPU 0: Tesla P100-PCIE-16GB
GPU 1: NVIDIA GeForce RTX 4090

Driver: NVIDIA 576.57
Windows driver version: 32.0.15.7657
Driver INF: nv_dispui.inf / oem3.inf

Source package:
cuda_12.9.1_576.57_windows.exe

CUDA Toolkit: 12.9
NVCC: 12.9.86

P100 mode: TCC
RTX 4090 mode: WDDM

P100: CM_PROB_NONE
RTX 4090: CM_PROB_NONE
```
