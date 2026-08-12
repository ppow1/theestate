$residentGatewayRuntimeRoot = "A:\EstateRuntime\host\estate-main\current"
$residentGatewayPythonPath = "A:\EstateRuntime\host\estate-main\current\src"

$script:EstateCoreServiceConfig = @{
    EstateRoot = "A:\theestate"
    PythonPath = "A:\theestate\src"
    ResidentGatewayRuntimeRoot = $residentGatewayRuntimeRoot
    ResidentGatewayPythonPath = $residentGatewayPythonPath
    PythonExe = "C:\Python314\python.exe"
    OpenWebUiExe = "A:\AI\OpenWebUI\.venv\Scripts\open-webui.exe"
    OpenWebUiWorkDir = "A:\AI\OpenWebUI"
    TextGenLauncher = "A:\AI\TextGen\textgen-4.9\textgen.bat"
    TextGenWorkDir = "A:\AI\TextGen\textgen-4.9"
    SillyTavernWorkDir = "A:\AI\SillyTavern"
    StateRoot = Join-Path $PSScriptRoot "state"

    Services = @{
        ollama = @{
            Id = "ollama"
            Name = "Ollama/provider"
            Ports = @(11434)
            HealthUrls = @(
                "http://127.0.0.1:11434/api/tags"
            )
            Command = "ollama"
            Arguments = @("serve")
            ExpectedPathFragments = @(
                "ollama",
                "cmd.exe"
            )
            ExpectedCommandFragments = @(
                "serve",
                "Start-Ollama.cmd"
            )
            Core = $true
        }

        resident_gateway = @{
            Id = "resident_gateway"
            Name = "Estate Resident Gateway"
            Ports = @(11435)
            HealthUrls = @(
                "http://127.0.0.1:11435/v1/models"
            )
            Command = "C:\Python314\python.exe"
            Arguments = @(
                "-m",
                "estate.cli.main",
                "resident-gateway",
                "start",
                "--host",
                "127.0.0.1",
                "--port",
                "11435"
            )
            WorkingDirectory = $residentGatewayRuntimeRoot
            Environment = @{
                PYTHONPATH = $residentGatewayPythonPath
            }
            RequiredPaths = @(
                "src",
                "src\estate",
                "src\estate\cli\main.py",
                "src\estate\core\resident_gateway.py"
            )
            ExpectedPathFragments = @(
                "python.exe",
                "cmd.exe"
            )
            ExpectedCommandFragments = @(
                "resident-gateway",
                "--port 11435",
                "Start-ResidentGateway.cmd"
            )
            Core = $true
        }

        open_webui = @{
            Id = "open_webui"
            Name = "Open WebUI"
            Ports = @(8080, 3000)
            HealthUrls = @(
                "http://127.0.0.1:8080/",
                "http://127.0.0.1:3000/"
            )
            Command = "A:\AI\OpenWebUI\.venv\Scripts\open-webui.exe"
            Arguments = @(
                "serve",
                "--host",
                "127.0.0.1",
                "--port",
                "8080"
            )
            WorkingDirectory = "A:\AI\OpenWebUI"
            Environment = @{
                DATA_DIR = "A:\AI\OpenWebUI\EstateCanonicalData"
            }
            ExpectedPathFragments = @(
                "open-webui.exe",
                "python.exe",
                "cmd.exe",
                "docker",
                "com.docker"
            )
            ExpectedCommandFragments = @(
                "open-webui",
                "--port 8080",
                "Start-OpenWebUI.cmd"
            )
            Core = $true
        }

        office = @{
            Id = "office"
            Name = "Office of the Steward"
            Ports = @(8765)
            HealthUrls = @(
                "http://127.0.0.1:8765/"
            )
            Command = "C:\Python314\python.exe"
            Arguments = @(
                "-m",
                "estate.cli.main",
                "steward-command-center",
                "--serve",
                "--host",
                "127.0.0.1",
                "--port",
                "8765"
            )
            WorkingDirectory = "A:\theestate"
            Environment = @{
                PYTHONPATH = "A:\theestate\src"
            }
            ExpectedPathFragments = @(
                "python.exe"
            )
            ExpectedCommandFragments = @(
                "steward-command-center",
                "--port 8765"
            )
            Core = $false
        }

        sillytavern = @{
            Id = "sillytavern"
            Name = "SillyTavern"
            Ports = @(8000)
            HealthUrls = @(
                "http://127.0.0.1:8000/"
            )
            Command = "C:\Program Files\nodejs\node.exe"
            Arguments = @(
                "server.js"
            )
            WorkingDirectory = "A:\AI\SillyTavern"
            ExpectedPathFragments = @(
                "node.exe"
            )
            ExpectedCommandFragments = @(
                "server.js",
                "SillyTavern"
            )
            Core = $false
        }

        textgen = @{
            Id = "textgen"
            Name = "TextGen"
            Ports = @(7860, 5000, 5005, 7861)
            HealthUrls = @(
                "http://127.0.0.1:5000/v1/models",
                "http://127.0.0.1:7860/"
            )
            Command = "A:\AI\TextGen\textgen-4.9\textgen.bat"
            Arguments = @(
                "--no-electron"
            )
            WorkingDirectory = "A:\AI\TextGen\textgen-4.9"
            ExpectedPathFragments = @(
                "textgen",
                "cmd.exe"
            )
            ExpectedCommandFragments = @(
                "textgen.bat",
                "--no-electron",
                "Start-TextGen.cmd"
            )
            Core = $false
        }

        comfyui = @{
            Id = "comfyui"
            Name = "ComfyUI"
            Ports = @(8188)
            HealthUrls = @(
                "http://127.0.0.1:8188/"
            )
            Command = "A:\AI\envs\comfyui_server_py311\Scripts\python.exe"
            Arguments = @(
                "A:\AI\ComfyUI\ComfyUI_Server\main.py",
                "--listen",
                "127.0.0.1",
                "--port",
                "8188",
                "--input-directory",
                "A:\AI\Input",
                "--output-directory",
                "A:\AI\Output"
            )
            WorkingDirectory = "A:\AI\ComfyUI\ComfyUI_Server"
            Environment = @{
                AI_HOME = "A:\AI"
                HF_HOME = "A:\AI\Cache\HuggingFace"
                HUGGINGFACE_HUB_CACHE = "A:\AI\Cache\HuggingFace\hub"
                TRANSFORMERS_CACHE = "A:\AI\Cache\Transformers"
                HF_DATASETS_CACHE = "A:\AI\Cache\Datasets"
                TORCH_HOME = "A:\AI\Cache\Torch"
                XDG_CACHE_HOME = "A:\AI\Cache\XDG"
                PIP_CACHE_DIR = "A:\AI\Temp\pip-cache"
                TEMP = "A:\AI\Temp\tmp"
                TMP = "A:\AI\Temp\tmp"
            }
            ExpectedPathFragments = @(
                "comfyui_server_py311",
                "python.exe",
                "cmd.exe"
            )
            ExpectedCommandFragments = @(
                "ComfyUI_Server\main.py",
                "--port 8188",
                "Start-ComfyUI.cmd"
            )
            Core = $false
        }
    }
}

function Get-EstateServiceConfig {
    return $script:EstateCoreServiceConfig
}
