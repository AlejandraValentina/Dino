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


def validate_number(value: object, field: str) -> None:
    if value is None:
        return
    label = NUMERIC_FIELDS[field]
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
        raise ProjectError(f"{NUMERIC_FIELDS[field]}: número inválido; no uses separadores de miles.")
    try:
        value = int(text) if field == "cylinder_count" else float(text.replace(",", "."))
    except ValueError as exc:
        raise ProjectError(f"{NUMERIC_FIELDS[field]}: número fuera del rango admitido.") from exc
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

    def to_dict(self) -> dict:
        self.validate()
        return {"format_version": 2, **asdict(self)}

    @classmethod
    def from_dict(cls, data: object) -> "Project":
        if not isinstance(data, dict):
            raise ProjectError("El archivo debe contener un objeto JSON.")
        if not {"format_version", "name", "cycle"} <= data.keys():
            raise ProjectError("Faltan campos obligatorios: format_version, name o cycle.")
        version = data["format_version"]
        if type(version) is not int or version not in (1, 2):
            raise ProjectError("La versión del archivo debe ser el entero 1 o 2.")
        if version == 1:
            project = cls(data["name"], data["cycle"])
        else:
            fields = cls.__dataclass_fields__
            if not fields.keys() <= data.keys():
                raise ProjectError("Faltan campos obligatorios de la ficha de motor versión 2.")
            project = cls(**{field: data[field] for field in fields})
        project.validate()
        return project
