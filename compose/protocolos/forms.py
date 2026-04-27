# protocolos/forms.py
from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from .models import Protocolo, ProtocoloAnimal, Procedimiento, ProcedimientoBase, Analgesico, ProtocoloInvestigador, Institucion

# Campos del modelo Protocolo que quieres exponer en el form principal
WANTED_FIELDS = [
    "titulo",
    "instituciones",
    "inv_nombre", "inv_departamento", "inv_telefono", "inv_email",
    "justificacion", "justificacion_3r",
    "transporte",
    "tiempo_permanencia",
    "descripcion_procedimientos",
    "parametros_anestesia",
    "cuidados_pre_post",
    "punto_final_humano",
    "metodo_eutanasia",
    "riesgo_biologico", "nivel_absl",
    "destino_animales",
    "declaracion_buena_practica",
    # totales (si los carga el usuario; si los calculas server-side, quítalos)
    "n_grupos", "n_por_grupo", "n_total",
]

class ProtocoloForm(forms.ModelForm):
    
    instituciones = forms.ModelMultipleChoiceField(
        label="Instituciones donde se realizará el proyecto",
        queryset=Institucion.objects.filter(activo=True),
        required=False,
        widget=forms.SelectMultiple(
            attrs={"class": "form-select", "size": 4}
        ),
    )

    class Meta:
        model = Protocolo
        # solo campos "concretos" presentes en WANTED_FIELDS
        fields = WANTED_FIELDS
    
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Asigne un titulo al protocolo"}),
            "inv_nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre y apellido"}),
            "inv_departamento": forms.TextInput(attrs={"class": "form-control", "placeholder": "Departamento/Unidad"}),
            "inv_telefono": forms.TextInput(attrs={"class": "form-control", "placeholder": "Teléfono"}),
            "inv_email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "correo@dominio.com"}),

            "justificacion": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "justificacion_3r": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "transporte": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "tiempo_permanencia": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej. 8 semanas"}),
            "descripcion_procedimientos": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "parametros_anestesia": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "cuidados_pre_post": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "punto_final_humano": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "metodo_eutanasia": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "riesgo_biologico": forms.RadioSelect(choices=[(False, "No"), (True, "Sí")]),
            "nivel_absl": forms.TextInput(attrs={"class": "form-control", "placeholder": "ABSL-1/2/3"}),
            "destino_animales": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "declaracion_buena_practica": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "n_grupos": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "n_por_grupo": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "n_total": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        order = [name for name in WANTED_FIELDS if name in self.fields]
        self.order_fields(order)

        if "instituciones" in self.fields:
            self.fields["instituciones"].queryset = Institucion.objects.filter(activo=True)
            self.fields["instituciones"].widget.attrs.update(
                {"class": "form-select", "size": 4}
            )

class ProtocoloInvestigadorForm(forms.ModelForm):
    class Meta:
        model = ProtocoloInvestigador
        fields = ["nombre", "adscripcion", "rol", "correo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre y Apellido"}),
            "adscripcion": forms.TextInput(attrs={"class": "form-control", "placeholder": "Unidad/Departamento"}),
            "rol": forms.TextInput(attrs={"class": "form-control", "placeholder": "Rol (p.ej. Coinvestigador)"}),
            "correo": forms.EmailInput(attrs={"class": "form-control", "placeholder": "correo@dominio.com"}),
        }

ProtocoloInvestigadorFormSet = inlineformset_factory(
    Protocolo, ProtocoloInvestigador,
    form=ProtocoloInvestigadorForm,
    extra=1,           # agrega la fila en blanco por defecto
    can_delete=True
)

# ============== FORMSETS ==============

# (A) Animales por especie (por si alguna vista lo usa ahora o más adelante)
class ProtocoloAnimalForm(forms.ModelForm):
    class Meta:
        model = ProtocoloAnimal
        fields = ["especie", "cantidad", "rango_peso", "rango_edad", "sexo"]
        widgets = {
            "especie": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej. Rattus norvegicus"}),
            "cantidad": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
            "rango_peso": forms.TextInput(attrs={"class": "form-control"}),
            "rango_edad": forms.TextInput(attrs={"class": "form-control", "placeholder": "8–10 semanas"}),
            "sexo": forms.Select(attrs={"class": "form-select"}),
        }

