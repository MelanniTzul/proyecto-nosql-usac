import { createContext, useContext } from 'react';
import useApi from '../../hooks/useApi';
const CatalogContext = createContext(null);
export function CatalogProvider({ children }) {
  const query = useApi('/api/catalogos');
  return <CatalogContext.Provider value={query}>{children}</CatalogContext.Provider>;
}
export function useCatalogs() { return useContext(CatalogContext); }
