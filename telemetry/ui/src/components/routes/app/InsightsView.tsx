import { Step } from '../../../api';

export const InsightsView = (props: { steps: Step[] }) => {
  // TODO: (1) ingest model costs from some static file.
  // TODO: (2) track costs on a per model basis.
  // TODO: (3) visualize / surface that.

  // Initialize a variable to hold the total sum
  let totalPromptTokens = 0;
  let totalCompletionTokens = 0;
  // const openaiPromptTokenCost = 500 / 1_000_000;
  // const openaiCompletionTokenCost = 1500 / 1_000_000;
  let totalLLMCalls = 0;

  // Iterate over each step
  props.steps.forEach((step) => {
    let hasPromptCall = false;
    // Iterate over each attribute in the step
    step.attributes.forEach((attribute) => {
      // Check if the attribute name ends with '_tokens'
      if (attribute.key.endsWith('prompt_tokens')) {
        hasPromptCall = true;
        // Add the attribute value to the total sum
        totalPromptTokens += attribute.value as number;
      } else if (attribute.key.endsWith('completion_tokens')) {
        totalCompletionTokens += attribute.value as number;
      }
    });
    if (hasPromptCall) {
      totalLLMCalls += 1;
    }
  });

  // Skip for now
  // const totalCost =
  //   (totalPromptTokens * openaiPromptTokenCost +
  //     totalCompletionTokens * openaiCompletionTokenCost) /
  //   100.0;

  if (totalLLMCalls > 0) {
    // Display the total sum
    // Skip cost for
    return (
      <div>
        <h2>Total Prompt Tokens: {totalPromptTokens}</h2>
        <h2>Total Completion Tokens: {totalCompletionTokens}</h2>
        {/*<h2>Total Cost: ${totalCost}</h2>*/}
        <h2>Total LLM Calls: {totalLLMCalls}</h2>
      </div>
    );
  } else {
    return (
      <div>
        <h2>No LLM calls found.</h2>
      </div>
    );
  }
};
