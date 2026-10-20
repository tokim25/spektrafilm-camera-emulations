from portra160_lab.stocks import all_stocks, supported_stock

def test_exact_user_priorities():
    want={
      'ektar100':('kodak_ektar_100','kodak_portra_endura'),
      'portra800':('kodak_portra_800','kodak_portra_endura'),
      'vision3_50d':('kodak_vision3_50d','kodak_2383'),
      'vision3_500t':('kodak_vision3_500t','kodak_2383'),
      'vision3_250d_2393':('kodak_vision3_250d','kodak_2393'),
    }
    for name,(film,print_name) in want.items():
        got=supported_stock(name)
        assert (got['film'],got['print'])==(film,print_name)

def test_missing_stocks_deferred_without_substitution():
    for key in ['ektachrome400','trix400','aerocolor_iv']:
        assert all_stocks()[key]['status']=='upstream_profile_missing'
