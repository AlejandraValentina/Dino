"""Datos del proyecto, independientes de la interfaz."""

from dataclasses import asdict, dataclass
from decimal import Decimal, localcontext
import math
import re


class ProjectError(ValueError):
    """Datos o archivo de proyecto que no se pueden utilizar."""


NUMERIC_FIELDS = {
    "cylinder_count": "Número de cilindros",
    "bore_mm": "Diámetro del cilindro",
    "stroke_mm": "Carrera",
    "rod_length_mm": "Longitud de biela entre centros",
    "compression_ratio": "Relación de compresión geométrica",
}


PORT_FIELDS = {"top_mm": "Distancia al borde superior", "height_mm": "Altura de ventana",
               "width_mm": "Ancho desarrollado"}
NUMBER_LABELS = {**NUMERIC_FIELDS, **PORT_FIELDS,
                 "crankcase_volume_bdc_cm3": "Volumen libre del cárter en PMI"}
TWO_STROKE_REFERENCE = "rectangular-peripheral-tdc-developed-bdc-v1"


def validate_number(value: object, field: str) -> None:
    if value is None:
        return
    label = NUMBER_LABELS[field]
    if field == "cylinder_count":
        if type(value) is not int or value <= 0:
            raise ProjectError(f"{label}: debe ser un entero positivo.")
        return
    try:
        valid = type(value) in (int, float) and math.isfinite(value)
    except OverflowError:
        valid = False
    minimum = 1 if field == "compression_ratio" else 0
    if not valid or value <= minimum:
        raise ProjectError(f"{label}: debe ser un número finito mayor que {minimum}.")


def parse_number(text: str, field: str) -> int | float | None:
    """Vacío es ausencia; cualquier otro texto se valida sin corregirlo."""
    text = text.strip()
    if not text:
        return None
    pattern = (r"\+?[0-9]+" if field == "cylinder_count" else
               r"[+-]?(?:[0-9]+(?:[.,][0-9]*)?|[.,][0-9]+)(?:[eE][+-]?[0-9]+)?")
    if not re.fullmatch(pattern, text):
        raise ProjectError(f"{NUMBER_LABELS[field]}: número inválido; no uses separadores de miles.")
    try:
        value = int(text) if re.fullmatch(r"[+-]?[0-9]+", text) else float(text.replace(",", "."))
    except ValueError as exc:
        raise ProjectError(f"{NUMBER_LABELS[field]}: número fuera del rango admitido.") from exc
    validate_number(value, field)
    return value


def displacements(bore: object, stroke: object, cylinders: object) -> tuple[Decimal | None, Decimal | None]:
    """cm³; cada resultado depende solo de sus entradas. Sin desbordar float."""
    try:
        validate_number(bore, "bore_mm")
        validate_number(stroke, "stroke_mm")
    except ProjectError:
        return None, None
    if bore is None or stroke is None:
        return None, None
    with localcontext() as context:
        context.prec = 40
        per_cylinder = Decimal(str(math.pi)) * Decimal(str(bore)) ** 2 * Decimal(str(stroke)) / 4000
        try:
            validate_number(cylinders, "cylinder_count")
        except ProjectError:
            return per_cylinder, None
        total = per_cylinder * cylinders if cylinders is not None else None
    return per_cylinder, total


@dataclass(frozen=True)
class Port:
    name: str = ""
    function: str | None = None
    top_mm: float | None = None
    height_mm: float | None = None
    width_mm: float | None = None

    def validate(self):
        if not isinstance(self.name, str):
            raise ProjectError("El nombre de lumbrera debe ser texto.")
        if self.function is not None and self.function not in ("escape", "transfer"):
            raise ProjectError("Función de lumbrera inválida: Escape o Transferencia.")
        for field in PORT_FIELDS:
            validate_number(getattr(self, field), field)

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or not cls.__dataclass_fields__.keys() <= data.keys():
            raise ProjectError("Faltan campos de la lumbrera.")
        port = cls(**{key: data[key] for key in cls.__dataclass_fields__})
        port.validate()
        return port


@dataclass(frozen=True)
class Project:
    name: str = "Sin título"
    cycle: str = "2T"
    manufacturer: str = ""
    model: str = ""
    cylinder_count: int | None = None
    bore_mm: float | None = None
    stroke_mm: float | None = None
    rod_length_mm: float | None = None
    compression_ratio: float | None = None
    notes: str = ""
    ports: tuple[Port, ...] = ()
    crankcase_volume_bdc_cm3: float | None = None

    def validate(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ProjectError("El nombre debe ser texto y no puede estar vacío ni contener solo espacios.")
        if not isinstance(self.cycle, str) or self.cycle not in ("2T", "4T"):
            raise ProjectError("El tipo de motor debe ser 2T o 4T.")
        for field in ("manufacturer", "model", "notes"):
            if not isinstance(getattr(self, field), str):
                raise ProjectError(f"{field}: debe ser texto, aunque esté vacío.")
        for field in NUMERIC_FIELDS:
            validate_number(getattr(self, field), field)

        validate_number(self.crankcase_volume_bdc_cm3, "crankcase_volume_bdc_cm3")
        if not isinstance(self.ports, tuple) or any(not isinstance(port, Port) for port in self.ports):
            raise ProjectError("La colección de lumbreras es inválida.")
        for port in self.ports:
            port.validate()

    def to_dict(self) -> dict:
        self.validate()
        return {"format_version": 3, **asdict(self), "ports": [asdict(port) for port in self.ports],
                "two_stroke_reference": TWO_STROKE_REFERENCE}

    @classmethod
    def from_dict(cls, data: object) -> "Project":
        if not isinstance(data, dict):
            raise ProjectError("El archivo debe contener un objeto JSON.")
        if not {"format_version", "name", "cycle"} <= data.keys():
            raise ProjectError("Faltan campos obligatorios: format_version, name o cycle.")
        version = data["format_version"]
        if type(version) is not int or version not in (1, 2, 3):
            raise ProjectError("La versión del archivo debe ser el entero 1, 2 o 3.")
        if version == 1:
            project = cls(data["name"], data["cycle"])
        else:
            fields = set(cls.__dataclass_fields__)
            if version == 2:
                fields -= {"ports", "crankcase_volume_bdc_cm3"}
            if not fields <= data.keys():
                raise ProjectError(f"Faltan campos obligatorios de la ficha versión {version}.")
            values = {field: data[field] for field in fields}
            if version == 3:
                if data.get("two_stroke_reference") != TWO_STROKE_REFERENCE:
                    raise ProjectError("Referencia de geometría 2T no admitida.")
                if not isinstance(data["ports"], list):
                    raise ProjectError("Las lumbreras deben ser una lista.")
                values["ports"] = tuple(Port.from_dict(port) for port in data["ports"])
            project = cls(**values)
        project.validate()
        return project
