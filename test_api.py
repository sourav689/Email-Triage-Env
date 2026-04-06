import requests

BASE = 'https://hugdevp-email-triage-env.hf.space'

print('1. Health check...')
r = requests.get(f'{BASE}/health')
assert r.status_code == 200, f'FAILED: {r.status_code}'
print('   PASS:', r.json())

print('2. Reset easy...')
r = requests.post(f'{BASE}/reset', params={'task': 'easy'})
assert r.status_code == 200, f'FAILED: {r.status_code}'
data = r.json()
episode_id = data['episode_id']
assert data['observation']['total_emails'] == 3
print('   PASS: episode_id =', episode_id)

print('3. Step...')
r = requests.post(f'{BASE}/step', json={
    'episode_id': episode_id,
    'action_type': 'ignore',
    'priority': 'low',
    'email_id': data['observation']['email_id']
})
assert r.status_code == 200, f'FAILED: {r.status_code}'
step_data = r.json()
assert step_data['done'] == False
assert 'reward' in step_data
print('   PASS: reward =', step_data['reward'])

print('4. State...')
r = requests.get(f'{BASE}/state')
assert r.status_code == 200, f'FAILED: {r.status_code}'
state = r.json()
assert state['current_index'] == 1
print('   PASS: current_index =', state['current_index'])

print('5. Reset medium...')
r = requests.post(f'{BASE}/reset', params={'task': 'medium'})
assert r.status_code == 200, f'FAILED: {r.status_code}'
assert r.json()['observation']['total_emails'] == 5
print('   PASS')

print('6. Reset hard...')
r = requests.post(f'{BASE}/reset', params={'task': 'hard'})
assert r.status_code == 200, f'FAILED: {r.status_code}'
assert r.json()['observation']['total_emails'] == 10
print('   PASS')

print()
print('ALL CHECKS PASSED — safe to submit')