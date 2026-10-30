import { useSearchParams } from 'react-router';

export default function useFilters(defaults, prefix = '') {
  const [params, setParams] = useSearchParams();
  const values = Object.fromEntries(Object.entries(defaults).map(([key, value]) => [key, params.get(prefix + key) ?? value]));
  function apply(next) {
    const query = new URLSearchParams(params);
    for (const key of Object.keys(defaults)) query.delete(prefix + key);
    for (const key of Object.keys(defaults)) if (next[key] !== '' && next[key] != null) query.set(prefix + key, next[key]);
    setParams(query);
  }
  return [values, apply, () => apply(defaults)];
}
