export interface ModelCost {
  [key: string]: {
    max_tokens?: number;
    max_input_tokens?: number;
    max_output_tokens?: number;
    input_cost_per_token?: number;
    output_cost_per_token?: number;
  };
}

export const modelCosts: ModelCost = {
  'gpt-4': {
    max_tokens: 4096,
    max_input_tokens: 8192,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-5,
    output_cost_per_token: 6e-5
  },
  'gpt-4o': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 5e-6,
    output_cost_per_token: 1.5e-5
  },
  'gpt-4o-mini': {
    max_tokens: 16384,
    max_input_tokens: 128000,
    max_output_tokens: 16384,
    input_cost_per_token: 1.5e-7,
    output_cost_per_token: 6e-7
  },
  'gpt-4o-mini-2024-07-18': {
    max_tokens: 16384,
    max_input_tokens: 128000,
    max_output_tokens: 16384,
    input_cost_per_token: 1.5e-7,
    output_cost_per_token: 6e-7
  },
  'o1-mini': {
    max_tokens: 65536,
    max_input_tokens: 128000,
    max_output_tokens: 65536,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 1.2e-5
  },
  'o1-mini-2024-09-12': {
    max_tokens: 65536,
    max_input_tokens: 128000,
    max_output_tokens: 65536,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 1.2e-5
  },
  'o1-preview': {
    max_tokens: 32768,
    max_input_tokens: 128000,
    max_output_tokens: 32768,
    input_cost_per_token: 1.5e-5,
    output_cost_per_token: 6e-5
  },
  'o1-preview-2024-09-12': {
    max_tokens: 32768,
    max_input_tokens: 128000,
    max_output_tokens: 32768,
    input_cost_per_token: 1.5e-5,
    output_cost_per_token: 6e-5
  },
  'chatgpt-4o-latest': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 5e-6,
    output_cost_per_token: 1.5e-5
  },
  'gpt-4o-2024-05-13': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 5e-6,
    output_cost_per_token: 1.5e-5
  },
  'gpt-4o-2024-08-06': {
    max_tokens: 16384,
    max_input_tokens: 128000,
    max_output_tokens: 16384,
    input_cost_per_token: 2.5e-6,
    output_cost_per_token: 1e-5
  },
  'gpt-4-turbo-preview': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 1e-5,
    output_cost_per_token: 3e-5
  },
  'gpt-4-0314': {
    max_tokens: 4096,
    max_input_tokens: 8192,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-5,
    output_cost_per_token: 6e-5
  },
  'gpt-4-0613': {
    max_tokens: 4096,
    max_input_tokens: 8192,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-5,
    output_cost_per_token: 6e-5
  },
  'gpt-4-32k': {
    max_tokens: 4096,
    max_input_tokens: 32768,
    max_output_tokens: 4096,
    input_cost_per_token: 6e-5,
    output_cost_per_token: 0.00012
  },
  'gpt-4-32k-0314': {
    max_tokens: 4096,
    max_input_tokens: 32768,
    max_output_tokens: 4096,
    input_cost_per_token: 6e-5,
    output_cost_per_token: 0.00012
  },
  'gpt-4-32k-0613': {
    max_tokens: 4096,
    max_input_tokens: 32768,
    max_output_tokens: 4096,
    input_cost_per_token: 6e-5,
    output_cost_per_token: 0.00012
  },
  'gpt-4-turbo': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 1e-5,
    output_cost_per_token: 3e-5
  },
  'gpt-4-turbo-2024-04-09': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 1e-5,
    output_cost_per_token: 3e-5
  },
  'gpt-4-1106-preview': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 1e-5,
    output_cost_per_token: 3e-5
  },
  'gpt-4-0125-preview': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 1e-5,
    output_cost_per_token: 3e-5
  },
  'gpt-4-vision-preview': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 1e-5,
    output_cost_per_token: 3e-5
  },
  'gpt-4-1106-vision-preview': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 1e-5,
    output_cost_per_token: 3e-5
  },
  'gpt-3.5-turbo': {
    max_tokens: 4097,
    max_input_tokens: 16385,
    max_output_tokens: 4096,
    input_cost_per_token: 1.5e-6,
    output_cost_per_token: 2e-6
  },
  'gpt-3.5-turbo-0301': {
    max_tokens: 4097,
    max_input_tokens: 4097,
    max_output_tokens: 4096,
    input_cost_per_token: 1.5e-6,
    output_cost_per_token: 2e-6
  },
  'gpt-3.5-turbo-0613': {
    max_tokens: 4097,
    max_input_tokens: 4097,
    max_output_tokens: 4096,
    input_cost_per_token: 1.5e-6,
    output_cost_per_token: 2e-6
  },
  'gpt-3.5-turbo-1106': {
    max_tokens: 16385,
    max_input_tokens: 16385,
    max_output_tokens: 4096,
    input_cost_per_token: 1e-6,
    output_cost_per_token: 2e-6
  },
  'gpt-3.5-turbo-0125': {
    max_tokens: 16385,
    max_input_tokens: 16385,
    max_output_tokens: 4096,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 1.5e-6
  },
  'gpt-3.5-turbo-16k': {
    max_tokens: 16385,
    max_input_tokens: 16385,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 4e-6
  },
  'gpt-3.5-turbo-16k-0613': {
    max_tokens: 16385,
    max_input_tokens: 16385,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 4e-6
  },
  'ft:gpt-3.5-turbo': {
    max_tokens: 4096,
    max_input_tokens: 16385,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 6e-6
  },
  'ft:gpt-3.5-turbo-0125': {
    max_tokens: 4096,
    max_input_tokens: 16385,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 6e-6
  },
  'ft:gpt-3.5-turbo-1106': {
    max_tokens: 4096,
    max_input_tokens: 16385,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 6e-6
  },
  'ft:gpt-3.5-turbo-0613': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 6e-6
  },
  'ft:gpt-4-0613': {
    max_tokens: 4096,
    max_input_tokens: 8192,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-5,
    output_cost_per_token: 6e-5
  },
  'ft:gpt-4o-2024-08-06': {
    max_tokens: 16384,
    max_input_tokens: 128000,
    max_output_tokens: 16384,
    input_cost_per_token: 3.75e-6,
    output_cost_per_token: 1.5e-5
  },
  'ft:gpt-4o-mini-2024-07-18': {
    max_tokens: 16384,
    max_input_tokens: 128000,
    max_output_tokens: 16384,
    input_cost_per_token: 3e-7,
    output_cost_per_token: 1.2e-6
  },
  'ft:davinci-002': {
    max_tokens: 16384,
    max_input_tokens: 16384,
    max_output_tokens: 4096,
    input_cost_per_token: 2e-6,
    output_cost_per_token: 2e-6
  },
  'ft:babbage-002': {
    max_tokens: 16384,
    max_input_tokens: 16384,
    max_output_tokens: 4096,
    input_cost_per_token: 4e-7,
    output_cost_per_token: 4e-7
  },
  'text-embedding-3-large': {
    max_tokens: 8191,
    max_input_tokens: 8191,
    input_cost_per_token: 1.3e-7,
    output_cost_per_token: 0.0
  },
  'text-embedding-3-small': {
    max_tokens: 8191,
    max_input_tokens: 8191,
    input_cost_per_token: 2e-8,
    output_cost_per_token: 0.0
  },
  'text-embedding-ada-002': {
    max_tokens: 8191,
    max_input_tokens: 8191,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 0.0
  },
  'text-embedding-ada-002-v2': {
    max_tokens: 8191,
    max_input_tokens: 8191,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 0.0
  },
  'text-moderation-stable': {
    max_tokens: 32768,
    max_input_tokens: 32768,
    max_output_tokens: 0,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'text-moderation-007': {
    max_tokens: 32768,
    max_input_tokens: 32768,
    max_output_tokens: 0,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'text-moderation-latest': {
    max_tokens: 32768,
    max_input_tokens: 32768,
    max_output_tokens: 0,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  '256-x-256/dall-e-2': {},
  '512-x-512/dall-e-2': {},
  '1024-x-1024/dall-e-2': {},
  'hd/1024-x-1792/dall-e-3': {},
  'hd/1792-x-1024/dall-e-3': {},
  'hd/1024-x-1024/dall-e-3': {},
  'standard/1024-x-1792/dall-e-3': {},
  'standard/1792-x-1024/dall-e-3': {},
  'standard/1024-x-1024/dall-e-3': {},
  'whisper-1': {},
  'tts-1': {},
  'tts-1-hd': {},
  'azure/tts-1': {},
  'azure/tts-1-hd': {},
  'azure/whisper-1': {},
  'azure/gpt-4o': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 5e-6,
    output_cost_per_token: 1.5e-5
  },
  'azure/gpt-4o-2024-08-06': {
    max_tokens: 16384,
    max_input_tokens: 128000,
    max_output_tokens: 16384,
    input_cost_per_token: 2.75e-6,
    output_cost_per_token: 1.1e-5
  },
  'azure/global-standard/gpt-4o-2024-08-06': {
    max_tokens: 16384,
    max_input_tokens: 128000,
    max_output_tokens: 16384,
    input_cost_per_token: 2.5e-6,
    output_cost_per_token: 1e-5
  },
  'azure/global-standard/gpt-4o-mini': {
    max_tokens: 16384,
    max_input_tokens: 128000,
    max_output_tokens: 16384,
    input_cost_per_token: 1.5e-7,
    output_cost_per_token: 6e-7
  },
  'azure/gpt-4o-mini': {
    max_tokens: 16384,
    max_input_tokens: 128000,
    max_output_tokens: 16384,
    input_cost_per_token: 1.65e-7,
    output_cost_per_token: 6.6e-7
  },
  'azure/gpt-4-turbo-2024-04-09': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 1e-5,
    output_cost_per_token: 3e-5
  },
  'azure/gpt-4-0125-preview': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 1e-5,
    output_cost_per_token: 3e-5
  },
  'azure/gpt-4-1106-preview': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 1e-5,
    output_cost_per_token: 3e-5
  },
  'azure/gpt-4-0613': {
    max_tokens: 4096,
    max_input_tokens: 8192,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-5,
    output_cost_per_token: 6e-5
  },
  'azure/gpt-4-32k-0613': {
    max_tokens: 4096,
    max_input_tokens: 32768,
    max_output_tokens: 4096,
    input_cost_per_token: 6e-5,
    output_cost_per_token: 0.00012
  },
  'azure/gpt-4-32k': {
    max_tokens: 4096,
    max_input_tokens: 32768,
    max_output_tokens: 4096,
    input_cost_per_token: 6e-5,
    output_cost_per_token: 0.00012
  },
  'azure/gpt-4': {
    max_tokens: 4096,
    max_input_tokens: 8192,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-5,
    output_cost_per_token: 6e-5
  },
  'azure/gpt-4-turbo': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 1e-5,
    output_cost_per_token: 3e-5
  },
  'azure/gpt-4-turbo-vision-preview': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 1e-5,
    output_cost_per_token: 3e-5
  },
  'azure/gpt-35-turbo-16k-0613': {
    max_tokens: 4096,
    max_input_tokens: 16385,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 4e-6
  },
  'azure/gpt-35-turbo-1106': {
    max_tokens: 4096,
    max_input_tokens: 16384,
    max_output_tokens: 4096,
    input_cost_per_token: 1e-6,
    output_cost_per_token: 2e-6
  },
  'azure/gpt-35-turbo-0613': {
    max_tokens: 4097,
    max_input_tokens: 4097,
    max_output_tokens: 4096,
    input_cost_per_token: 1.5e-6,
    output_cost_per_token: 2e-6
  },
  'azure/gpt-35-turbo-0301': {
    max_tokens: 4097,
    max_input_tokens: 4097,
    max_output_tokens: 4096,
    input_cost_per_token: 2e-7,
    output_cost_per_token: 2e-6
  },
  'azure/gpt-35-turbo-0125': {
    max_tokens: 4096,
    max_input_tokens: 16384,
    max_output_tokens: 4096,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 1.5e-6
  },
  'azure/gpt-35-turbo-16k': {
    max_tokens: 4096,
    max_input_tokens: 16385,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 4e-6
  },
  'azure/gpt-35-turbo': {
    max_tokens: 4096,
    max_input_tokens: 4097,
    max_output_tokens: 4096,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 1.5e-6
  },
  'azure/gpt-3.5-turbo-instruct-0914': {
    max_tokens: 4097,
    max_input_tokens: 4097,
    input_cost_per_token: 1.5e-6,
    output_cost_per_token: 2e-6
  },
  'azure/gpt-35-turbo-instruct': {
    max_tokens: 4097,
    max_input_tokens: 4097,
    input_cost_per_token: 1.5e-6,
    output_cost_per_token: 2e-6
  },
  'azure/gpt-35-turbo-instruct-0914': {
    max_tokens: 4097,
    max_input_tokens: 4097,
    input_cost_per_token: 1.5e-6,
    output_cost_per_token: 2e-6
  },
  'azure/mistral-large-latest': {
    max_tokens: 32000,
    max_input_tokens: 32000,
    input_cost_per_token: 8e-6,
    output_cost_per_token: 2.4e-5
  },
  'azure/mistral-large-2402': {
    max_tokens: 32000,
    max_input_tokens: 32000,
    input_cost_per_token: 8e-6,
    output_cost_per_token: 2.4e-5
  },
  'azure/command-r-plus': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 1.5e-5
  },
  'azure/ada': {
    max_tokens: 8191,
    max_input_tokens: 8191,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 0.0
  },
  'azure/text-embedding-ada-002': {
    max_tokens: 8191,
    max_input_tokens: 8191,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 0.0
  },
  'azure/text-embedding-3-large': {
    max_tokens: 8191,
    max_input_tokens: 8191,
    input_cost_per_token: 1.3e-7,
    output_cost_per_token: 0.0
  },
  'azure/text-embedding-3-small': {
    max_tokens: 8191,
    max_input_tokens: 8191,
    input_cost_per_token: 2e-8,
    output_cost_per_token: 0.0
  },
  'azure/standard/1024-x-1024/dall-e-3': { output_cost_per_token: 0.0 },
  'azure/hd/1024-x-1024/dall-e-3': { output_cost_per_token: 0.0 },
  'azure/standard/1024-x-1792/dall-e-3': { output_cost_per_token: 0.0 },
  'azure/standard/1792-x-1024/dall-e-3': { output_cost_per_token: 0.0 },
  'azure/hd/1024-x-1792/dall-e-3': { output_cost_per_token: 0.0 },
  'azure/hd/1792-x-1024/dall-e-3': { output_cost_per_token: 0.0 },
  'azure/standard/1024-x-1024/dall-e-2': { output_cost_per_token: 0.0 },
  'azure_ai/jamba-instruct': {
    max_tokens: 4096,
    max_input_tokens: 70000,
    max_output_tokens: 4096,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 7e-7
  },
  'azure_ai/mistral-large': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 4e-6,
    output_cost_per_token: 1.2e-5
  },
  'azure_ai/mistral-small': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 1e-6,
    output_cost_per_token: 3e-6
  },
  'azure_ai/Meta-Llama-3-70B-Instruct': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 1.1e-6,
    output_cost_per_token: 3.7e-7
  },
  'azure_ai/Meta-Llama-31-8B-Instruct': {
    max_tokens: 128000,
    max_input_tokens: 128000,
    max_output_tokens: 128000,
    input_cost_per_token: 3e-7,
    output_cost_per_token: 6.1e-7
  },
  'azure_ai/Meta-Llama-31-70B-Instruct': {
    max_tokens: 128000,
    max_input_tokens: 128000,
    max_output_tokens: 128000,
    input_cost_per_token: 2.68e-6,
    output_cost_per_token: 3.54e-6
  },
  'azure_ai/Meta-Llama-31-405B-Instruct': {
    max_tokens: 128000,
    max_input_tokens: 128000,
    max_output_tokens: 128000,
    input_cost_per_token: 5.33e-6,
    output_cost_per_token: 1.6e-5
  },
  'azure_ai/cohere-rerank-v3-multilingual': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'azure_ai/cohere-rerank-v3-english': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'azure_ai/Cohere-embed-v3-english': {
    max_tokens: 512,
    max_input_tokens: 512,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 0.0
  },
  'azure_ai/Cohere-embed-v3-multilingual': {
    max_tokens: 512,
    max_input_tokens: 512,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 0.0
  },
  'babbage-002': {
    max_tokens: 16384,
    max_input_tokens: 16384,
    max_output_tokens: 4096,
    input_cost_per_token: 4e-7,
    output_cost_per_token: 4e-7
  },
  'davinci-002': {
    max_tokens: 16384,
    max_input_tokens: 16384,
    max_output_tokens: 4096,
    input_cost_per_token: 2e-6,
    output_cost_per_token: 2e-6
  },
  'gpt-3.5-turbo-instruct': {
    max_tokens: 4096,
    max_input_tokens: 8192,
    max_output_tokens: 4096,
    input_cost_per_token: 1.5e-6,
    output_cost_per_token: 2e-6
  },
  'gpt-3.5-turbo-instruct-0914': {
    max_tokens: 4097,
    max_input_tokens: 8192,
    max_output_tokens: 4097,
    input_cost_per_token: 1.5e-6,
    output_cost_per_token: 2e-6
  },
  'claude-instant-1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 1.63e-6,
    output_cost_per_token: 5.51e-6
  },
  'mistral/mistral-tiny': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 2.5e-7,
    output_cost_per_token: 2.5e-7
  },
  'mistral/mistral-small': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 1e-6,
    output_cost_per_token: 3e-6
  },
  'mistral/mistral-small-latest': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 1e-6,
    output_cost_per_token: 3e-6
  },
  'mistral/mistral-medium': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 2.7e-6,
    output_cost_per_token: 8.1e-6
  },
  'mistral/mistral-medium-latest': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 2.7e-6,
    output_cost_per_token: 8.1e-6
  },
  'mistral/mistral-medium-2312': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 2.7e-6,
    output_cost_per_token: 8.1e-6
  },
  'mistral/mistral-large-latest': {
    max_tokens: 128000,
    max_input_tokens: 128000,
    max_output_tokens: 128000,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 9e-6
  },
  'mistral/mistral-large-2402': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 4e-6,
    output_cost_per_token: 1.2e-5
  },
  'mistral/mistral-large-2407': {
    max_tokens: 128000,
    max_input_tokens: 128000,
    max_output_tokens: 128000,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 9e-6
  },
  'mistral/pixtral-12b-2409': {
    max_tokens: 128000,
    max_input_tokens: 128000,
    max_output_tokens: 128000,
    input_cost_per_token: 1.5e-7,
    output_cost_per_token: 1.5e-7
  },
  'mistral/open-mistral-7b': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 2.5e-7,
    output_cost_per_token: 2.5e-7
  },
  'mistral/open-mixtral-8x7b': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 7e-7,
    output_cost_per_token: 7e-7
  },
  'mistral/open-mixtral-8x22b': {
    max_tokens: 8191,
    max_input_tokens: 64000,
    max_output_tokens: 8191,
    input_cost_per_token: 2e-6,
    output_cost_per_token: 6e-6
  },
  'mistral/codestral-latest': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 1e-6,
    output_cost_per_token: 3e-6
  },
  'mistral/codestral-2405': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 1e-6,
    output_cost_per_token: 3e-6
  },
  'mistral/open-mistral-nemo': {
    max_tokens: 128000,
    max_input_tokens: 128000,
    max_output_tokens: 128000,
    input_cost_per_token: 3e-7,
    output_cost_per_token: 3e-7
  },
  'mistral/open-mistral-nemo-2407': {
    max_tokens: 128000,
    max_input_tokens: 128000,
    max_output_tokens: 128000,
    input_cost_per_token: 3e-7,
    output_cost_per_token: 3e-7
  },
  'mistral/open-codestral-mamba': {
    max_tokens: 256000,
    max_input_tokens: 256000,
    max_output_tokens: 256000,
    input_cost_per_token: 2.5e-7,
    output_cost_per_token: 2.5e-7
  },
  'mistral/codestral-mamba-latest': {
    max_tokens: 256000,
    max_input_tokens: 256000,
    max_output_tokens: 256000,
    input_cost_per_token: 2.5e-7,
    output_cost_per_token: 2.5e-7
  },
  'mistral/mistral-embed': { max_tokens: 8192, max_input_tokens: 8192, input_cost_per_token: 1e-7 },
  'deepseek-chat': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 1.4e-7,
    output_cost_per_token: 2.8e-7
  },
  'codestral/codestral-latest': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'codestral/codestral-2405': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'text-completion-codestral/codestral-latest': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'text-completion-codestral/codestral-2405': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'deepseek-coder': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 1.4e-7,
    output_cost_per_token: 2.8e-7
  },
  'groq/llama2-70b-4096': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 7e-7,
    output_cost_per_token: 8e-7
  },
  'groq/llama3-8b-8192': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 5e-8,
    output_cost_per_token: 8e-8
  },
  'groq/llama3-70b-8192': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 5.9e-7,
    output_cost_per_token: 7.9e-7
  },
  'groq/llama-3.1-8b-instant': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 5.9e-7,
    output_cost_per_token: 7.9e-7
  },
  'groq/llama-3.1-70b-versatile': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 5.9e-7,
    output_cost_per_token: 7.9e-7
  },
  'groq/llama-3.1-405b-reasoning': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 5.9e-7,
    output_cost_per_token: 7.9e-7
  },
  'groq/mixtral-8x7b-32768': {
    max_tokens: 32768,
    max_input_tokens: 32768,
    max_output_tokens: 32768,
    input_cost_per_token: 2.4e-7,
    output_cost_per_token: 2.4e-7
  },
  'groq/gemma-7b-it': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 7e-8,
    output_cost_per_token: 7e-8
  },
  'groq/gemma2-9b-it': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 2e-7,
    output_cost_per_token: 2e-7
  },
  'groq/llama3-groq-70b-8192-tool-use-preview': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 8.9e-7,
    output_cost_per_token: 8.9e-7
  },
  'groq/llama3-groq-8b-8192-tool-use-preview': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 1.9e-7,
    output_cost_per_token: 1.9e-7
  },
  'cerebras/llama3.1-8b': {
    max_tokens: 128000,
    max_input_tokens: 128000,
    max_output_tokens: 128000,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 1e-7
  },
  'cerebras/llama3.1-70b': {
    max_tokens: 128000,
    max_input_tokens: 128000,
    max_output_tokens: 128000,
    input_cost_per_token: 6e-7,
    output_cost_per_token: 6e-7
  },
  'friendliai/mixtral-8x7b-instruct-v0-1': {
    max_tokens: 32768,
    max_input_tokens: 32768,
    max_output_tokens: 32768,
    input_cost_per_token: 4e-7,
    output_cost_per_token: 4e-7
  },
  'friendliai/meta-llama-3-8b-instruct': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 1e-7
  },
  'friendliai/meta-llama-3-70b-instruct': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 8e-7,
    output_cost_per_token: 8e-7
  },
  'claude-instant-1.2': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 1.63e-7,
    output_cost_per_token: 5.51e-7
  },
  'claude-2': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 8e-6,
    output_cost_per_token: 2.4e-5
  },
  'claude-2.1': {
    max_tokens: 8191,
    max_input_tokens: 200000,
    max_output_tokens: 8191,
    input_cost_per_token: 8e-6,
    output_cost_per_token: 2.4e-5
  },
  'claude-3-haiku-20240307': {
    max_tokens: 4096,
    max_input_tokens: 200000,
    max_output_tokens: 4096,
    input_cost_per_token: 2.5e-7,
    output_cost_per_token: 1.25e-6
  },
  'claude-3-opus-20240229': {
    max_tokens: 4096,
    max_input_tokens: 200000,
    max_output_tokens: 4096,
    input_cost_per_token: 1.5e-5,
    output_cost_per_token: 7.5e-5
  },
  'claude-3-sonnet-20240229': {
    max_tokens: 4096,
    max_input_tokens: 200000,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 1.5e-5
  },
  'claude-3-5-sonnet-20240620': {
    max_tokens: 8192,
    max_input_tokens: 200000,
    max_output_tokens: 8192,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 1.5e-5
  },
  'text-bison': { max_tokens: 2048, max_input_tokens: 8192, max_output_tokens: 2048 },
  'text-bison@001': { max_tokens: 1024, max_input_tokens: 8192, max_output_tokens: 1024 },
  'text-bison@002': { max_tokens: 1024, max_input_tokens: 8192, max_output_tokens: 1024 },
  'text-bison32k': {
    max_tokens: 1024,
    max_input_tokens: 8192,
    max_output_tokens: 1024,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'text-bison32k@002': {
    max_tokens: 1024,
    max_input_tokens: 8192,
    max_output_tokens: 1024,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'text-unicorn': {
    max_tokens: 1024,
    max_input_tokens: 8192,
    max_output_tokens: 1024,
    input_cost_per_token: 1e-5,
    output_cost_per_token: 2.8e-5
  },
  'text-unicorn@001': {
    max_tokens: 1024,
    max_input_tokens: 8192,
    max_output_tokens: 1024,
    input_cost_per_token: 1e-5,
    output_cost_per_token: 2.8e-5
  },
  'chat-bison': {
    max_tokens: 4096,
    max_input_tokens: 8192,
    max_output_tokens: 4096,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'chat-bison@001': {
    max_tokens: 4096,
    max_input_tokens: 8192,
    max_output_tokens: 4096,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'chat-bison@002': {
    max_tokens: 4096,
    max_input_tokens: 8192,
    max_output_tokens: 4096,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'chat-bison-32k': {
    max_tokens: 8192,
    max_input_tokens: 32000,
    max_output_tokens: 8192,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'chat-bison-32k@002': {
    max_tokens: 8192,
    max_input_tokens: 32000,
    max_output_tokens: 8192,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'code-bison': {
    max_tokens: 1024,
    max_input_tokens: 6144,
    max_output_tokens: 1024,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'code-bison@001': {
    max_tokens: 1024,
    max_input_tokens: 6144,
    max_output_tokens: 1024,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'code-bison@002': {
    max_tokens: 1024,
    max_input_tokens: 6144,
    max_output_tokens: 1024,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'code-bison32k': {
    max_tokens: 1024,
    max_input_tokens: 6144,
    max_output_tokens: 1024,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'code-bison-32k@002': {
    max_tokens: 1024,
    max_input_tokens: 6144,
    max_output_tokens: 1024,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'code-gecko@001': {
    max_tokens: 64,
    max_input_tokens: 2048,
    max_output_tokens: 64,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'code-gecko@002': {
    max_tokens: 64,
    max_input_tokens: 2048,
    max_output_tokens: 64,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'code-gecko': {
    max_tokens: 64,
    max_input_tokens: 2048,
    max_output_tokens: 64,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'code-gecko-latest': {
    max_tokens: 64,
    max_input_tokens: 2048,
    max_output_tokens: 64,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'codechat-bison@latest': {
    max_tokens: 1024,
    max_input_tokens: 6144,
    max_output_tokens: 1024,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'codechat-bison': {
    max_tokens: 1024,
    max_input_tokens: 6144,
    max_output_tokens: 1024,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'codechat-bison@001': {
    max_tokens: 1024,
    max_input_tokens: 6144,
    max_output_tokens: 1024,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'codechat-bison@002': {
    max_tokens: 1024,
    max_input_tokens: 6144,
    max_output_tokens: 1024,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'codechat-bison-32k': {
    max_tokens: 8192,
    max_input_tokens: 32000,
    max_output_tokens: 8192,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'codechat-bison-32k@002': {
    max_tokens: 8192,
    max_input_tokens: 32000,
    max_output_tokens: 8192,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'gemini-pro': {
    max_tokens: 8192,
    max_input_tokens: 32760,
    max_output_tokens: 8192,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 1.5e-6
  },
  'gemini-1.0-pro': {
    max_tokens: 8192,
    max_input_tokens: 32760,
    max_output_tokens: 8192,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 1.5e-6
  },
  'gemini-1.0-pro-001': {
    max_tokens: 8192,
    max_input_tokens: 32760,
    max_output_tokens: 8192,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 1.5e-6
  },
  'gemini-1.0-ultra': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 2048,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 1.5e-6
  },
  'gemini-1.0-ultra-001': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 2048,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 1.5e-6
  },
  'gemini-1.0-pro-002': {
    max_tokens: 8192,
    max_input_tokens: 32760,
    max_output_tokens: 8192,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 1.5e-6
  },
  'gemini-1.5-pro': {
    max_tokens: 8192,
    max_input_tokens: 2097152,
    max_output_tokens: 8192,
    input_cost_per_token: 5e-6,
    output_cost_per_token: 1.5e-5
  },
  'gemini-1.5-pro-002': {
    max_tokens: 8192,
    max_input_tokens: 2097152,
    max_output_tokens: 8192,
    input_cost_per_token: 5e-6,
    output_cost_per_token: 1.5e-5
  },
  'gemini-1.5-pro-001': {
    max_tokens: 8192,
    max_input_tokens: 1000000,
    max_output_tokens: 8192,
    input_cost_per_token: 5e-6,
    output_cost_per_token: 1.5e-5
  },
  'gemini-1.5-pro-preview-0514': {
    max_tokens: 8192,
    max_input_tokens: 1000000,
    max_output_tokens: 8192,
    input_cost_per_token: 5e-6,
    output_cost_per_token: 1.5e-5
  },
  'gemini-1.5-pro-preview-0215': {
    max_tokens: 8192,
    max_input_tokens: 1000000,
    max_output_tokens: 8192,
    input_cost_per_token: 5e-6,
    output_cost_per_token: 1.5e-5
  },
  'gemini-1.5-pro-preview-0409': {
    max_tokens: 8192,
    max_input_tokens: 1000000,
    max_output_tokens: 8192,
    input_cost_per_token: 5e-6,
    output_cost_per_token: 1.5e-5
  },
  'gemini-1.5-flash': {
    max_tokens: 8192,
    max_input_tokens: 1000000,
    max_output_tokens: 8192,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 1.5e-6
  },
  'gemini-1.5-flash-exp-0827': {
    max_tokens: 8192,
    max_input_tokens: 1000000,
    max_output_tokens: 8192,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 1.5e-6
  },
  'gemini-1.5-flash-002': {
    max_tokens: 8192,
    max_input_tokens: 1048576,
    max_output_tokens: 8192,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 1.5e-6
  },
  'gemini-1.5-flash-001': {
    max_tokens: 8192,
    max_input_tokens: 1000000,
    max_output_tokens: 8192,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 1.5e-6
  },
  'gemini-1.5-flash-preview-0514': {
    max_tokens: 8192,
    max_input_tokens: 1000000,
    max_output_tokens: 8192,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 1.5e-6
  },
  'gemini-pro-experimental': {
    max_tokens: 8192,
    max_input_tokens: 1000000,
    max_output_tokens: 8192,
    input_cost_per_token: 0,
    output_cost_per_token: 0
  },
  'gemini-pro-flash': {
    max_tokens: 8192,
    max_input_tokens: 1000000,
    max_output_tokens: 8192,
    input_cost_per_token: 0,
    output_cost_per_token: 0
  },
  'gemini-pro-vision': {
    max_tokens: 2048,
    max_input_tokens: 16384,
    max_output_tokens: 2048,
    input_cost_per_token: 2.5e-7,
    output_cost_per_token: 5e-7
  },
  'gemini-1.0-pro-vision': {
    max_tokens: 2048,
    max_input_tokens: 16384,
    max_output_tokens: 2048,
    input_cost_per_token: 2.5e-7,
    output_cost_per_token: 5e-7
  },
  'gemini-1.0-pro-vision-001': {
    max_tokens: 2048,
    max_input_tokens: 16384,
    max_output_tokens: 2048,
    input_cost_per_token: 2.5e-7,
    output_cost_per_token: 5e-7
  },
  'medlm-medium': { max_tokens: 8192, max_input_tokens: 32768, max_output_tokens: 8192 },
  'medlm-large': { max_tokens: 1024, max_input_tokens: 8192, max_output_tokens: 1024 },
  'vertex_ai/claude-3-sonnet@20240229': {
    max_tokens: 4096,
    max_input_tokens: 200000,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 1.5e-5
  },
  'vertex_ai/claude-3-5-sonnet@20240620': {
    max_tokens: 8192,
    max_input_tokens: 200000,
    max_output_tokens: 8192,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 1.5e-5
  },
  'vertex_ai/claude-3-haiku@20240307': {
    max_tokens: 4096,
    max_input_tokens: 200000,
    max_output_tokens: 4096,
    input_cost_per_token: 2.5e-7,
    output_cost_per_token: 1.25e-6
  },
  'vertex_ai/claude-3-opus@20240229': {
    max_tokens: 4096,
    max_input_tokens: 200000,
    max_output_tokens: 4096,
    input_cost_per_token: 1.5e-5,
    output_cost_per_token: 7.5e-5
  },
  'vertex_ai/meta/llama3-405b-instruct-maas': {
    max_tokens: 32000,
    max_input_tokens: 32000,
    max_output_tokens: 32000,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'vertex_ai/meta/llama3-70b-instruct-maas': {
    max_tokens: 32000,
    max_input_tokens: 32000,
    max_output_tokens: 32000,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'vertex_ai/meta/llama3-8b-instruct-maas': {
    max_tokens: 32000,
    max_input_tokens: 32000,
    max_output_tokens: 32000,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'vertex_ai/meta/llama-3.2-90b-vision-instruct-maas': {
    max_tokens: 8192,
    max_input_tokens: 128000,
    max_output_tokens: 8192,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'vertex_ai/mistral-large@latest': {
    max_tokens: 8191,
    max_input_tokens: 128000,
    max_output_tokens: 8191,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 9e-6
  },
  'vertex_ai/mistral-large@2407': {
    max_tokens: 8191,
    max_input_tokens: 128000,
    max_output_tokens: 8191,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 9e-6
  },
  'vertex_ai/mistral-nemo@latest': {
    max_tokens: 128000,
    max_input_tokens: 128000,
    max_output_tokens: 128000,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 3e-6
  },
  'vertex_ai/jamba-1.5-mini@001': {
    max_tokens: 256000,
    max_input_tokens: 256000,
    max_output_tokens: 256000,
    input_cost_per_token: 2e-7,
    output_cost_per_token: 4e-7
  },
  'vertex_ai/jamba-1.5-large@001': {
    max_tokens: 256000,
    max_input_tokens: 256000,
    max_output_tokens: 256000,
    input_cost_per_token: 2e-6,
    output_cost_per_token: 8e-6
  },
  'vertex_ai/jamba-1.5': {
    max_tokens: 256000,
    max_input_tokens: 256000,
    max_output_tokens: 256000,
    input_cost_per_token: 2e-7,
    output_cost_per_token: 4e-7
  },
  'vertex_ai/jamba-1.5-mini': {
    max_tokens: 256000,
    max_input_tokens: 256000,
    max_output_tokens: 256000,
    input_cost_per_token: 2e-7,
    output_cost_per_token: 4e-7
  },
  'vertex_ai/jamba-1.5-large': {
    max_tokens: 256000,
    max_input_tokens: 256000,
    max_output_tokens: 256000,
    input_cost_per_token: 2e-6,
    output_cost_per_token: 8e-6
  },
  'vertex_ai/mistral-nemo@2407': {
    max_tokens: 128000,
    max_input_tokens: 128000,
    max_output_tokens: 128000,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 3e-6
  },
  'vertex_ai/codestral@latest': {
    max_tokens: 128000,
    max_input_tokens: 128000,
    max_output_tokens: 128000,
    input_cost_per_token: 1e-6,
    output_cost_per_token: 3e-6
  },
  'vertex_ai/codestral@2405': {
    max_tokens: 128000,
    max_input_tokens: 128000,
    max_output_tokens: 128000,
    input_cost_per_token: 1e-6,
    output_cost_per_token: 3e-6
  },
  'vertex_ai/imagegeneration@006': {},
  'vertex_ai/imagen-3.0-generate-001': {},
  'vertex_ai/imagen-3.0-fast-generate-001': {},
  'text-embedding-004': {
    max_tokens: 3072,
    max_input_tokens: 3072,
    input_cost_per_token: 6.25e-9,
    output_cost_per_token: 0
  },
  'text-multilingual-embedding-002': {
    max_tokens: 2048,
    max_input_tokens: 2048,
    input_cost_per_token: 6.25e-9,
    output_cost_per_token: 0
  },
  'textembedding-gecko': {
    max_tokens: 3072,
    max_input_tokens: 3072,
    input_cost_per_token: 6.25e-9,
    output_cost_per_token: 0
  },
  'textembedding-gecko-multilingual': {
    max_tokens: 3072,
    max_input_tokens: 3072,
    input_cost_per_token: 6.25e-9,
    output_cost_per_token: 0
  },
  'textembedding-gecko-multilingual@001': {
    max_tokens: 3072,
    max_input_tokens: 3072,
    input_cost_per_token: 6.25e-9,
    output_cost_per_token: 0
  },
  'textembedding-gecko@001': {
    max_tokens: 3072,
    max_input_tokens: 3072,
    input_cost_per_token: 6.25e-9,
    output_cost_per_token: 0
  },
  'textembedding-gecko@003': {
    max_tokens: 3072,
    max_input_tokens: 3072,
    input_cost_per_token: 6.25e-9,
    output_cost_per_token: 0
  },
  'text-embedding-preview-0409': {
    max_tokens: 3072,
    max_input_tokens: 3072,
    input_cost_per_token: 6.25e-9,
    output_cost_per_token: 0
  },
  'text-multilingual-embedding-preview-0409': {
    max_tokens: 3072,
    max_input_tokens: 3072,
    input_cost_per_token: 6.25e-9,
    output_cost_per_token: 0
  },
  'palm/chat-bison': {
    max_tokens: 4096,
    max_input_tokens: 8192,
    max_output_tokens: 4096,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'palm/chat-bison-001': {
    max_tokens: 4096,
    max_input_tokens: 8192,
    max_output_tokens: 4096,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'palm/text-bison': {
    max_tokens: 1024,
    max_input_tokens: 8192,
    max_output_tokens: 1024,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'palm/text-bison-001': {
    max_tokens: 1024,
    max_input_tokens: 8192,
    max_output_tokens: 1024,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'palm/text-bison-safety-off': {
    max_tokens: 1024,
    max_input_tokens: 8192,
    max_output_tokens: 1024,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'palm/text-bison-safety-recitation-off': {
    max_tokens: 1024,
    max_input_tokens: 8192,
    max_output_tokens: 1024,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 1.25e-7
  },
  'gemini/gemini-1.5-flash-002': {
    max_tokens: 8192,
    max_input_tokens: 1048576,
    max_output_tokens: 8192,
    input_cost_per_token: 7.5e-8,
    output_cost_per_token: 3e-7
  },
  'gemini/gemini-1.5-flash-001': {
    max_tokens: 8192,
    max_input_tokens: 1048576,
    max_output_tokens: 8192,
    input_cost_per_token: 7.5e-8,
    output_cost_per_token: 3e-7
  },
  'gemini/gemini-1.5-flash': {
    max_tokens: 8192,
    max_input_tokens: 1048576,
    max_output_tokens: 8192,
    input_cost_per_token: 7.5e-8,
    output_cost_per_token: 3e-7
  },
  'gemini/gemini-1.5-flash-latest': {
    max_tokens: 8192,
    max_input_tokens: 1048576,
    max_output_tokens: 8192,
    input_cost_per_token: 7.5e-8,
    output_cost_per_token: 3e-7
  },
  'gemini/gemini-1.5-flash-8b-exp-0924': {
    max_tokens: 8192,
    max_input_tokens: 1048576,
    max_output_tokens: 8192,
    input_cost_per_token: 0,
    output_cost_per_token: 0
  },
  'gemini/gemini-1.5-flash-exp-0827': {
    max_tokens: 8192,
    max_input_tokens: 1048576,
    max_output_tokens: 8192,
    input_cost_per_token: 0,
    output_cost_per_token: 0
  },
  'gemini/gemini-1.5-flash-8b-exp-0827': {
    max_tokens: 8192,
    max_input_tokens: 1000000,
    max_output_tokens: 8192,
    input_cost_per_token: 0,
    output_cost_per_token: 0
  },
  'gemini/gemini-pro': {
    max_tokens: 8192,
    max_input_tokens: 32760,
    max_output_tokens: 8192,
    input_cost_per_token: 3.5e-7,
    output_cost_per_token: 1.05e-6
  },
  'gemini/gemini-1.5-pro': {
    max_tokens: 8192,
    max_input_tokens: 2097152,
    max_output_tokens: 8192,
    input_cost_per_token: 3.5e-6,
    output_cost_per_token: 1.05e-5
  },
  'gemini/gemini-1.5-pro-002': {
    max_tokens: 8192,
    max_input_tokens: 2097152,
    max_output_tokens: 8192,
    input_cost_per_token: 3.5e-6,
    output_cost_per_token: 1.05e-5
  },
  'gemini/gemini-1.5-pro-001': {
    max_tokens: 8192,
    max_input_tokens: 2097152,
    max_output_tokens: 8192,
    input_cost_per_token: 3.5e-6,
    output_cost_per_token: 1.05e-5
  },
  'gemini/gemini-1.5-pro-exp-0801': {
    max_tokens: 8192,
    max_input_tokens: 2097152,
    max_output_tokens: 8192,
    input_cost_per_token: 3.5e-6,
    output_cost_per_token: 1.05e-5
  },
  'gemini/gemini-1.5-pro-exp-0827': {
    max_tokens: 8192,
    max_input_tokens: 2097152,
    max_output_tokens: 8192,
    input_cost_per_token: 0,
    output_cost_per_token: 0
  },
  'gemini/gemini-1.5-pro-latest': {
    max_tokens: 8192,
    max_input_tokens: 1048576,
    max_output_tokens: 8192,
    input_cost_per_token: 3.5e-6,
    output_cost_per_token: 1.05e-6
  },
  'gemini/gemini-pro-vision': {
    max_tokens: 2048,
    max_input_tokens: 30720,
    max_output_tokens: 2048,
    input_cost_per_token: 3.5e-7,
    output_cost_per_token: 1.05e-6
  },
  'gemini/gemini-gemma-2-27b-it': {
    max_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 3.5e-7,
    output_cost_per_token: 1.05e-6
  },
  'gemini/gemini-gemma-2-9b-it': {
    max_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 3.5e-7,
    output_cost_per_token: 1.05e-6
  },
  'command-r': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 1.5e-7,
    output_cost_per_token: 6e-7
  },
  'command-r-08-2024': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 1.5e-7,
    output_cost_per_token: 6e-7
  },
  'command-light': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-7,
    output_cost_per_token: 6e-7
  },
  'command-r-plus': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 2.5e-6,
    output_cost_per_token: 1e-5
  },
  'command-r-plus-08-2024': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 2.5e-6,
    output_cost_per_token: 1e-5
  },
  'command-nightly': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 1e-6,
    output_cost_per_token: 2e-6
  },
  command: {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 1e-6,
    output_cost_per_token: 2e-6
  },
  'rerank-english-v3.0': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'rerank-multilingual-v3.0': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'rerank-english-v2.0': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'rerank-multilingual-v2.0': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'embed-english-v3.0': {
    max_tokens: 512,
    max_input_tokens: 512,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 0.0
  },
  'embed-english-light-v3.0': {
    max_tokens: 512,
    max_input_tokens: 512,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 0.0
  },
  'embed-multilingual-v3.0': {
    max_tokens: 512,
    max_input_tokens: 512,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 0.0
  },
  'embed-english-v2.0': {
    max_tokens: 512,
    max_input_tokens: 512,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 0.0
  },
  'embed-english-light-v2.0': {
    max_tokens: 512,
    max_input_tokens: 512,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 0.0
  },
  'embed-multilingual-v2.0': {
    max_tokens: 256,
    max_input_tokens: 256,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 0.0
  },
  'replicate/meta/llama-2-13b': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 5e-7
  },
  'replicate/meta/llama-2-13b-chat': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 5e-7
  },
  'replicate/meta/llama-2-70b': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 6.5e-7,
    output_cost_per_token: 2.75e-6
  },
  'replicate/meta/llama-2-70b-chat': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 6.5e-7,
    output_cost_per_token: 2.75e-6
  },
  'replicate/meta/llama-2-7b': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 5e-8,
    output_cost_per_token: 2.5e-7
  },
  'replicate/meta/llama-2-7b-chat': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 5e-8,
    output_cost_per_token: 2.5e-7
  },
  'replicate/meta/llama-3-70b': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 6.5e-7,
    output_cost_per_token: 2.75e-6
  },
  'replicate/meta/llama-3-70b-instruct': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 6.5e-7,
    output_cost_per_token: 2.75e-6
  },
  'replicate/meta/llama-3-8b': {
    max_tokens: 8086,
    max_input_tokens: 8086,
    max_output_tokens: 8086,
    input_cost_per_token: 5e-8,
    output_cost_per_token: 2.5e-7
  },
  'replicate/meta/llama-3-8b-instruct': {
    max_tokens: 8086,
    max_input_tokens: 8086,
    max_output_tokens: 8086,
    input_cost_per_token: 5e-8,
    output_cost_per_token: 2.5e-7
  },
  'replicate/mistralai/mistral-7b-v0.1': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 5e-8,
    output_cost_per_token: 2.5e-7
  },
  'replicate/mistralai/mistral-7b-instruct-v0.2': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 5e-8,
    output_cost_per_token: 2.5e-7
  },
  'replicate/mistralai/mixtral-8x7b-instruct-v0.1': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-7,
    output_cost_per_token: 1e-6
  },
  'openrouter/deepseek/deepseek-coder': {
    max_tokens: 4096,
    max_input_tokens: 32000,
    max_output_tokens: 4096,
    input_cost_per_token: 1.4e-7,
    output_cost_per_token: 2.8e-7
  },
  'openrouter/microsoft/wizardlm-2-8x22b:nitro': {
    max_tokens: 65536,
    input_cost_per_token: 1e-6,
    output_cost_per_token: 1e-6
  },
  'openrouter/google/gemini-pro-1.5': {
    max_tokens: 8192,
    max_input_tokens: 1000000,
    max_output_tokens: 8192,
    input_cost_per_token: 2.5e-6,
    output_cost_per_token: 7.5e-6
  },
  'openrouter/mistralai/mixtral-8x22b-instruct': {
    max_tokens: 65536,
    input_cost_per_token: 6.5e-7,
    output_cost_per_token: 6.5e-7
  },
  'openrouter/cohere/command-r-plus': {
    max_tokens: 128000,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 1.5e-5
  },
  'openrouter/databricks/dbrx-instruct': {
    max_tokens: 32768,
    input_cost_per_token: 6e-7,
    output_cost_per_token: 6e-7
  },
  'openrouter/anthropic/claude-3-haiku': {
    max_tokens: 200000,
    input_cost_per_token: 2.5e-7,
    output_cost_per_token: 1.25e-6
  },
  'openrouter/anthropic/claude-3-haiku-20240307': {
    max_tokens: 4096,
    max_input_tokens: 200000,
    max_output_tokens: 4096,
    input_cost_per_token: 2.5e-7,
    output_cost_per_token: 1.25e-6
  },
  'openrouter/anthropic/claude-3.5-sonnet': {
    max_tokens: 8192,
    max_input_tokens: 200000,
    max_output_tokens: 8192,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 1.5e-5
  },
  'openrouter/anthropic/claude-3.5-sonnet:beta': {
    max_tokens: 8192,
    max_input_tokens: 200000,
    max_output_tokens: 8192,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 1.5e-5
  },
  'openrouter/anthropic/claude-3-sonnet': {
    max_tokens: 200000,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 1.5e-5
  },
  'openrouter/mistralai/mistral-large': {
    max_tokens: 32000,
    input_cost_per_token: 8e-6,
    output_cost_per_token: 2.4e-5
  },
  'openrouter/cognitivecomputations/dolphin-mixtral-8x7b': {
    max_tokens: 32769,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 5e-7
  },
  'openrouter/google/gemini-pro-vision': {
    max_tokens: 45875,
    input_cost_per_token: 1.25e-7,
    output_cost_per_token: 3.75e-7
  },
  'openrouter/fireworks/firellava-13b': {
    max_tokens: 4096,
    input_cost_per_token: 2e-7,
    output_cost_per_token: 2e-7
  },
  'openrouter/meta-llama/llama-3-8b-instruct:free': {
    max_tokens: 8192,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'openrouter/meta-llama/llama-3-8b-instruct:extended': {
    max_tokens: 16384,
    input_cost_per_token: 2.25e-7,
    output_cost_per_token: 2.25e-6
  },
  'openrouter/meta-llama/llama-3-70b-instruct:nitro': {
    max_tokens: 8192,
    input_cost_per_token: 9e-7,
    output_cost_per_token: 9e-7
  },
  'openrouter/meta-llama/llama-3-70b-instruct': {
    max_tokens: 8192,
    input_cost_per_token: 5.9e-7,
    output_cost_per_token: 7.9e-7
  },
  'openrouter/openai/o1-mini': {
    max_tokens: 65536,
    max_input_tokens: 128000,
    max_output_tokens: 65536,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 1.2e-5
  },
  'openrouter/openai/o1-mini-2024-09-12': {
    max_tokens: 65536,
    max_input_tokens: 128000,
    max_output_tokens: 65536,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 1.2e-5
  },
  'openrouter/openai/o1-preview': {
    max_tokens: 32768,
    max_input_tokens: 128000,
    max_output_tokens: 32768,
    input_cost_per_token: 1.5e-5,
    output_cost_per_token: 6e-5
  },
  'openrouter/openai/o1-preview-2024-09-12': {
    max_tokens: 32768,
    max_input_tokens: 128000,
    max_output_tokens: 32768,
    input_cost_per_token: 1.5e-5,
    output_cost_per_token: 6e-5
  },
  'openrouter/openai/gpt-4o': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 5e-6,
    output_cost_per_token: 1.5e-5
  },
  'openrouter/openai/gpt-4o-2024-05-13': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 5e-6,
    output_cost_per_token: 1.5e-5
  },
  'openrouter/openai/gpt-4-vision-preview': {
    max_tokens: 130000,
    input_cost_per_token: 1e-5,
    output_cost_per_token: 3e-5
  },
  'openrouter/openai/gpt-3.5-turbo': {
    max_tokens: 4095,
    input_cost_per_token: 1.5e-6,
    output_cost_per_token: 2e-6
  },
  'openrouter/openai/gpt-3.5-turbo-16k': {
    max_tokens: 16383,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 4e-6
  },
  'openrouter/openai/gpt-4': {
    max_tokens: 8192,
    input_cost_per_token: 3e-5,
    output_cost_per_token: 6e-5
  },
  'openrouter/anthropic/claude-instant-v1': {
    max_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 1.63e-6,
    output_cost_per_token: 5.51e-6
  },
  'openrouter/anthropic/claude-2': {
    max_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 1.102e-5,
    output_cost_per_token: 3.268e-5
  },
  'openrouter/anthropic/claude-3-opus': {
    max_tokens: 4096,
    max_input_tokens: 200000,
    max_output_tokens: 4096,
    input_cost_per_token: 1.5e-5,
    output_cost_per_token: 7.5e-5
  },
  'openrouter/google/palm-2-chat-bison': {
    max_tokens: 25804,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 5e-7
  },
  'openrouter/google/palm-2-codechat-bison': {
    max_tokens: 20070,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 5e-7
  },
  'openrouter/meta-llama/llama-2-13b-chat': {
    max_tokens: 4096,
    input_cost_per_token: 2e-7,
    output_cost_per_token: 2e-7
  },
  'openrouter/meta-llama/llama-2-70b-chat': {
    max_tokens: 4096,
    input_cost_per_token: 1.5e-6,
    output_cost_per_token: 1.5e-6
  },
  'openrouter/meta-llama/codellama-34b-instruct': {
    max_tokens: 8192,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 5e-7
  },
  'openrouter/nousresearch/nous-hermes-llama2-13b': {
    max_tokens: 4096,
    input_cost_per_token: 2e-7,
    output_cost_per_token: 2e-7
  },
  'openrouter/mancer/weaver': {
    max_tokens: 8000,
    input_cost_per_token: 5.625e-6,
    output_cost_per_token: 5.625e-6
  },
  'openrouter/gryphe/mythomax-l2-13b': {
    max_tokens: 8192,
    input_cost_per_token: 1.875e-6,
    output_cost_per_token: 1.875e-6
  },
  'openrouter/jondurbin/airoboros-l2-70b-2.1': {
    max_tokens: 4096,
    input_cost_per_token: 1.3875e-5,
    output_cost_per_token: 1.3875e-5
  },
  'openrouter/undi95/remm-slerp-l2-13b': {
    max_tokens: 6144,
    input_cost_per_token: 1.875e-6,
    output_cost_per_token: 1.875e-6
  },
  'openrouter/pygmalionai/mythalion-13b': {
    max_tokens: 4096,
    input_cost_per_token: 1.875e-6,
    output_cost_per_token: 1.875e-6
  },
  'openrouter/mistralai/mistral-7b-instruct': {
    max_tokens: 8192,
    input_cost_per_token: 1.3e-7,
    output_cost_per_token: 1.3e-7
  },
  'openrouter/mistralai/mistral-7b-instruct:free': {
    max_tokens: 8192,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'j2-ultra': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 1.5e-5,
    output_cost_per_token: 1.5e-5
  },
  'jamba-1.5-mini@001': {
    max_tokens: 256000,
    max_input_tokens: 256000,
    max_output_tokens: 256000,
    input_cost_per_token: 2e-7,
    output_cost_per_token: 4e-7
  },
  'jamba-1.5-large@001': {
    max_tokens: 256000,
    max_input_tokens: 256000,
    max_output_tokens: 256000,
    input_cost_per_token: 2e-6,
    output_cost_per_token: 8e-6
  },
  'jamba-1.5': {
    max_tokens: 256000,
    max_input_tokens: 256000,
    max_output_tokens: 256000,
    input_cost_per_token: 2e-7,
    output_cost_per_token: 4e-7
  },
  'jamba-1.5-mini': {
    max_tokens: 256000,
    max_input_tokens: 256000,
    max_output_tokens: 256000,
    input_cost_per_token: 2e-7,
    output_cost_per_token: 4e-7
  },
  'jamba-1.5-large': {
    max_tokens: 256000,
    max_input_tokens: 256000,
    max_output_tokens: 256000,
    input_cost_per_token: 2e-6,
    output_cost_per_token: 8e-6
  },
  'j2-mid': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 1e-5,
    output_cost_per_token: 1e-5
  },
  'j2-light': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 3e-6
  },
  dolphin: {
    max_tokens: 16384,
    max_input_tokens: 16384,
    max_output_tokens: 16384,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 5e-7
  },
  chatdolphin: {
    max_tokens: 16384,
    max_input_tokens: 16384,
    max_output_tokens: 16384,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 5e-7
  },
  'luminous-base': { max_tokens: 2048, input_cost_per_token: 3e-5, output_cost_per_token: 3.3e-5 },
  'luminous-base-control': {
    max_tokens: 2048,
    input_cost_per_token: 3.75e-5,
    output_cost_per_token: 4.125e-5
  },
  'luminous-extended': {
    max_tokens: 2048,
    input_cost_per_token: 4.5e-5,
    output_cost_per_token: 4.95e-5
  },
  'luminous-extended-control': {
    max_tokens: 2048,
    input_cost_per_token: 5.625e-5,
    output_cost_per_token: 6.1875e-5
  },
  'luminous-supreme': {
    max_tokens: 2048,
    input_cost_per_token: 0.000175,
    output_cost_per_token: 0.0001925
  },
  'luminous-supreme-control': {
    max_tokens: 2048,
    input_cost_per_token: 0.00021875,
    output_cost_per_token: 0.000240625
  },
  'ai21.j2-mid-v1': {
    max_tokens: 8191,
    max_input_tokens: 8191,
    max_output_tokens: 8191,
    input_cost_per_token: 1.25e-5,
    output_cost_per_token: 1.25e-5
  },
  'ai21.j2-ultra-v1': {
    max_tokens: 8191,
    max_input_tokens: 8191,
    max_output_tokens: 8191,
    input_cost_per_token: 1.88e-5,
    output_cost_per_token: 1.88e-5
  },
  'ai21.jamba-instruct-v1:0': {
    max_tokens: 4096,
    max_input_tokens: 70000,
    max_output_tokens: 4096,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 7e-7
  },
  'amazon.titan-text-lite-v1': {
    max_tokens: 4000,
    max_input_tokens: 42000,
    max_output_tokens: 4000,
    input_cost_per_token: 3e-7,
    output_cost_per_token: 4e-7
  },
  'amazon.titan-text-express-v1': {
    max_tokens: 8000,
    max_input_tokens: 42000,
    max_output_tokens: 8000,
    input_cost_per_token: 1.3e-6,
    output_cost_per_token: 1.7e-6
  },
  'amazon.titan-text-premier-v1:0': {
    max_tokens: 32000,
    max_input_tokens: 42000,
    max_output_tokens: 32000,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 1.5e-6
  },
  'amazon.titan-embed-text-v1': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 0.0
  },
  'amazon.titan-embed-text-v2:0': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    input_cost_per_token: 2e-7,
    output_cost_per_token: 0.0
  },
  'mistral.mistral-7b-instruct-v0:2': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 1.5e-7,
    output_cost_per_token: 2e-7
  },
  'mistral.mixtral-8x7b-instruct-v0:1': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 4.5e-7,
    output_cost_per_token: 7e-7
  },
  'mistral.mistral-large-2402-v1:0': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 8e-6,
    output_cost_per_token: 2.4e-5
  },
  'mistral.mistral-large-2407-v1:0': {
    max_tokens: 8191,
    max_input_tokens: 128000,
    max_output_tokens: 8191,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 9e-6
  },
  'mistral.mistral-small-2402-v1:0': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 1e-6,
    output_cost_per_token: 3e-6
  },
  'bedrock/us-west-2/mistral.mixtral-8x7b-instruct-v0:1': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 4.5e-7,
    output_cost_per_token: 7e-7
  },
  'bedrock/us-east-1/mistral.mixtral-8x7b-instruct-v0:1': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 4.5e-7,
    output_cost_per_token: 7e-7
  },
  'bedrock/eu-west-3/mistral.mixtral-8x7b-instruct-v0:1': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 5.9e-7,
    output_cost_per_token: 9.1e-7
  },
  'bedrock/us-west-2/mistral.mistral-7b-instruct-v0:2': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 1.5e-7,
    output_cost_per_token: 2e-7
  },
  'bedrock/us-east-1/mistral.mistral-7b-instruct-v0:2': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 1.5e-7,
    output_cost_per_token: 2e-7
  },
  'bedrock/eu-west-3/mistral.mistral-7b-instruct-v0:2': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 2e-7,
    output_cost_per_token: 2.6e-7
  },
  'bedrock/us-east-1/mistral.mistral-large-2402-v1:0': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 8e-6,
    output_cost_per_token: 2.4e-5
  },
  'bedrock/us-west-2/mistral.mistral-large-2402-v1:0': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 8e-6,
    output_cost_per_token: 2.4e-5
  },
  'bedrock/eu-west-3/mistral.mistral-large-2402-v1:0': {
    max_tokens: 8191,
    max_input_tokens: 32000,
    max_output_tokens: 8191,
    input_cost_per_token: 1.04e-5,
    output_cost_per_token: 3.12e-5
  },
  'anthropic.claude-3-sonnet-20240229-v1:0': {
    max_tokens: 4096,
    max_input_tokens: 200000,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 1.5e-5
  },
  'anthropic.claude-3-5-sonnet-20240620-v1:0': {
    max_tokens: 4096,
    max_input_tokens: 200000,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 1.5e-5
  },
  'anthropic.claude-3-haiku-20240307-v1:0': {
    max_tokens: 4096,
    max_input_tokens: 200000,
    max_output_tokens: 4096,
    input_cost_per_token: 2.5e-7,
    output_cost_per_token: 1.25e-6
  },
  'anthropic.claude-3-opus-20240229-v1:0': {
    max_tokens: 4096,
    max_input_tokens: 200000,
    max_output_tokens: 4096,
    input_cost_per_token: 1.5e-5,
    output_cost_per_token: 7.5e-5
  },
  'us.anthropic.claude-3-sonnet-20240229-v1:0': {
    max_tokens: 4096,
    max_input_tokens: 200000,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 1.5e-5
  },
  'us.anthropic.claude-3-5-sonnet-20240620-v1:0': {
    max_tokens: 4096,
    max_input_tokens: 200000,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 1.5e-5
  },
  'us.anthropic.claude-3-haiku-20240307-v1:0': {
    max_tokens: 4096,
    max_input_tokens: 200000,
    max_output_tokens: 4096,
    input_cost_per_token: 2.5e-7,
    output_cost_per_token: 1.25e-6
  },
  'us.anthropic.claude-3-opus-20240229-v1:0': {
    max_tokens: 4096,
    max_input_tokens: 200000,
    max_output_tokens: 4096,
    input_cost_per_token: 1.5e-5,
    output_cost_per_token: 7.5e-5
  },
  'eu.anthropic.claude-3-sonnet-20240229-v1:0': {
    max_tokens: 4096,
    max_input_tokens: 200000,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 1.5e-5
  },
  'eu.anthropic.claude-3-5-sonnet-20240620-v1:0': {
    max_tokens: 4096,
    max_input_tokens: 200000,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 1.5e-5
  },
  'eu.anthropic.claude-3-haiku-20240307-v1:0': {
    max_tokens: 4096,
    max_input_tokens: 200000,
    max_output_tokens: 4096,
    input_cost_per_token: 2.5e-7,
    output_cost_per_token: 1.25e-6
  },
  'eu.anthropic.claude-3-opus-20240229-v1:0': {
    max_tokens: 4096,
    max_input_tokens: 200000,
    max_output_tokens: 4096,
    input_cost_per_token: 1.5e-5,
    output_cost_per_token: 7.5e-5
  },
  'anthropic.claude-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 8e-6,
    output_cost_per_token: 2.4e-5
  },
  'bedrock/us-east-1/anthropic.claude-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 8e-6,
    output_cost_per_token: 2.4e-5
  },
  'bedrock/us-west-2/anthropic.claude-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 8e-6,
    output_cost_per_token: 2.4e-5
  },
  'bedrock/ap-northeast-1/anthropic.claude-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 8e-6,
    output_cost_per_token: 2.4e-5
  },
  'bedrock/ap-northeast-1/1-month-commitment/anthropic.claude-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/ap-northeast-1/6-month-commitment/anthropic.claude-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/eu-central-1/anthropic.claude-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 8e-6,
    output_cost_per_token: 2.4e-5
  },
  'bedrock/eu-central-1/1-month-commitment/anthropic.claude-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/eu-central-1/6-month-commitment/anthropic.claude-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/us-east-1/1-month-commitment/anthropic.claude-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/us-east-1/6-month-commitment/anthropic.claude-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/us-west-2/1-month-commitment/anthropic.claude-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/us-west-2/6-month-commitment/anthropic.claude-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'anthropic.claude-v2': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 8e-6,
    output_cost_per_token: 2.4e-5
  },
  'bedrock/us-east-1/anthropic.claude-v2': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 8e-6,
    output_cost_per_token: 2.4e-5
  },
  'bedrock/us-west-2/anthropic.claude-v2': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 8e-6,
    output_cost_per_token: 2.4e-5
  },
  'bedrock/ap-northeast-1/anthropic.claude-v2': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 8e-6,
    output_cost_per_token: 2.4e-5
  },
  'bedrock/ap-northeast-1/1-month-commitment/anthropic.claude-v2': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/ap-northeast-1/6-month-commitment/anthropic.claude-v2': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/eu-central-1/anthropic.claude-v2': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 8e-6,
    output_cost_per_token: 2.4e-5
  },
  'bedrock/eu-central-1/1-month-commitment/anthropic.claude-v2': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/eu-central-1/6-month-commitment/anthropic.claude-v2': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/us-east-1/1-month-commitment/anthropic.claude-v2': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/us-east-1/6-month-commitment/anthropic.claude-v2': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/us-west-2/1-month-commitment/anthropic.claude-v2': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/us-west-2/6-month-commitment/anthropic.claude-v2': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'anthropic.claude-v2:1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 8e-6,
    output_cost_per_token: 2.4e-5
  },
  'bedrock/us-east-1/anthropic.claude-v2:1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 8e-6,
    output_cost_per_token: 2.4e-5
  },
  'bedrock/us-west-2/anthropic.claude-v2:1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 8e-6,
    output_cost_per_token: 2.4e-5
  },
  'bedrock/ap-northeast-1/anthropic.claude-v2:1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 8e-6,
    output_cost_per_token: 2.4e-5
  },
  'bedrock/ap-northeast-1/1-month-commitment/anthropic.claude-v2:1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/ap-northeast-1/6-month-commitment/anthropic.claude-v2:1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/eu-central-1/anthropic.claude-v2:1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 8e-6,
    output_cost_per_token: 2.4e-5
  },
  'bedrock/eu-central-1/1-month-commitment/anthropic.claude-v2:1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/eu-central-1/6-month-commitment/anthropic.claude-v2:1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/us-east-1/1-month-commitment/anthropic.claude-v2:1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/us-east-1/6-month-commitment/anthropic.claude-v2:1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/us-west-2/1-month-commitment/anthropic.claude-v2:1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/us-west-2/6-month-commitment/anthropic.claude-v2:1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'anthropic.claude-instant-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 1.63e-6,
    output_cost_per_token: 5.51e-6
  },
  'bedrock/us-east-1/anthropic.claude-instant-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 8e-7,
    output_cost_per_token: 2.4e-6
  },
  'bedrock/us-east-1/1-month-commitment/anthropic.claude-instant-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/us-east-1/6-month-commitment/anthropic.claude-instant-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/us-west-2/1-month-commitment/anthropic.claude-instant-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/us-west-2/6-month-commitment/anthropic.claude-instant-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/us-west-2/anthropic.claude-instant-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 8e-7,
    output_cost_per_token: 2.4e-6
  },
  'bedrock/ap-northeast-1/anthropic.claude-instant-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 2.23e-6,
    output_cost_per_token: 7.55e-6
  },
  'bedrock/ap-northeast-1/1-month-commitment/anthropic.claude-instant-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/ap-northeast-1/6-month-commitment/anthropic.claude-instant-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/eu-central-1/anthropic.claude-instant-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191,
    input_cost_per_token: 2.48e-6,
    output_cost_per_token: 8.38e-6
  },
  'bedrock/eu-central-1/1-month-commitment/anthropic.claude-instant-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'bedrock/eu-central-1/6-month-commitment/anthropic.claude-instant-v1': {
    max_tokens: 8191,
    max_input_tokens: 100000,
    max_output_tokens: 8191
  },
  'cohere.command-text-v14': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 1.5e-6,
    output_cost_per_token: 2e-6
  },
  'bedrock/*/1-month-commitment/cohere.command-text-v14': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096
  },
  'bedrock/*/6-month-commitment/cohere.command-text-v14': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096
  },
  'cohere.command-light-text-v14': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-7,
    output_cost_per_token: 6e-7
  },
  'bedrock/*/1-month-commitment/cohere.command-light-text-v14': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096
  },
  'bedrock/*/6-month-commitment/cohere.command-light-text-v14': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096
  },
  'cohere.command-r-plus-v1:0': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 1.5e-5
  },
  'cohere.command-r-v1:0': {
    max_tokens: 4096,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 1.5e-6
  },
  'cohere.embed-english-v3': {
    max_tokens: 512,
    max_input_tokens: 512,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 0.0
  },
  'cohere.embed-multilingual-v3': {
    max_tokens: 512,
    max_input_tokens: 512,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 0.0
  },
  'meta.llama2-13b-chat-v1': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 7.5e-7,
    output_cost_per_token: 1e-6
  },
  'meta.llama2-70b-chat-v1': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 1.95e-6,
    output_cost_per_token: 2.56e-6
  },
  'meta.llama3-8b-instruct-v1:0': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 3e-7,
    output_cost_per_token: 6e-7
  },
  'bedrock/us-east-1/meta.llama3-8b-instruct-v1:0': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 3e-7,
    output_cost_per_token: 6e-7
  },
  'bedrock/us-west-1/meta.llama3-8b-instruct-v1:0': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 3e-7,
    output_cost_per_token: 6e-7
  },
  'bedrock/ap-south-1/meta.llama3-8b-instruct-v1:0': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 3.6e-7,
    output_cost_per_token: 7.2e-7
  },
  'bedrock/ca-central-1/meta.llama3-8b-instruct-v1:0': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 3.5e-7,
    output_cost_per_token: 6.9e-7
  },
  'bedrock/eu-west-1/meta.llama3-8b-instruct-v1:0': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 3.2e-7,
    output_cost_per_token: 6.5e-7
  },
  'bedrock/eu-west-2/meta.llama3-8b-instruct-v1:0': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 3.9e-7,
    output_cost_per_token: 7.8e-7
  },
  'bedrock/sa-east-1/meta.llama3-8b-instruct-v1:0': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 5e-7,
    output_cost_per_token: 1.01e-6
  },
  'meta.llama3-70b-instruct-v1:0': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 2.65e-6,
    output_cost_per_token: 3.5e-6
  },
  'bedrock/us-east-1/meta.llama3-70b-instruct-v1:0': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 2.65e-6,
    output_cost_per_token: 3.5e-6
  },
  'bedrock/us-west-1/meta.llama3-70b-instruct-v1:0': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 2.65e-6,
    output_cost_per_token: 3.5e-6
  },
  'bedrock/ap-south-1/meta.llama3-70b-instruct-v1:0': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 3.18e-6,
    output_cost_per_token: 4.2e-6
  },
  'bedrock/ca-central-1/meta.llama3-70b-instruct-v1:0': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 3.05e-6,
    output_cost_per_token: 4.03e-6
  },
  'bedrock/eu-west-1/meta.llama3-70b-instruct-v1:0': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 2.86e-6,
    output_cost_per_token: 3.78e-6
  },
  'bedrock/eu-west-2/meta.llama3-70b-instruct-v1:0': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 3.45e-6,
    output_cost_per_token: 4.55e-6
  },
  'bedrock/sa-east-1/meta.llama3-70b-instruct-v1:0': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 4.45e-6,
    output_cost_per_token: 5.88e-6
  },
  'meta.llama3-1-8b-instruct-v1:0': {
    max_tokens: 128000,
    max_input_tokens: 128000,
    max_output_tokens: 2048,
    input_cost_per_token: 2.2e-7,
    output_cost_per_token: 2.2e-7
  },
  'meta.llama3-1-70b-instruct-v1:0': {
    max_tokens: 128000,
    max_input_tokens: 128000,
    max_output_tokens: 2048,
    input_cost_per_token: 9.9e-7,
    output_cost_per_token: 9.9e-7
  },
  'meta.llama3-1-405b-instruct-v1:0': {
    max_tokens: 128000,
    max_input_tokens: 128000,
    max_output_tokens: 4096,
    input_cost_per_token: 5.32e-6,
    output_cost_per_token: 1.6e-5
  },
  '512-x-512/50-steps/stability.stable-diffusion-xl-v0': { max_tokens: 77, max_input_tokens: 77 },
  '512-x-512/max-steps/stability.stable-diffusion-xl-v0': { max_tokens: 77, max_input_tokens: 77 },
  'max-x-max/50-steps/stability.stable-diffusion-xl-v0': { max_tokens: 77, max_input_tokens: 77 },
  'max-x-max/max-steps/stability.stable-diffusion-xl-v0': { max_tokens: 77, max_input_tokens: 77 },
  '1024-x-1024/50-steps/stability.stable-diffusion-xl-v1': { max_tokens: 77, max_input_tokens: 77 },
  '1024-x-1024/max-steps/stability.stable-diffusion-xl-v1': {
    max_tokens: 77,
    max_input_tokens: 77
  },
  'sagemaker/meta-textgeneration-llama-2-7b': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'sagemaker/meta-textgeneration-llama-2-7b-f': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'sagemaker/meta-textgeneration-llama-2-13b': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'sagemaker/meta-textgeneration-llama-2-13b-f': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'sagemaker/meta-textgeneration-llama-2-70b': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'sagemaker/meta-textgeneration-llama-2-70b-b-f': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'together-ai-up-to-4b': { input_cost_per_token: 1e-7, output_cost_per_token: 1e-7 },
  'together-ai-4.1b-8b': { input_cost_per_token: 2e-7, output_cost_per_token: 2e-7 },
  'together-ai-8.1b-21b': {
    max_tokens: 1000,
    input_cost_per_token: 3e-7,
    output_cost_per_token: 3e-7
  },
  'together-ai-21.1b-41b': { input_cost_per_token: 8e-7, output_cost_per_token: 8e-7 },
  'together-ai-41.1b-80b': { input_cost_per_token: 9e-7, output_cost_per_token: 9e-7 },
  'together-ai-81.1b-110b': { input_cost_per_token: 1.8e-6, output_cost_per_token: 1.8e-6 },
  'together-ai-embedding-up-to-150m': { input_cost_per_token: 8e-9, output_cost_per_token: 0.0 },
  'together-ai-embedding-151m-to-350m': {
    input_cost_per_token: 1.6e-8,
    output_cost_per_token: 0.0
  },
  'together_ai/mistralai/Mixtral-8x7B-Instruct-v0.1': {
    input_cost_per_token: 6e-7,
    output_cost_per_token: 6e-7
  },
  'together_ai/mistralai/Mistral-7B-Instruct-v0.1': {},
  'together_ai/togethercomputer/CodeLlama-34b-Instruct': {},
  'ollama/codegemma': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/codegeex4': {
    max_tokens: 32768,
    max_input_tokens: 32768,
    max_output_tokens: 8192,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/deepseek-coder-v2-instruct': {
    max_tokens: 32768,
    max_input_tokens: 32768,
    max_output_tokens: 8192,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/deepseek-coder-v2-base': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/deepseek-coder-v2-lite-instruct': {
    max_tokens: 32768,
    max_input_tokens: 32768,
    max_output_tokens: 8192,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/deepseek-coder-v2-lite-base': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/internlm2_5-20b-chat': {
    max_tokens: 32768,
    max_input_tokens: 32768,
    max_output_tokens: 8192,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/llama2': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/llama2:7b': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/llama2:13b': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/llama2:70b': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/llama2-uncensored': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/llama3': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/llama3:8b': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/llama3:70b': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/llama3.1': {
    max_tokens: 32768,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/mistral-large-instruct-2407': {
    max_tokens: 65536,
    max_input_tokens: 65536,
    max_output_tokens: 8192,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/mistral': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/mistral-7B-Instruct-v0.1': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/mistral-7B-Instruct-v0.2': {
    max_tokens: 32768,
    max_input_tokens: 32768,
    max_output_tokens: 32768,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/mixtral-8x7B-Instruct-v0.1': {
    max_tokens: 32768,
    max_input_tokens: 32768,
    max_output_tokens: 32768,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/mixtral-8x22B-Instruct-v0.1': {
    max_tokens: 65536,
    max_input_tokens: 65536,
    max_output_tokens: 65536,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/codellama': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/orca-mini': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'ollama/vicuna': {
    max_tokens: 2048,
    max_input_tokens: 2048,
    max_output_tokens: 2048,
    input_cost_per_token: 0.0,
    output_cost_per_token: 0.0
  },
  'deepinfra/lizpreciatior/lzlv_70b_fp16_hf': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 7e-7,
    output_cost_per_token: 9e-7
  },
  'deepinfra/Gryphe/MythoMax-L2-13b': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 2.2e-7,
    output_cost_per_token: 2.2e-7
  },
  'deepinfra/mistralai/Mistral-7B-Instruct-v0.1': {
    max_tokens: 8191,
    max_input_tokens: 32768,
    max_output_tokens: 8191,
    input_cost_per_token: 1.3e-7,
    output_cost_per_token: 1.3e-7
  },
  'deepinfra/meta-llama/Llama-2-70b-chat-hf': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 7e-7,
    output_cost_per_token: 9e-7
  },
  'deepinfra/cognitivecomputations/dolphin-2.6-mixtral-8x7b': {
    max_tokens: 8191,
    max_input_tokens: 32768,
    max_output_tokens: 8191,
    input_cost_per_token: 2.7e-7,
    output_cost_per_token: 2.7e-7
  },
  'deepinfra/codellama/CodeLlama-34b-Instruct-hf': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 6e-7,
    output_cost_per_token: 6e-7
  },
  'deepinfra/deepinfra/mixtral': {
    max_tokens: 4096,
    max_input_tokens: 32000,
    max_output_tokens: 4096,
    input_cost_per_token: 2.7e-7,
    output_cost_per_token: 2.7e-7
  },
  'deepinfra/Phind/Phind-CodeLlama-34B-v2': {
    max_tokens: 4096,
    max_input_tokens: 16384,
    max_output_tokens: 4096,
    input_cost_per_token: 6e-7,
    output_cost_per_token: 6e-7
  },
  'deepinfra/mistralai/Mixtral-8x7B-Instruct-v0.1': {
    max_tokens: 8191,
    max_input_tokens: 32768,
    max_output_tokens: 8191,
    input_cost_per_token: 2.7e-7,
    output_cost_per_token: 2.7e-7
  },
  'deepinfra/deepinfra/airoboros-70b': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 7e-7,
    output_cost_per_token: 9e-7
  },
  'deepinfra/01-ai/Yi-34B-Chat': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 6e-7,
    output_cost_per_token: 6e-7
  },
  'deepinfra/01-ai/Yi-6B-200K': {
    max_tokens: 4096,
    max_input_tokens: 200000,
    max_output_tokens: 4096,
    input_cost_per_token: 1.3e-7,
    output_cost_per_token: 1.3e-7
  },
  'deepinfra/jondurbin/airoboros-l2-70b-gpt4-1.4.1': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 7e-7,
    output_cost_per_token: 9e-7
  },
  'deepinfra/meta-llama/Llama-2-13b-chat-hf': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 2.2e-7,
    output_cost_per_token: 2.2e-7
  },
  'deepinfra/amazon/MistralLite': {
    max_tokens: 8191,
    max_input_tokens: 32768,
    max_output_tokens: 8191,
    input_cost_per_token: 2e-7,
    output_cost_per_token: 2e-7
  },
  'deepinfra/meta-llama/Llama-2-7b-chat-hf': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 1.3e-7,
    output_cost_per_token: 1.3e-7
  },
  'deepinfra/meta-llama/Meta-Llama-3-8B-Instruct': {
    max_tokens: 8191,
    max_input_tokens: 8191,
    max_output_tokens: 4096,
    input_cost_per_token: 8e-8,
    output_cost_per_token: 8e-8
  },
  'deepinfra/meta-llama/Meta-Llama-3-70B-Instruct': {
    max_tokens: 8191,
    max_input_tokens: 8191,
    max_output_tokens: 4096,
    input_cost_per_token: 5.9e-7,
    output_cost_per_token: 7.9e-7
  },
  'deepinfra/01-ai/Yi-34B-200K': {
    max_tokens: 4096,
    max_input_tokens: 200000,
    max_output_tokens: 4096,
    input_cost_per_token: 6e-7,
    output_cost_per_token: 6e-7
  },
  'deepinfra/openchat/openchat_3.5': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 1.3e-7,
    output_cost_per_token: 1.3e-7
  },
  'perplexity/codellama-34b-instruct': {
    max_tokens: 16384,
    max_input_tokens: 16384,
    max_output_tokens: 16384,
    input_cost_per_token: 3.5e-7,
    output_cost_per_token: 1.4e-6
  },
  'perplexity/codellama-70b-instruct': {
    max_tokens: 16384,
    max_input_tokens: 16384,
    max_output_tokens: 16384,
    input_cost_per_token: 7e-7,
    output_cost_per_token: 2.8e-6
  },
  'perplexity/llama-3.1-70b-instruct': {
    max_tokens: 131072,
    max_input_tokens: 131072,
    max_output_tokens: 131072,
    input_cost_per_token: 1e-6,
    output_cost_per_token: 1e-6
  },
  'perplexity/llama-3.1-8b-instruct': {
    max_tokens: 131072,
    max_input_tokens: 131072,
    max_output_tokens: 131072,
    input_cost_per_token: 2e-7,
    output_cost_per_token: 2e-7
  },
  'perplexity/llama-3.1-sonar-huge-128k-online': {
    max_tokens: 127072,
    max_input_tokens: 127072,
    max_output_tokens: 127072,
    input_cost_per_token: 5e-6,
    output_cost_per_token: 5e-6
  },
  'perplexity/llama-3.1-sonar-large-128k-online': {
    max_tokens: 127072,
    max_input_tokens: 127072,
    max_output_tokens: 127072,
    input_cost_per_token: 1e-6,
    output_cost_per_token: 1e-6
  },
  'perplexity/llama-3.1-sonar-large-128k-chat': {
    max_tokens: 131072,
    max_input_tokens: 131072,
    max_output_tokens: 131072,
    input_cost_per_token: 1e-6,
    output_cost_per_token: 1e-6
  },
  'perplexity/llama-3.1-sonar-small-128k-chat': {
    max_tokens: 131072,
    max_input_tokens: 131072,
    max_output_tokens: 131072,
    input_cost_per_token: 2e-7,
    output_cost_per_token: 2e-7
  },
  'perplexity/llama-3.1-sonar-small-128k-online': {
    max_tokens: 127072,
    max_input_tokens: 127072,
    max_output_tokens: 127072,
    input_cost_per_token: 2e-7,
    output_cost_per_token: 2e-7
  },
  'perplexity/pplx-7b-chat': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 7e-8,
    output_cost_per_token: 2.8e-7
  },
  'perplexity/pplx-70b-chat': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 7e-7,
    output_cost_per_token: 2.8e-6
  },
  'perplexity/pplx-7b-online': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 0.0,
    output_cost_per_token: 2.8e-7
  },
  'perplexity/pplx-70b-online': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 0.0,
    output_cost_per_token: 2.8e-6
  },
  'perplexity/llama-2-70b-chat': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 7e-7,
    output_cost_per_token: 2.8e-6
  },
  'perplexity/mistral-7b-instruct': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 7e-8,
    output_cost_per_token: 2.8e-7
  },
  'perplexity/mixtral-8x7b-instruct': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 7e-8,
    output_cost_per_token: 2.8e-7
  },
  'perplexity/sonar-small-chat': {
    max_tokens: 16384,
    max_input_tokens: 16384,
    max_output_tokens: 16384,
    input_cost_per_token: 7e-8,
    output_cost_per_token: 2.8e-7
  },
  'perplexity/sonar-small-online': {
    max_tokens: 12000,
    max_input_tokens: 12000,
    max_output_tokens: 12000,
    input_cost_per_token: 0,
    output_cost_per_token: 2.8e-7
  },
  'perplexity/sonar-medium-chat': {
    max_tokens: 16384,
    max_input_tokens: 16384,
    max_output_tokens: 16384,
    input_cost_per_token: 6e-7,
    output_cost_per_token: 1.8e-6
  },
  'perplexity/sonar-medium-online': {
    max_tokens: 12000,
    max_input_tokens: 12000,
    max_output_tokens: 12000,
    input_cost_per_token: 0,
    output_cost_per_token: 1.8e-6
  },
  'fireworks_ai/accounts/fireworks/models/llama-v3p2-1b-instruct': {
    max_tokens: 16384,
    max_input_tokens: 16384,
    max_output_tokens: 16384,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 1e-7
  },
  'fireworks_ai/accounts/fireworks/models/llama-v3p2-3b-instruct': {
    max_tokens: 16384,
    max_input_tokens: 16384,
    max_output_tokens: 16384,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 1e-7
  },
  'fireworks_ai/accounts/fireworks/models/llama-v3p2-11b-vision-instruct': {
    max_tokens: 16384,
    max_input_tokens: 16384,
    max_output_tokens: 16384,
    input_cost_per_token: 2e-7,
    output_cost_per_token: 2e-7
  },
  'accounts/fireworks/models/llama-v3p2-90b-vision-instruct': {
    max_tokens: 16384,
    max_input_tokens: 16384,
    max_output_tokens: 16384,
    input_cost_per_token: 9e-7,
    output_cost_per_token: 9e-7
  },
  'fireworks_ai/accounts/fireworks/models/firefunction-v2': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 9e-7,
    output_cost_per_token: 9e-7
  },
  'fireworks_ai/accounts/fireworks/models/mixtral-8x22b-instruct-hf': {
    max_tokens: 65536,
    max_input_tokens: 65536,
    max_output_tokens: 65536,
    input_cost_per_token: 1.2e-6,
    output_cost_per_token: 1.2e-6
  },
  'fireworks_ai/accounts/fireworks/models/qwen2-72b-instruct': {
    max_tokens: 32768,
    max_input_tokens: 32768,
    max_output_tokens: 32768,
    input_cost_per_token: 9e-7,
    output_cost_per_token: 9e-7
  },
  'fireworks_ai/accounts/fireworks/models/yi-large': {
    max_tokens: 32768,
    max_input_tokens: 32768,
    max_output_tokens: 32768,
    input_cost_per_token: 3e-6,
    output_cost_per_token: 3e-6
  },
  'fireworks_ai/accounts/fireworks/models/deepseek-coder-v2-instruct': {
    max_tokens: 65536,
    max_input_tokens: 65536,
    max_output_tokens: 8192,
    input_cost_per_token: 1.2e-6,
    output_cost_per_token: 1.2e-6
  },
  'fireworks_ai/nomic-ai/nomic-embed-text-v1.5': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    input_cost_per_token: 8e-9,
    output_cost_per_token: 0.0
  },
  'fireworks_ai/nomic-ai/nomic-embed-text-v1': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    input_cost_per_token: 8e-9,
    output_cost_per_token: 0.0
  },
  'fireworks_ai/WhereIsAI/UAE-Large-V1': {
    max_tokens: 512,
    max_input_tokens: 512,
    input_cost_per_token: 1.6e-8,
    output_cost_per_token: 0.0
  },
  'fireworks_ai/thenlper/gte-large': {
    max_tokens: 512,
    max_input_tokens: 512,
    input_cost_per_token: 1.6e-8,
    output_cost_per_token: 0.0
  },
  'fireworks_ai/thenlper/gte-base': {
    max_tokens: 512,
    max_input_tokens: 512,
    input_cost_per_token: 8e-9,
    output_cost_per_token: 0.0
  },
  'fireworks-ai-up-to-16b': { input_cost_per_token: 2e-7, output_cost_per_token: 2e-7 },
  'fireworks-ai-16.1b-to-80b': { input_cost_per_token: 9e-7, output_cost_per_token: 9e-7 },
  'fireworks-ai-moe-up-to-56b': { input_cost_per_token: 5e-7, output_cost_per_token: 5e-7 },
  'fireworks-ai-56b-to-176b': { input_cost_per_token: 1.2e-6, output_cost_per_token: 1.2e-6 },
  'fireworks-ai-default': { input_cost_per_token: 0.0, output_cost_per_token: 0.0 },
  'fireworks-ai-embedding-up-to-150m': { input_cost_per_token: 8e-9, output_cost_per_token: 0.0 },
  'fireworks-ai-embedding-150m-to-350m': {
    input_cost_per_token: 1.6e-8,
    output_cost_per_token: 0.0
  },
  'anyscale/mistralai/Mistral-7B-Instruct-v0.1': {
    max_tokens: 16384,
    max_input_tokens: 16384,
    max_output_tokens: 16384,
    input_cost_per_token: 1.5e-7,
    output_cost_per_token: 1.5e-7
  },
  'anyscale/mistralai/Mixtral-8x7B-Instruct-v0.1': {
    max_tokens: 16384,
    max_input_tokens: 16384,
    max_output_tokens: 16384,
    input_cost_per_token: 1.5e-7,
    output_cost_per_token: 1.5e-7
  },
  'anyscale/mistralai/Mixtral-8x22B-Instruct-v0.1': {
    max_tokens: 65536,
    max_input_tokens: 65536,
    max_output_tokens: 65536,
    input_cost_per_token: 9e-7,
    output_cost_per_token: 9e-7
  },
  'anyscale/HuggingFaceH4/zephyr-7b-beta': {
    max_tokens: 16384,
    max_input_tokens: 16384,
    max_output_tokens: 16384,
    input_cost_per_token: 1.5e-7,
    output_cost_per_token: 1.5e-7
  },
  'anyscale/google/gemma-7b-it': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 1.5e-7,
    output_cost_per_token: 1.5e-7
  },
  'anyscale/meta-llama/Llama-2-7b-chat-hf': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 1.5e-7,
    output_cost_per_token: 1.5e-7
  },
  'anyscale/meta-llama/Llama-2-13b-chat-hf': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 2.5e-7,
    output_cost_per_token: 2.5e-7
  },
  'anyscale/meta-llama/Llama-2-70b-chat-hf': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 1e-6,
    output_cost_per_token: 1e-6
  },
  'anyscale/codellama/CodeLlama-34b-Instruct-hf': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 1e-6,
    output_cost_per_token: 1e-6
  },
  'anyscale/codellama/CodeLlama-70b-Instruct-hf': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 1e-6,
    output_cost_per_token: 1e-6
  },
  'anyscale/meta-llama/Meta-Llama-3-8B-Instruct': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 1.5e-7,
    output_cost_per_token: 1.5e-7
  },
  'anyscale/meta-llama/Meta-Llama-3-70B-Instruct': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 1e-6,
    output_cost_per_token: 1e-6
  },
  'cloudflare/@cf/meta/llama-2-7b-chat-fp16': {
    max_tokens: 3072,
    max_input_tokens: 3072,
    max_output_tokens: 3072,
    input_cost_per_token: 1.923e-6,
    output_cost_per_token: 1.923e-6
  },
  'cloudflare/@cf/meta/llama-2-7b-chat-int8': {
    max_tokens: 2048,
    max_input_tokens: 2048,
    max_output_tokens: 2048,
    input_cost_per_token: 1.923e-6,
    output_cost_per_token: 1.923e-6
  },
  'cloudflare/@cf/mistral/mistral-7b-instruct-v0.1': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 1.923e-6,
    output_cost_per_token: 1.923e-6
  },
  'cloudflare/@hf/thebloke/codellama-7b-instruct-awq': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 1.923e-6,
    output_cost_per_token: 1.923e-6
  },
  'voyage/voyage-01': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 0.0
  },
  'voyage/voyage-lite-01': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 0.0
  },
  'voyage/voyage-large-2': {
    max_tokens: 16000,
    max_input_tokens: 16000,
    input_cost_per_token: 1.2e-7,
    output_cost_per_token: 0.0
  },
  'voyage/voyage-law-2': {
    max_tokens: 16000,
    max_input_tokens: 16000,
    input_cost_per_token: 1.2e-7,
    output_cost_per_token: 0.0
  },
  'voyage/voyage-code-2': {
    max_tokens: 16000,
    max_input_tokens: 16000,
    input_cost_per_token: 1.2e-7,
    output_cost_per_token: 0.0
  },
  'voyage/voyage-2': {
    max_tokens: 4000,
    max_input_tokens: 4000,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 0.0
  },
  'voyage/voyage-lite-02-instruct': {
    max_tokens: 4000,
    max_input_tokens: 4000,
    input_cost_per_token: 1e-7,
    output_cost_per_token: 0.0
  },
  'databricks/databricks-meta-llama-3-1-405b-instruct': {
    max_tokens: 128000,
    max_input_tokens: 128000,
    max_output_tokens: 128000,
    input_cost_per_token: 5e-6,
    output_cost_per_token: 1.500002e-5
  },
  'databricks/databricks-meta-llama-3-1-70b-instruct': {
    max_tokens: 128000,
    max_input_tokens: 128000,
    max_output_tokens: 128000,
    input_cost_per_token: 1.00002e-6,
    output_cost_per_token: 2.99999e-6
  },
  'databricks/databricks-dbrx-instruct': {
    max_tokens: 32768,
    max_input_tokens: 32768,
    max_output_tokens: 32768,
    input_cost_per_token: 7.4998e-7,
    output_cost_per_token: 2.24901e-6
  },
  'databricks/databricks-meta-llama-3-70b-instruct': {
    max_tokens: 128000,
    max_input_tokens: 128000,
    max_output_tokens: 128000,
    input_cost_per_token: 1.00002e-6,
    output_cost_per_token: 2.99999e-6
  },
  'databricks/databricks-llama-2-70b-chat': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 5.0001e-7,
    output_cost_per_token: 1.5e-6
  },
  'databricks/databricks-mixtral-8x7b-instruct': {
    max_tokens: 4096,
    max_input_tokens: 4096,
    max_output_tokens: 4096,
    input_cost_per_token: 5.0001e-7,
    output_cost_per_token: 9.9902e-7
  },
  'databricks/databricks-mpt-30b-instruct': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 9.9902e-7,
    output_cost_per_token: 9.9902e-7
  },
  'databricks/databricks-mpt-7b-instruct': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    max_output_tokens: 8192,
    input_cost_per_token: 5.0001e-7,
    output_cost_per_token: 0.0
  },
  'databricks/databricks-bge-large-en': {
    max_tokens: 512,
    max_input_tokens: 512,
    input_cost_per_token: 1.0003e-7,
    output_cost_per_token: 0.0
  },
  'databricks/databricks-gte-large-en': {
    max_tokens: 8192,
    max_input_tokens: 8192,
    input_cost_per_token: 1.2999e-7,
    output_cost_per_token: 0.0
  }
};