ProtocoloAnimalFormSet = inlineformset_factory(
    Protocolo, ProtocoloAnimal,
    form=ProtocoloAnimalForm,
    extra=1, 
    can_delete=True
)
# ------------ Procedimientos -----------------


class ProcedimientoForm(forms.ModelForm):
    """
    Form para el inlineformset de Procedimiento.
    - 'nombre' viene de ProcedimientoBase (FK) y se envía oculto.
    - 'nombre_label' es solo para mostrar el texto en la plantilla.
    """
    nombre_label = ""  # se setea en __init__

    class Meta:
        model = Procedimiento
        fields = ["nombre", "aplica", "detalle"]
        widgets = {
            "nombre": forms.HiddenInput(),
            "aplica": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "detalle": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Vía, dosis, frecuencia, etc.",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        base_obj = None

        # 1) Si estamos editando y el Procedimiento ya existe
        if self.instance and self.instance.pk and self.instance.nombre_id:
            base_obj = self.instance.nombre

        # 2) Si es un formulario nuevo construido con initial
        elif "nombre" in self.initial:
            raw = self.initial["nombre"]
            # Puede venir como instancia o como PK
            if isinstance(raw, ProcedimientoBase):
                base_obj = raw
            else:
                try:
                    base_obj = ProcedimientoBase.objects.get(pk=raw)
                except ProcedimientoBase.DoesNotExist:
                    base_obj = None

        # 3) Último intento: si viene en self.data (por un POST)
        if not base_obj:
            raw_id = self.data.get(self.add_prefix("nombre"))
            if raw_id:
                try:
                    base_obj = ProcedimientoBase.objects.get(pk=raw_id)
                except ProcedimientoBase.DoesNotExist:
                    base_obj = None

        self.nombre_label = base_obj.nombre if base_obj else ""


class BaseProcedimientoFormSet(BaseInlineFormSet):
    """
    Formset personalizado para que:
    - En creación: muestre 1 form por cada ProcedimientoBase.
    - En edición: use el comportamiento normal (los procedimientos que ya tiene el protocolo).
    """

    def __init__(self, *args, **kwargs):
        # guardamos cuántos initial vienen (cuando se usa en la vista de creación)
        self._initial_len = len(kwargs.get("initial") or [])
        super().__init__(*args, **kwargs)

    def get_extra(self):
        # Si el protocolo ya existe (edición), dejamos el extra por defecto (0)
        if self.instance and self.instance.pk:
            return 0
        
        # En creación: si recibimos initial, usamos su longitud
        if self._initial_len:
            return self._initial_len

        # Fallback: cantidad de ProcedimientoBase en BD
        return ProcedimientoBase.objects.count()
# no existe datos en procedimientobase.
# PROC_BASE_COUNT = ProcedimientoBase.objects.count()

ProcedimientoFormSet = inlineformset_factory(
    Protocolo,
    Procedimiento,
    form=ProcedimientoForm,
    formset=BaseProcedimientoFormSet,
    # Cambia PROC_BASE_COUNT por 0 o un número fijo
    # Tu BaseProcedimientoFormSet ya se encarga de calcular el real después
    extra=0,          
    can_delete=True,
)

# ProcedimientoFormSet = inlineformset_factory(
#     Protocolo,
#     Procedimiento,
#     form=ProcedimientoForm,
#     formset=BaseProcedimientoFormSet,
#     extra=PROC_BASE_COUNT,          # el número real lo da BaseProcedimientoFormSet.get_extra()
#     can_delete=True,
# )

# (C) Analgésicos / Anestésicos / Tranquilizantes (punto 9)
class AnalgesicoForm(forms.ModelForm):
    class Meta:
        model = Analgesico
        fields = ["tipo", "agente", "dosis", "via", "frecuencia"]
        widgets = {
            "tipo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Analgésico / Anestésico / Tranquilizante"}),
            "agente": forms.TextInput(attrs={"class": "form-control"}),
            "dosis": forms.TextInput(attrs={"class": "form-control"}),
            "via": forms.TextInput(attrs={"class": "form-control", "placeholder": "Vía de administración"}),
            "frecuencia": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        cleaned = super().clean()

        # si todos los campos están vacíos no valida esta fila
        if not any(cleaned.values()):
            self.cleaned_data["DELETE"] = True  # descartar fila
        return cleaned
    
AnalgesicoFormSet = inlineformset_factory(
    Protocolo, Analgesico,
    form=AnalgesicoForm,
    extra=1, can_delete=True
)
