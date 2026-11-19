import sys, json, requests
from pathlib import Path

BASE_URL   = sys.argv[1].rstrip('/') if len(sys.argv) > 1 else 'http://localhost:5000'
API        = f'{BASE_URL}/api/v1'
SCRIPT_DIR = Path(__file__).resolve().parent
SAMPLES    = SCRIPT_DIR / 'sample_images'

def ok(label, resp):
    try: body = resp.json()
    except Exception: body = {'raw': resp.text}
    if resp.status_code >= 400:
        print(f'  X {label} -- HTTP {resp.status_code}')
        print('   ', json.dumps(body)[:400])
        return None
    print(f'  OK {label}')
    return body

def get(path, **kw): return requests.get(f'{API}{path}', timeout=120, **kw)
def post(path, **kw): return requests.post(f'{API}{path}', timeout=300, **kw)

print('\n' + '='*60)
print('  UAV Construction Monitor -- Demo Project Seeder')
print('='*60)

print('\n[0] Checking server ...')
try:
    r = get('/health')
    if r.status_code != 200:
        print(f'  X Server not ready ({r.status_code}). Start Flask first.')
        sys.exit(1)
    print('  OK Server online')
except requests.exceptions.ConnectionError:
    print(f'  X Cannot connect to {BASE_URL}. Start Flask first.')
    sys.exit(1)

print('\n[1] Creating demonstration project ...')
r = post('/projects', json={
    'name':                 'UAV Monitoring -- Site Alpha',
    'description':          'Demonstration project for the Explainable Vision-Based UAV Construction Progress Monitoring System.',
    'location':             'Urban Construction Site, Block A',
    'project_type':         'Commercial Building',
    'status':               'active',
    'start_date':           '2026-01-01',
    'approximate_end_date': '2026-12-31',
    'project_manager':      'Dr. K. Sivakumar',
    'client':               'Alpha Developments Pvt. Ltd.',
    'contractor':           'Meridian Construction Group',
    'budget':               '4.5 Crore INR',
})
body = ok('Create project', r)
if not body: sys.exit(1)
project_id   = body['data']['project_id']
project_name = body['data']['name']
print(f'    ID: {project_id}')

print('\n[2] Verifying sample images ...')
expected = [
    'change_pair1_before.png', 'change_pair1_after.png',
    'change_pair2_before.png', 'change_pair2_after.png',
    'safety_sample_1.jpg',     'safety_sample_2.jpg',
    'safety_sample_3.jpg',     'safety_sample_4.jpg',
]
missing = [f for f in expected if not (SAMPLES / f).exists()]
if missing:
    print(f'  X Missing sample images: {missing}')
    print(f'    Expected in: {SAMPLES}')
    sys.exit(1)
print('  OK All 8 sample images found')

print('\n[3] Uploading sample images ...')
files = []
for f in expected:
    mime = 'image/png' if f.endswith('.png') else 'image/jpeg'
    files.append(('images', (f, open(SAMPLES / f, 'rb'), mime)))
r = post(f'/projects/{project_id}/upload', files=files)
body = ok('Upload 8 sample images', r)
if body:
    d = body['data']
    print(f'    Uploaded: {d.get("uploaded",0)}, Processed: {d.get("processed",0)}')

print('\n[4] Creating inspection ...')
r = post(f'/projects/{project_id}/inspections', json={
    'name':        'Initial Site Survey -- Q3 2026',
    'description': 'Comprehensive UAV drone survey covering structural progress, safety compliance, and change detection.',
    'date':        '2026-08-25',
    'weather':     'Clear, 28C, wind 12 km/h',
    'inspector':   'UAV Pilot Team Alpha',
})
body = ok('Create inspection', r)
if not body: sys.exit(1)
inspection_id = body['data']['inspection_id']
print(f'    Inspection ID: {inspection_id}')

print('\n[5] Uploading images to inspection ...')
files2 = []
for f in expected:
    mime = 'image/png' if f.endswith('.png') else 'image/jpeg'
    files2.append(('images', (f, open(SAMPLES / f, 'rb'), mime)))
r = post(f'/projects/{project_id}/inspections/{inspection_id}/upload', files=files2)
ok('Upload to inspection', r)

print('\n[6] Running full AI analysis pipeline (Modules 2-6) ...')
print('    This may take 1-3 minutes ...')
r = post(f'/projects/{project_id}/inspections/{inspection_id}/analyze', json={
    'planned_duration': 365, 'start_date': '2026-01-01',
    'limit': 8, 'w_change': 0.40, 'w_activity': 0.30, 'w_temporal': 0.20, 'w_quality': 0.10,
})
body = ok('Full AI analysis pipeline', r)
if body:
    stages = body.get('data', {}).get('stages', {})
    for sname, sdata in stages.items():
        print(f'    Stage [{sname}]: {sdata.get("status","?")}')

print('\n[7] Running 17-step comprehensive assessment ...')
r = post(f'/projects/{project_id}/full_assessment', json={'limit': 8, 'run_xai': True})
body = ok('Full assessment', r)
if body:
    data = body.get('data', {})
    prog = data.get('progress_analysis', {})
    qres = data.get('quantitative_results', {})
    print(f'    Progress score : {prog.get("actual_progress","--")}%')
    print(f'    Delay status   : {prog.get("delay_status","--")}')
    print(f'    Risk level     : {qres.get("risk_level","--")}')

print('\n[8] Computing health score ...')
r = get(f'/projects/{project_id}/health_score')
body = ok('Health score', r)
if body:
    h = body.get('data', {}).get('health', {})
    print(f'    Score: {h.get("score","--")} ({h.get("classification","--")})')

print('\n[9] Generating final inspection summary ...')
r = post(f'/projects/{project_id}/final_summary', json={'inspection_id': inspection_id})
body = ok('Final inspection summary', r)
if body:
    data = body.get('data', {})
    hs   = data.get('health_score', {})
    print(f'    Health: {hs.get("score","--")} ({hs.get("classification","--")})')
    for finding in data.get('key_findings', [])[:3]:
        print(f'      * {finding}')

print('\n[10] Verifying XAI query engine ...')
r = get(f'/projects/{project_id}/xai/query', params={'query': 'progress_status'})
body = ok('XAI query: progress_status', r)
if body:
    d = body.get('data', {})
    print(f'    Finding: {str(d.get("finding","--"))[:100]}...')
    print(f'    Confidence: {d.get("confidence","--")}')

print('\n[11] Verifying evaluation endpoints ...')
r = get('/evaluation/change_detection')
body = ok('Change detection eval (LEVIR+SYSU)', r)
if body:
    datasets = body.get('data', {}).get('datasets', {})
    for dname, ddata in datasets.items():
        iou = ddata.get('mean_iou')
        f1  = ddata.get('mean_f1')
        if iou is not None:
            print(f'    {dname}: IoU={iou:.4f}, F1={f1:.4f}')

r2 = get('/evaluation/detection')
body2 = ok('Detection dataset eval (Roboflow)', r2)
if body2:
    d2 = body2.get('data', {})
    print(f'    Roboflow: {d2.get("total_images","?")} images, {d2.get("total_detections","?")} detections')

print('\n' + '='*60)
print('  DEMO PROJECT SEEDED SUCCESSFULLY')
print(f'  Project ID   : {project_id}')
print(f'  Project Name : {project_name}')
print(f'  Dashboard    : {BASE_URL}')
print('='*60 + '\n')
