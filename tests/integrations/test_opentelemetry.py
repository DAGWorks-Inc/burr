import typing

import burr.integrations.opentelemetry as burr_otel


def test_instrument_specs_match_instruments_literal():
    assert set(typing.get_args(burr_otel.INSTRUMENTS)) == set(burr_otel.INSTRUMENTS_SPECS.keys())
