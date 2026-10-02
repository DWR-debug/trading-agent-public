from pathlib import Path

WORKFLOW = Path('.github/workflows/android-phone-fleet-worker.yml')

def _block(text: str, slot: str, next_slot: str | None) -> str:
    start = text.index(f'  phone_{slot}:\n')
    end = text.index(f'  phone_{next_slot}:\n', start) if next_slot else len(text)
    return text[start:end]

def test_phone_04_binds_to_phone_04_everywhere():
    text = WORKFLOW.read_text(encoding='utf-8')
    block = _block(text, '04', '05')
    assert 'runs-on: [self-hosted, linux, ARM64, samsung-phone-04]' in block
    assert 'PHONE_RESOURCE_ID: SAMSUNG-PHONE-04' in block
    assert 'PHONE_RUNNER_NAME: SAMSUNG-PHONE-04-TERMUX' in block
    assert 'android-phone/SAMSUNG-PHONE-04/runs' in block
    assert 'resource-id "SAMSUNG-PHONE-04"' in block
    assert 'android-phone-${{ github.run_id }}-SAMSUNG-PHONE-04' in block
    assert 'samsung-phone-03' not in block
    assert 'SAMSUNG-PHONE-03' not in block

def test_phone_05_binds_to_phone_05_everywhere():
    text = WORKFLOW.read_text(encoding='utf-8')
    block = _block(text, '05', None)
    assert 'runs-on: [self-hosted, linux, ARM64, samsung-phone-05]' in block
    assert 'PHONE_RESOURCE_ID: SAMSUNG-PHONE-05' in block
    assert 'PHONE_RUNNER_NAME: SAMSUNG-PHONE-05-TERMUX' in block
    assert 'android-phone/SAMSUNG-PHONE-05/runs' in block
    assert 'resource-id "SAMSUNG-PHONE-05"' in block
    assert 'android-phone-${{ github.run_id }}-SAMSUNG-PHONE-05' in block
    assert 'samsung-phone-03' not in block
    assert 'SAMSUNG-PHONE-03' not in block
