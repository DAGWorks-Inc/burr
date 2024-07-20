import lancedb
import lancedb.context
import pyarrow as pa
import pyarrow.parquet
from lancedb.pydantic import LanceModel, Vector


def connection(lance_path: str = "./transcriptions") -> lancedb.DBConnection:
    """Connect to LanceDB"""
    return lancedb.connect(lance_path)


def transcriptions_table(connection: lancedb.DBConnection) -> lancedb.table.Table:
    """Create a LanceDB table with a registered embedding function.

    When inserting data, the `SourceField()` (`text` in this case) will automatically
    be embedded using a local sentence-transformers model.
    """
    registry = lancedb.embeddings.get_registry()
    model = registry.get("sentence-transformers").create(device="cuda")

    class Captions(LanceModel):
        file_name: str
        start: float
        end: float
        text: str = model.SourceField()
        uuid: str
        vector: Vector(model.ndims()) = model.VectorField()

    return connection.create_table("transcriptions", schema=Captions, exist_ok=True)


def transcriptions(data_path: str = "./tanscriptions.parquet") -> pa.Table:
    """Read the stored transcriptions from parquet."""
    return pyarrow.parquet.read_table(data_path)


def contextualized_transcriptions(
    transcriptions: pa.Table, window: int = 5, stride: int = 4
) -> pa.Table:
    """Use a LanceDB query to join individual transcriptions into larger contextual windows.
    Window and stride can help create large spans with/without overlaps, helping with retrieval.

    reference: https://lancedb.github.io/lancedb/python/python/#lancedb.context.contextualize
    """
    captions_df = transcriptions.to_pandas()
    context_builder = (
        lancedb.context.contextualize(captions_df)
        .groupby("file_name")
        .text_col("text")
        .window(window)
        .stride(stride)
    )
    # Contextualizer() doesn't have `.to_arrow()`
    return pa.Table.from_pandas(context_builder.to_pandas())


def insert_data(
    contextualized_transcriptions: pa.Table,
    transcriptions_table: lancedb.table.Table,
    update_table: bool = False,
) -> pa.Table:
    """LanceDB query to insert new data.

    If update_table is True, modify existing records.
    Else, simply insert new records.
    """
    if update_table:
        (
            transcriptions_table.merge_insert("uuid")
            .when_matched_update_all()
            .execute(contextualized_transcriptions)
        )

    (
        transcriptions_table.merge_insert("uuid")
        .when_not_matched_insert_all()
        .execute(contextualized_transcriptions)
    )
    return transcriptions_table.to_arrow()
