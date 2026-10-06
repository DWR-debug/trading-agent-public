from pathlib import Path
from automation import q219_options_source_breadth_gate as gate

def test_q219_breadth_gate_is_non_authorizing(tmp_path, monkeypatch):
    release={"id":289029018,"tag_name":"data-v1","assets":[{"name":"SPY_options.parquet"},{"name":"QQQ_options.parquet"},{"name":"IWM_options.parquet"},{"name":"SPY_underlying.parquet"}]}
    responses={
      gate.Q129_RELEASE:(200,'application/json',__import__('json').dumps(release).encode()),
      gate.ALT_STORE:(200,'text/html',b'gitignored 1.5 GB for 2 years ALPACA_API_KEY_ID ALPACA_API_SECRET_KEY'),
      gate.CBOE_ARCHIVE:(200,'text/html',b'Cboe Equity Option Volume Archive')}
    monkeypatch.setattr(gate,'fetch',lambda url:responses[url])
    monkeypatch.setattr(gate.Path,'read_text',lambda *a,**k: __import__('json').dumps({'broad_source_lead':{'status':'BREADTH_LEAD_REQUIRES_DIRECT_HTTP_VALIDATION'}}))
    result=gate.run(tmp_path/'r.json')
    assert result['q129_option_asset_count']==3
    assert result['q129_option_underlyings']==['IWM','QQQ','SPY']
    assert result['q129_is_broad_individual_equity_option_source'] is False
    assert result['piekstra_requires_alpaca_credentials'] is True
    assert result['cboe_is_quotes_iv_oi_source_proven'] is False
    assert result['performance_authorization'] is False
