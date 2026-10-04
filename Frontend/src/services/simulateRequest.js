export const simulateRequest = (value, delay = 450) =>
  new Promise((resolve) => setTimeout(() => resolve(structuredClone(value)), delay))
