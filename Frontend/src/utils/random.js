// Deterministic generator so mock data stays stable between reloads.
export const createRandom = (seed) => {
  let state = seed
  return () => (state = (state * 16807) % 2147483647) / 2147483647
}
