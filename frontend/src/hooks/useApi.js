import { useCallback, useEffect, useState } from 'react';
import { request } from '../services/api';

export default function useApi(url) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState({ url: null, status: 'idle', response: null });
  useEffect(() => {
    if (!url) return;
    const controller = new AbortController();
    let active = true;
    setState({ url, status: 'loading', response: null });
    request(url, { signal: controller.signal }).then((response) => {
      if (active) setState({ url, status: 'success', response });
    }).catch((error) => {
      if (active && error.name !== 'AbortError') setState({ url, status: 'error', response: null, error });
    });
    return () => { active = false; controller.abort(); };
  }, [url, attempt]);
  const retry = useCallback(() => setAttempt((n) => n + 1), []);
  if (!url) return { status: 'idle', response: null, retry };
  return { ...(state.url === url ? state : { status: 'loading', response: null }), retry };
}
