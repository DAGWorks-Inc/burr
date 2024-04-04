# Simulations

This example is a WIP -- we're actively looking for contributors + ideas. See [this issue](https://github.com/DAGWorks-Inc/burr/issues/136) to track.

At a high level, simulations generally run over a set of time steps and maintain state. The user then manages the state, which becomes
the input to the next time step, as well as output data to analyze.

For instance:

### Time-series Forecast
A time-series forecast will execute a computation (say, feature-engineering + a model) at each step for which the user is predicting. The 
user will then store a history of data (predictions, raw data, etc...), and use that to pass into the next step in the simulation.

The merge into state + query from state capabilities can be complicated -- windowed operations, rolling averages, etc.. may all be useful,
and they may want to visualize simulations live (E.G. by tracking some metrics as it goes along). Burr is a natural way to persist this -- even
if it is just a few actions (`query_data`, `feature_engineer`, `forecast`), the persistence capabilities + hooks can allow
for logging to whatever live framework one wants to visualize, and centralizing the logic of reading from/writing to state.


### Portfolio Construction

This is a special case of time-series forecasting, in which one wants to simulate a financial portfolio. Actions might be:
- `query_data` - get data from state/load externally
- `prepare_data` - format to something you can make predictions on
- `forecast` - runs a model to do stock-price fore asting
- `construct_portfolio` - uses the forecast to construct a portfolio
- `evaluate_portfolio` - evaluates the portfolio

Each one of these could be a DAG using [Hamilton](https://github.com/dagworks-inc/hamilton), or running any custom code.

### Multi-agent simulation

See [Stanford Smallville](https://hai.stanford.edu/news/computational-agents-exhibit-believable-humanlike-behavior) for an example.
For multiple independent "agents", Burr could help model the way they interact. This could be multiplke Burr applications, applications called within
actions, or an action that loops over all "users". We are still figuring out the best way to model this, so reach out if you have ideas! 


Please comment at [this issue](https://github.com/DAGWorks-Inc/burr/issues/136) if you have any opinions on the above! We would love user-contributed examples.

