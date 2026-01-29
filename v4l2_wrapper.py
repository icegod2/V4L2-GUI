import subprocess
import re

def list_devices():
    """
    執行 v4l2-ctl --list-devices 並解析結果。
    回傳範例: [{'name': 'Integrated Camera', 'path': '/dev/video0'}, ...]
    """
    try:
        result = subprocess.check_output(['v4l2-ctl', '--list-devices'], text=True)
        devices = []
        lines = result.strip().split('\n')
        
        current_name = None
        for line in lines:
            if line.startswith('\t'):
                if current_name:
                    path = line.strip()
                    devices.append({'name': current_name, 'path': path})
                    current_name = None 
            elif line.strip():
                current_name = line.strip()
        return devices
    except Exception as e:
        print(f"Error listing devices: {e}")
        return []

def get_controls(device_path):
    """
    解析 v4l2-ctl -d <path> --list-ctrls-menus
    回傳 controls 列表，每個包含 name, type, min, max, step, default, value, flags, options(選單型才有)
    """
    try:
        result = subprocess.check_output(['v4l2-ctl', '-d', device_path, '--list-ctrls-menus'], text=True)
        controls = []
        lines = result.split('\n')
        
        current_ctrl = None
        
        # Regex for main control line
        # e.g., "brightness 0x00980900 (int)    : min=0 max=255 step=1 default=128 value=128"
        ctrl_re = re.compile(r'^\s*([a-zA-Z0-9_]+)\s+0x[0-9a-f]+\s+\(([a-z]+)\)\s*:\s*(.*)')
        # Regex for menu items
        # e.g., "1: 50 Hz"
        menu_re = re.compile(r'^\s*([0-9]+):\s*(.*)')

        for line in lines:
            if not line.strip():
                continue
                
            ctrl_match = ctrl_re.match(line)
            if ctrl_match:
                name, ctrl_type, attrs_str = ctrl_match.groups()
                attrs = {}
                # 解析 key=value 形式的屬性
                for pair in re.findall(r'([a-z]+)=([^ ]+)', attrs_str):
                    key, val = pair
                    try:
                        attrs[key] = int(val)
                    except ValueError:
                        attrs[key] = val
                
                current_ctrl = {
                    'name': name,
                    'type': ctrl_type,
                    'min': attrs.get('min'),
                    'max': attrs.get('max'),
                    'step': attrs.get('step'),
                    'default': attrs.get('default'),
                    'value': attrs.get('value'),
                    'flags': attrs.get('flags', ''),
                    'options': {} # For menu type
                }
                controls.append(current_ctrl)
            else:
                menu_match = menu_re.match(line)
                if menu_match and current_ctrl and current_ctrl['type'] == 'menu':
                    idx, label = menu_match.groups()
                    current_ctrl['options'][int(idx)] = label
                    
        return controls
    except Exception as e:
        print(f"Error getting controls for {device_path}: {e}")
        return []

def set_control(device_path, name, value):
    """
    設定攝影機參數
    """
    try:
        subprocess.run(['v4l2-ctl', '-d', device_path, '--set-ctrl', f'{name}={value}'], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error setting control {name} to {value} on {device_path}: {e}")
        return False

if __name__ == "__main__":
    devices = list_devices()
    if devices:
        path = devices[0]['path']
        print(f"Controls for {path}:")
        for ctrl in get_controls(path):
            print(f"- {ctrl['name']} ({ctrl['type']}): val={ctrl['value']} range={ctrl['min']}-{ctrl['max']}")
            if ctrl['options']:
                print(f"  Options: {ctrl['options']}")
