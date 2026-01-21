# protocolos/views.py
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404, render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, View, TemplateView, UpdateView
from django.db import transaction
from django.db.models import Q
from .models import Protocolo, ProcedimientoBase, Institucion
from .forms import (
    ProtocoloForm,
    ProcedimientoFormSet,
    AnalgesicoFormSet,
    ProtocoloInvestigadorFormSet,
    ProtocoloAnimalFormSet,
)

# ================== CONSTANTES ==================
PROTOCOLO_DETAIL_URL = "protocolos:detail"
PROTOCOLO_LIST_URL = "protocolos:list"


# ================== UTILIDAD ==================
def _es_admin(user):
    return user.is_superuser or user.groups.filter(name="Administrador").exists()


# ================== LISTADO ==================
class ProtocoloListView(LoginRequiredMixin, ListView):
    template_name = "protocolos/protocolo_list.html"
    context_object_name = "items"

    def get_queryset(self):
        qs = Protocolo.objects.all()
        user = self.request.user
        if _es_admin(user):
            # Admin ve:
            #  - todos los protocolos que él creó (cualquier estado)
            #  - y todos los protocolos que NO estén en borrador
            return qs.filter(
                Q(creado_por=user) | ~Q(estado="borrador")
            )
            
        return qs.filter(creado_por=user)


