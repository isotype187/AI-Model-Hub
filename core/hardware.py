import psutil
import subprocess


def get_specs():
    specs = {
        'cpu': psutil.cpu_count(logical=True),
        'ram_gb': round(psutil.virtual_memory().total / (1024**3), 2),
        'gpu': 'unknown',
        'vram_mb': 0
    }

    try:
        out = subprocess.check_output('wmic path win32_VideoController get name,AdapterRAM', shell=True).decode()
        if 'AdapterRAM' in out:
            lines = out.splitlines()
            for l in lines:
                if 'AdapterRAM' in l or not l.strip():
                    continue
                parts = l.split()
                if len(parts) > 1:
                    specs['gpu'] = parts[0]
                    try:
                        specs['vram_mb'] = int(parts[-1]) / (1024 * 1024)
                    except:
                        pass
    except:
        pass

    return specs


def estimate_model_cost(model):
    ram = psutil.virtual_memory().total / (1024**3)

    base_cost = {
        'ollama': 4,
        'hf': 8,
        'gguf': 6
    }.get(model.get('type'), 5)

    score = ram / base_cost

    if score < 1:
        return "HEAVY"
    elif score < 2:
        return "MODERATE"
    return "LIGHT"
