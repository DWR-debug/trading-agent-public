from automation.h06_sector_neutral_residual_momentum_performance import _weights

class Bar:
    def __init__(self,close): self.close=close

def _assets():
    sectors={
      "technology":("MU","ADBE","CRM"),
      "healthcare":("ABT","BMY","BAX"),
      "industrials":("PH","ROK","DOV"),
      "consumer_staples":("CPB","SJM","CAG"),
      "utilities":("EXC","SRE","CMS"),
    }
    out={}
    symbols=sum((list(v) for v in sectors.values()),[])
    for s in symbols:
        out[s]=[Bar(100.0),Bar(100.0)]
    # MU 20%, ADBE 10%, CRM 0%; residuals +10,0,-10
    out["MU"]=[Bar(100.0),Bar(120.0)]
    out["ADBE"]=[Bar(100.0),Bar(110.0)]
    out["CRM"]=[Bar(100.0),Bar(100.0)]
    # ABT 10%, BMY 5%, BAX 0%; residuals +7.5, +2.5, -2.5
    out["ABT"]=[Bar(100.0),Bar(110.0)]
    out["BMY"]=[Bar(100.0),Bar(105.0)]
    return out

def test_h06_residual_ranking_is_sector_neutral():
    assets=_assets()
    # Need 274 entries, with last points representing anchor/origin.
    result=_weights(assets,273)
    assert sum(result.values())==1.0
    assert result["MU"]==0.5
    assert result["ABT"]==0.5
    assert all(result[s]==0.0 for s in ("ADBE","CRM","BMY","BAX","PH","ROK","DOV","CPB","SJM","CAG","EXC","SRE","CMS"))
