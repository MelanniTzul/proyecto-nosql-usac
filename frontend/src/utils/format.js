export const number = (value) => value == null ? '—' : new Intl.NumberFormat('es-GT').format(value);
export const percent = (value) => value == null ? 'Sin datos' : `${new Intl.NumberFormat('es-GT', { maximumFractionDigits: 2 }).format(value)}%`;
export const careerName = (row) => `${row.carrera || 'Sin información'}${row.estado === 'recortada' ? ' · texto recortado' : ''}`;
export const resultName = (value) => value ? 'Aprobado' : 'No aprobado';
