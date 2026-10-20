import pytest
from portra160_lab.stocks import all_stocks,supported_stock


def test_three_upstream_stocks():
    assert supported_stock('portra160')['film']=='kodak_portra_160'
    assert supported_stock('portra400')['film']=='kodak_portra_400'
    assert supported_stock('vision3_250d')['print']=='kodak_2383'


@pytest.mark.parametrize('name',['ektachrome400','trix400','aerocolor_iv'])
def test_missing_stock_fails_closed(name):
    assert all_stocks()[name]['status']=='upstream_profile_missing'
    with pytest.raises(ValueError,match='different stock must not be substituted'):
        supported_stock(name)
