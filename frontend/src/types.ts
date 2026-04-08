export type MetricCard = {
  label: string;
  value: string | number;
  delta?: string | null;
};

export type DistributionItem = {
  label: string;
  value: number;
};

export type TrendPoint = {
  time: string;
  effectiveness: number;
};

export type ViaStatusItem = {
  via: string;
  estado: string;
  cantidad: number;
};

export type DashboardRecord = {
  hora: string;
  via: string;
  patente: string;
  tag: string;
  forma_pago: string;
  categoria: string;
  sentido: string;
  transito: number;
  estado: string;
  violacion_via_abierta: boolean;
  descripcion_original: string;
};

export type ExemptRecord = {
  hora: string;
  via: string;
  patente: string;
  agrupacion: string;
  tipo: string;
  subtipo: string;
  detalle: string;
  documento: string;
  tag_ref: string;
  observacion: string;
};

export type DashboardResponse = {
  generated_at: string;
  file_name: string;
  total_records: number;
  filters: {
    vias: string[];
    sentidos: string[];
  };
  headline: string;
  highlights: string[];
  metrics: MetricCard[];
  status_distribution: DistributionItem[];
  payment_distribution: DistributionItem[];
  category_distribution: DistributionItem[];
  effectiveness_trend: TrendPoint[];
  status_by_via: ViaStatusItem[];
  records: DashboardRecord[];
  exempt_total: number;
  exempt_supervisor_total: number;
  exempt_classified: number;
  exempt_distribution: DistributionItem[];
  exempt_supervisor_distribution: DistributionItem[];
  exempt_records: ExemptRecord[];
};
