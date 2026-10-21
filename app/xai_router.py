import json
from fastapi import APIRouter, Depends, HTTPException
from app.trace_security import require_trace_api_enabled
from xai.trace import TRACE_DIR

router = APIRouter(prefix='/api/v1/xai', tags=['xai'])

@router.get('/traces')
def list_traces(_: None = Depends(require_trace_api_enabled)):
    if not TRACE_DIR.exists():
        return {'count': 0, 'traces': []}
    traces = []
    for path in sorted(TRACE_DIR.glob('*.json'), key=lambda p: p.stat().st_mtime, reverse=True)[:100]:
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            traces.append({'trace_id': data.get('trace_id'), 'session_id': data.get('session_id'), 'started_at': data.get('started_at'), 'completed_at': data.get('completed_at'), 'intent': (data.get('router') or {}).get('intent'), 'risk_level': (data.get('policy') or {}).get('risk_level'), 'final_status': (data.get('final') or {}).get('status')})
        except (OSError, json.JSONDecodeError):
            continue
    return {'count': len(traces), 'traces': traces}

@router.get('/traces/{trace_id}')
def get_trace(trace_id: str, _: None = Depends(require_trace_api_enabled)):
    if not trace_id.replace('-', '').isalnum():
        raise HTTPException(status_code=400, detail='Invalid trace ID.')
    trace_root = TRACE_DIR.resolve()
    path = (trace_root / (trace_id + '.json')).resolve()
    if not path.is_relative_to(trace_root):
        raise HTTPException(status_code=400, detail='Invalid trace path.')
    if not path.is_file():
        raise HTTPException(status_code=404, detail='Trace not found.')
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail='Trace file is unreadable.') from exc
