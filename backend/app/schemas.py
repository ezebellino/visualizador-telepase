from pydantic import BaseModel, Field


class MetricCard(BaseModel):
    label: str
    value: str | int | float
    delta: str | None = None


class DistributionItem(BaseModel):
    label: str
    value: int


class TrendPoint(BaseModel):
    time: str
    effectiveness: float


class ViaStatusItem(BaseModel):
    via: str
    estado: str
    cantidad: int


class DashboardRecord(BaseModel):
    hora: str
    via: str
    patente: str
    tag: str
    forma_pago: str
    categoria: str
    sentido: str
    transito: int
    estado: str
    violacion_via_abierta: bool
    descripcion_original: str


class ExemptRecord(BaseModel):
    hora: str
    via: str
    patente: str
    agrupacion: str
    tipo: str
    subtipo: str
    detalle: str
    documento: str
    tag_ref: str
    observacion: str


class FilterOptions(BaseModel):
    vias: list[str] = Field(default_factory=list)
    sentidos: list[str] = Field(default_factory=list)


class DashboardResponse(BaseModel):
    generated_at: str
    file_name: str
    total_records: int
    filters: FilterOptions
    headline: str
    highlights: list[str]
    metrics: list[MetricCard]
    status_distribution: list[DistributionItem]
    payment_distribution: list[DistributionItem]
    category_distribution: list[DistributionItem]
    effectiveness_trend: list[TrendPoint]
    status_by_via: list[ViaStatusItem]
    records: list[DashboardRecord]
    exempt_total: int
    exempt_supervisor_total: int
    exempt_classified: int
    exempt_distribution: list[DistributionItem]
    exempt_supervisor_distribution: list[DistributionItem]
    exempt_records: list[ExemptRecord]
