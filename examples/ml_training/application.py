import burr.core.application
from burr.core import Action, Condition, State, default


class ProcessDataAction(Action):
    @property
    def reads(self) -> list[str]:
        return ["data_path"]

    def run(self, state: State) -> dict:
        pass

    @property
    def writes(self) -> list[str]:
        return ["training_data", "evaluation_data"]

    def update(self, result: dict, state: State) -> State:
        return state.update(training_data=result["training_data"])


class TrainModel(Action):
    @property
    def reads(self) -> list[str]:
        return ["training_data", "epochs"]

    def run(self, state: State) -> dict:
        pass

    @property
    def writes(self) -> list[str]:
        return ["models", "training_metrics", "epochs"]

    def update(self, result: dict, state: State) -> State:
        return state.update(
            epochs=result["epochs"],  # overwrite each epoch
        ).append(
            models=result["model"],  # append -- note this can get big if your model is big
            # so you'll want to overwrite but store the conditions, or log somewhere
            metrics=result["metrics"],  # append the metrics
        )


class ValidateModel(Action):
    @property
    def reads(self) -> list[str]:
        return ["models", "evaluation_data"]

    def run(self, state: State) -> dict:
        pass

    @property
    def writes(self) -> list[str]:
        return ["validation_metrics"]

    def update(self, result: dict, state: State) -> State:
        return state.append(validation_metrics=result["validation_metrics"])


class BestModel(Action):
    @property
    def reads(self) -> list[str]:
        return ["validation_metrics", "models"]

    def run(self, state: State) -> dict:
        pass

    @property
    def writes(self) -> list[str]:
        return ["best_model"]

    def update(self, result: dict, state: State) -> State:
        return state.update(best_model=result["best_model"])


def application(epochs: int) -> burr.core.application.Application:
    return (
        burr.core.ApplicationBuilder()
        .with_state(
            data_path="data.csv",
            epochs=10,
            training_data=None,
            evaluation_data=None,
            models=[],
            training_metrics=[],
            validation_metrics=[],
            best_model=None,
        )
        .with_actions(
            process_data=ProcessDataAction(),
            train_model=TrainModel(),
            validate_model=ValidateModel(),
            best_model=BestModel(),
        )
        .with_transitions(
            ("process_data", "train_model", default),
            ("train_model", "validate_model", default),
            ("validate_model", "best_model", Condition.expr(f"epochs>{epochs}")),
            ("validate_model", "train_model", default),
        )
        .with_entrypoint("process_data")
        .build()
    )


if __name__ == "__main__":
    app = application(100)  # doing good data science is up to you...
    # state, result = app.run(until=["result"])
    app.visualize(output_file_path="ml_training.png", include_conditions=True, view=True)
    # assert state["counter"] == 10
    # print(state["counter"])
