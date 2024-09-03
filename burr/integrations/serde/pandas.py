# try to import to serialize Pandas Objects
import hashlib
import os

import pandas as pd

from burr.core import serde


@serde.serialize.register(pd.DataFrame)
def serialize_pandas_df(value: pd.DataFrame, pandas_kwargs: dict, **kwargs) -> dict:
    """Custom serde for pandas dataframes.

    Saves the dataframe to a parquet file and returns the path to the file.
    Requires a `path` key in the `pandas_kwargs` dictionary.

    :param value: the pandas dataframe to serialize.
    :param pandas_kwargs: `path` key is required -- this is the base path to save the parquet file. As \
    well as any other kwargs to pass to the pandas to_parquet function.
    :param kwargs:
    :return:
    """
    hash_object = hashlib.sha256()
    hash_value = str(value.columns) + str(value.shape) + str(value.dtypes)
    hash_object.update(hash_value.encode())

    # Return the hexadecimal representation of the hash
    file_name = f"df_{hash_object.hexdigest()}.parquet"
    kwargs = pandas_kwargs.copy()
    base_path: str = kwargs.pop("path")
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    saved_to = os.path.join(base_path, file_name)
    value.to_parquet(path=saved_to, **kwargs)
    return {serde.KEY: "pandas.DataFrame", "path": saved_to}


@serde.deserializer.register("pandas.DataFrame")
def deserialize_pandas_df(value: dict, pandas_kwargs: dict, **kwargs) -> pd.DataFrame:
    """Custom deserializer for pandas dataframes.

    :param value: the dictionary to pull the path from to load the parquet file.
    :param pandas_kwargs: other args to pass to the pandas read_parquet function.
    :param kwargs:
    :return: pandas dataframe
    """
    kwargs = pandas_kwargs.copy()
    if "path" in kwargs:
        # remove this to not clash; we already have the full path.
        kwargs.pop("path")
    return pd.read_parquet(value["path"], **kwargs)
