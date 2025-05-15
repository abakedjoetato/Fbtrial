import sys
import traceback
import importlib.util

def load_module(module_name, file_path):
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print(f'Module {module_name} loaded successfully')
        return True
    except Exception as e:
        print(f'Error loading module {module_name}: {e}')
        traceback.print_exc(file=sys.stdout)
        return False

if __name__ == "__main__":
    load_module('help_fixed', 'cogs/help_fixed.py')