# ================== DETALLE ==================
class ProtocoloDetailView(LoginRequiredMixin, DetailView):
    model = Protocolo
    template_name = "protocolos/protocolo_detail.html"

    def get_queryset(self):
        qs = super().get_queryset()
        if _es_admin(self.request.user):
            return qs
        return qs.filter(creado_por=self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["es_admin"] = _es_admin(self.request.user)
        return ctx

# ================== CREACIÓN ==================
class ProtocoloCreateView(LoginRequiredMixin, CreateView):
    model = Protocolo
    form_class = ProtocoloForm
    template_name = "protocolos/protocolo_form.html"
    success_url = reverse_lazy(PROTOCOLO_LIST_URL)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        if self.request.POST:
            ctx["formset_invest"] = ProtocoloInvestigadorFormSet(
                self.request.POST, prefix="invest"
            )
            ctx["formset_animales"] = ProtocoloAnimalFormSet(
                self.request.POST, prefix="anim"
            )

            # Procedimientos base (no dinámico en el front)
            ctx["formset_proc"] = ProcedimientoFormSet(
                self.request.POST, prefix="proc"
            )

            ctx["formset_anlg"] = AnalgesicoFormSet(
                self.request.POST, prefix="anlg"
            )
        else:
            ctx["formset_invest"] = ProtocoloInvestigadorFormSet(prefix="invest")
            ctx["formset_animales"] = ProtocoloAnimalFormSet(prefix="anim")

            bases = list(ProcedimientoBase.objects.order_by("id"))
            initial_proc = [{"nombre": b.pk} for b in bases]
            ctx["formset_proc"] = ProcedimientoFormSet(
                prefix="proc",
                initial=initial_proc,
            )

            ctx["formset_anlg"] = AnalgesicoFormSet(prefix="anlg")

        return ctx

    @transaction.atomic
    def form_valid(self, form):
        """
        Guarda el protocolo y todos los formsets.
        Si algo falla en los formsets, se considera inválido.
        """
        ctx = self.get_context_data(form=form)
        fs_invest = ctx["formset_invest"]
        fs_anim = ctx["formset_animales"]
        fs_proc = ctx["formset_proc"]
        fs_anlg = ctx["formset_anlg"]

        # Validar TODO junto
        if not (fs_invest.is_valid() and fs_anim.is_valid()
                and fs_proc.is_valid() and fs_anlg.is_valid()):
            return self.form_invalid(form)

        # Guardar protocolo
        self.object = form.save(commit=False)
        self.object.creado_por = self.request.user
        self.object.save()

        form.save_m2m()

        # Asociar formsets al protocolo y guardar
        for fs in (fs_invest, fs_anim, fs_proc, fs_anlg):
            fs.instance = self.object
            fs.save()

        messages.success(
            self.request,
            "Borrador creado. Complete las secciones y envíe para evaluación.",
        )
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        """
        Vuelve a pintar el formulario con los formsets y permite ver errores.
        """
        ctx = self.get_context_data(form=form)

        
        return self.render_to_response(ctx)


# ================== EDICIÓN (GET) ==================
@login_required
@require_http_methods(["GET"])
def protocolo_edit(request, pk):
    """
    GET: renderiza el formulario de edición (solo lectura).
    """
    protocolo = get_object_or_404(Protocolo, pk=pk)

    if protocolo.estado in ("enviado", "aprobado"):
        messages.error(
            request,
            "No se puede editar un protocolo enviado o aprobado. "
            "Debe ser rechazado para poder modificarlo."
        )
        return redirect(PROTOCOLO_DETAIL_URL, pk=protocolo.pk)

    if not (_es_admin(request.user) or protocolo.creado_por_id == request.user.id):
        messages.error(request, "No tiene permisos para editar este protocolo.")
        return redirect(PROTOCOLO_LIST_URL)

    form = ProtocoloForm(instance=protocolo)
    fs_invest = ProtocoloInvestigadorFormSet(instance=protocolo, prefix="invest")
    fs_proc = ProcedimientoFormSet(instance=protocolo, prefix="proc")
    fs_anlg = AnalgesicoFormSet(instance=protocolo, prefix="anlg")
    fs_anim = ProtocoloAnimalFormSet(instance=protocolo, prefix="anim")

    return render(
        request,
        "protocolos/protocolo_formsets.html",
        {
            "form": form,
            "fs_invest": fs_invest,
            "fs_proc": fs_proc,
            "fs_anlg": fs_anlg,
            "fs_anim": fs_anim,
            "obj": protocolo,
        },
    )


# ================== EDICIÓN (POST) ==================
@login_required
@csrf_protect
@require_http_methods(["POST"])
def protocolo_edit_save(request, pk):
    """
    POST: valida y guarda cambios del protocolo (operación no segura).
    """
    protocolo = get_object_or_404(Protocolo, pk=pk)

    if protocolo.estado in ("enviado", "aprobado"):
        messages.error(
            request,
            "No se puede editar un protocolo enviado o aprobado. "
            "Debe ser rechazado para poder modificarlo."
        )
        return redirect(PROTOCOLO_DETAIL_URL, pk=protocolo.pk)

    if not (_es_admin(request.user) or protocolo.creado_por_id == request.user.id):
        messages.error(request, "No tiene permisos para editar este protocolo.")
        return redirect(PROTOCOLO_LIST_URL)

    form = ProtocoloForm(request.POST, instance=protocolo)
    fs_invest = ProtocoloInvestigadorFormSet(request.POST, instance=protocolo, prefix="invest")
    fs_proc = ProcedimientoFormSet(request.POST, instance=protocolo, prefix="proc")
    fs_anlg = AnalgesicoFormSet(request.POST, instance=protocolo, prefix="anlg")
    fs_anim = ProtocoloAnimalFormSet(request.POST, instance=protocolo, prefix="anim")

    if form.is_valid() and fs_invest.is_valid() and fs_proc.is_valid() and fs_anlg.is_valid() and fs_anim.is_valid():
        try:
            with transaction.atomic():
                obj = form.save()
                fs_invest.save()
                fs_proc.save()
                fs_anlg.save()
                fs_anim.save()
            messages.success(request, "Protocolo actualizado correctamente.")
            return redirect(PROTOCOLO_DETAIL_URL, pk=obj.pk)
        except Exception:
            messages.error(request, "Ocurrió un error al guardar. Intente nuevamente.")

    # Si hay errores, re-render del mismo template con errores
    return render(
        request,
        "protocolos/protocolo_formsets.html",
        {
            "form": form,
            "fs_invest": fs_invest,
            "fs_proc": fs_proc,
            "fs_anlg": fs_anlg,
            "fs_anim": fs_anim,
            "obj": protocolo,
        },
    )



# ================== ENVÍO ==================
class ProtocoloEnviarView(LoginRequiredMixin, View):
    """Cambia estado a 'enviado'."""

    def post(self, request, pk):
        obj = get_object_or_404(Protocolo, pk=pk)
        if obj.creado_por_id != request.user.id and not _es_admin(request.user):
            messages.error(request, "No puede enviar este protocolo.")
        else:
            obj.estado = "enviado"
            obj.save(update_fields=["estado"])
            messages.success(request, "Protocolo enviado a evaluación.")
        return redirect(PROTOCOLO_DETAIL_URL, pk=pk)


# ================== CAMBIO DE ESTADO ==================
class ProtocoloCambiarEstadoView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Solo administradores: aprobar / rechazar."""

    def test_func(self):
        return _es_admin(self.request.user)

    def post(self, request, pk):
        obj = get_object_or_404(Protocolo, pk=pk)
        accion = request.POST.get("accion")

        if accion == "aprobar":
            obj.estado = "aprobado"
            obj.observacion_rechazo = ""   # limpiar observación previa
            obj.save(update_fields=["estado", "observacion_rechazo"])
            messages.success(request, "Protocolo aprobado correctamente.")

        elif accion == "rechazar":
            obs = request.POST.get("observacion_rechazo", "").strip()
            if not obs:
                messages.error(request, "Debe indicar un motivo para rechazar el protocolo.")
                return redirect(PROTOCOLO_DETAIL_URL, pk=pk)
           
            obj.estado = "rechazado"
            obj.observacion_rechazo = obs
            obj.save(update_fields=["estado", "observacion_rechazo"])
            messages.success(request, "Protocolo rechazado.")

        else:
            messages.error(request, "Acción no válida.")

        return redirect(PROTOCOLO_DETAIL_URL, pk=pk)

# ================== CONFIGURA ITEMS DE PROTOCOLO ==================
class ConfiguracionProtocolosView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = "protocolos/configuracion.html"

    def test_func(self):
        """Solo superusuarios o miembros del grupo Administrador."""
        user = self.request.user
        return user.is_superuser or user.groups.filter(name="Administrador").exists()
    

class AdminOnlyMixin(UserPassesTestMixin):
    """
    Mixin para restringir vistas solo a superusuarios o grupo 'Administrador'.
    Usar junto con LoginRequiredMixin.
    """
    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.groups.filter(name="Administrador").exists()


class InstitucionListView(LoginRequiredMixin, AdminOnlyMixin, ListView):
    model = Institucion
    template_name = "protocolos/institucion_list.html"
    context_object_name = "items"


class InstitucionCreateView(LoginRequiredMixin, AdminOnlyMixin, CreateView):
    model = Institucion
    template_name = "protocolos/institucion_form.html"
    fields = ["nombre", "activo"]
    success_url = reverse_lazy("protocolos:instituciones_list")

    def form_valid(self, form):
        messages.success(self.request, "Institución creada correctamente.")
        return super().form_valid(form)


class InstitucionUpdateView(LoginRequiredMixin, AdminOnlyMixin, UpdateView):
    model = Institucion
    template_name = "protocolos/institucion_form.html"
    fields = ["nombre", "activo"]
    success_url = reverse_lazy("protocolos:instituciones_list")

    def form_valid(self, form):
        messages.success(self.request, "Institución actualizada correctamente.")
        return super().form_valid(form)


class ProcedimientoBaseListView(LoginRequiredMixin, AdminOnlyMixin, ListView):
    model = ProcedimientoBase
    template_name = "protocolos/procedimientobase_list.html"
    context_object_name = "items"


class ProcedimientoBaseCreateView(LoginRequiredMixin, AdminOnlyMixin, CreateView):
    model = ProcedimientoBase
    template_name = "protocolos/procedimientobase_form.html"
    fields = ["nombre"]
    success_url = reverse_lazy("protocolos:procedimientos_list")

    def form_valid(self, form):
        messages.success(self.request, "Procedimiento base creado correctamente.")
        return super().form_valid(form)


class ProcedimientoBaseUpdateView(LoginRequiredMixin, AdminOnlyMixin, UpdateView):
    model = ProcedimientoBase
    template_name = "protocolos/procedimientobase_form.html"
    fields = ["nombre"]
    success_url = reverse_lazy("protocolos:procedimientos_list")

    def form_valid(self, form):
        messages.success(self.request, "Procedimiento base actualizado correctamente.")
        return super().form_valid(form)


# ================== IMPRIMIR PROTOCOLO ==================
class ProtocoloPrintView(LoginRequiredMixin, DetailView):
    """
    Vista de solo lectura para generar una versión imprimible
    del protocolo (ideal para imprimir o guardar como PDF).
    """
    model = Protocolo
    template_name = "protocolos/protocolo_print.html"

    def get_queryset(self):
        qs = super().get_queryset()
        # Mismos permisos que en detalle: admin ve todo, usuario solo lo suyo
        if _es_admin(self.request.user):
            return qs
        return qs.filter(creado_por=self.request.user)
