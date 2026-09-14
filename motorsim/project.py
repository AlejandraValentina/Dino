"""Datos del proyecto, independientes de la interfaz."""

from dataclasses import dataclass


class ProjectError(ValueError):
    """Datos o archivo de proyecto que no se pueden utilizar."""


@dataclass(frozen=True)
class Project:
    name: str = "Sin título"
    cycle: str = "2T"

    def validate(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ProjectError("El nombre debe ser texto y no puede estar vacío ni contener solo espacios.")
        if not isinstance(self.cycle, str) or self.cycle not in ("2T", "4T"):
            raise ProjectError("El tipo de motor debe ser 2T o 4T.")

    def to_dict(self) -> dict:
        self.validate()
        return {"format_version": 1, "name": self.name, "cycle": self.cycle}

    @classmethod
    def from_dict(cls, data: object) -> "Project":
        if not isinstance(data, dict):
            raise ProjectError("El archivo debe contener un objeto JSON.")
        if not {"format_version", "name", "cycle"} <= data.keys():
            raise ProjectError("Faltan campos obligatorios: format_version, name o cycle.")
        if type(data["format_version"]) is not int or data["format_version"] != 1:
            raise ProjectError("La versión del archivo debe ser el entero 1.")
        project = cls(data["name"], data["cycle"])
        project.validate()
        return project
