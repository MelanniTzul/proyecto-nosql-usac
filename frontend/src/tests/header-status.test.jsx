import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Routes, Route } from 'react-router';
import AppShell from '../components/layout/AppShell';

const success = () => ({ ok: true, json: async () => ({ status: 'ok', mongodb: { status: 'ok' }, neo4j: { status: 'ok' } }) });
function mount() {
  render(<MemoryRouter><Routes><Route element={<AppShell/>}><Route index element={<p>Datos existentes</p>}/></Route></Routes></MemoryRouter>);
}

describe('Comprobación de estado del encabezado', () => {
  it('comprueba solo conexiones, muestra carga y confirma sin recargar los datos', async () => {
    let finish;
    const fetch = vi.fn().mockResolvedValueOnce(success()).mockImplementationOnce(() => new Promise((resolve) => { finish = resolve; }));
    vi.stubGlobal('fetch', fetch);
    mount();
    await screen.findByText('Sistema disponible');
    const button = screen.getByRole('button', { name: 'Comprobar conexión' });
    expect(button).toHaveTextContent('Comprobar conexión');
    expect(button).toHaveAccessibleDescription('Comprueba el estado de las conexiones. No actualiza los datos de las pantallas.');
    await userEvent.click(button);
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute('aria-busy', 'true');
    expect(screen.getByText('Comprobando estado…')).toBeVisible();
    expect(screen.queryByText('Estado actualizado')).not.toBeInTheDocument();
    finish(success());
    await screen.findByText('Estado actualizado');
    expect(button).toBeEnabled();
    expect(screen.getByText('Datos existentes')).toBeVisible();
    expect(fetch.mock.calls.map(([url]) => url)).toEqual(['/api/health/databases', '/api/health/databases']);
  });
  it('informa un fallo y permite volver a comprobar el estado', async () => {
    const fetch = vi.fn().mockResolvedValueOnce(success()).mockRejectedValueOnce(new TypeError('network unavailable')).mockResolvedValueOnce(success());
    vi.stubGlobal('fetch', fetch);
    mount();
    await screen.findByText('Sistema disponible');
    const button = screen.getByRole('button', { name: 'Comprobar conexión' });
    await userEvent.click(button);
    expect(await screen.findByText('No se pudo comprobar el estado. Intenta nuevamente.')).toBeVisible();
    expect(screen.getByText('Servicio no disponible')).toBeVisible();
    await userEvent.click(button);
    await waitFor(() => expect(screen.getByText('Estado actualizado')).toBeVisible());
    expect(screen.getByText('Sistema disponible')).toBeVisible();
    expect(fetch).toHaveBeenCalledTimes(3);
  });
});
