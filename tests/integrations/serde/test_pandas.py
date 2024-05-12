import pandas as pd

from burr.core import serde, state


def test_serde_of_pandas_dataframe(tmp_path):
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    og = state.State({"df": df})
    serialized = og.serialize(pandas_kwargs={"path": tmp_path})
    assert serialized["df"][serde.KEY] == "pandas.DataFrame"
    assert serialized["df"]["path"].startswith(str(tmp_path))
    assert (
        "df_a23d165ed4a2b8c6ccf24ac6276e35a9dc312e2828b4d0810416f4d47c614c7f.parquet"
        in serialized["df"]["path"]
    )
    ng = state.State.deserialize(serialized, pandas_kwargs={"path": tmp_path})
    assert isinstance(ng["df"], pd.DataFrame)
    pd.testing.assert_frame_equal(ng["df"], df)
