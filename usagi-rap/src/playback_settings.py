"""The one user preference: audio seconds earned by each typing event."""
import json,math
DEFAULT_SECONDS=.3
def validate_seconds(value):
    try:seconds=float(value)
    except (ValueError,TypeError):raise ValueError('0.05~3초 사이 숫자를 입력해 주세요.') from None
    if not math.isfinite(seconds) or not .05<=seconds<=3:
        raise ValueError('0.05~3초 사이 숫자를 입력해 주세요.')
    return seconds
def load_seconds(path):
    try:return validate_seconds(json.loads(path.read_text('utf-8'))['seconds_per_input'])
    except (OSError,ValueError,TypeError,KeyError):return DEFAULT_SECONDS
def save_seconds(path,seconds):
    seconds=validate_seconds(seconds)
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps({'seconds_per_input':seconds},indent=2),'utf-8')
    temp.replace(path)
