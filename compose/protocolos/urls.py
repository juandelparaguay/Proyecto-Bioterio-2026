from django.urls import path
from .views import (
    ProtocoloListView, ProtocoloDetailView, ProtocoloCreateView,
    protocolo_edit, protocolo_edit_save, ProtocoloEnviarView, ProtocoloCambiarEstadoView,
    ConfiguracionProtocolosView, InstitucionListView, InstitucionCreateView,
    InstitucionUpdateView, ProcedimientoBaseListView, ProcedimientoBaseCreateView,
    ProcedimientoBaseUpdateView, ProtocoloPrintView
)

app_name = "protocolos"

urlpatterns = [
    path("", ProtocoloListView.as_view(), name="list"),
    path("nuevo/", ProtocoloCreateView.as_view(), name="new"),
    path("<int:pk>/", ProtocoloDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", protocolo_edit, name="edit"),               
    path("<int:pk>/edit/save/", protocolo_edit_save, name="edit_save"),
    path("<int:pk>/enviar/", ProtocoloEnviarView.as_view(), name="send"),
    path("<int:pk>/estado/", ProtocoloCambiarEstadoView.as_view(), name="estado"),
    path("<int:pk>/imprimir/", ProtocoloPrintView.as_view(), name="print"),
    path("config/", ConfiguracionProtocolosView.as_view(), name="config"),
    path("config/instituciones/", InstitucionListView.as_view(), name="instituciones_list"),
    path("config/instituciones/nueva/", InstitucionCreateView.as_view(), name="instituciones_new"),
    path("config/instituciones/<int:pk>/editar/", InstitucionUpdateView.as_view(), name="instituciones_edit"),
    path("config/procedimientos/", ProcedimientoBaseListView.as_view(), name="procedimientos_list"),
    path("config/procedimientos/nuevo/", ProcedimientoBaseCreateView.as_view(), name="procedimientos_new"),
    path("config/procedimientos/<int:pk>/editar/", ProcedimientoBaseUpdateView.as_view(), name="procedimientos_edit"),
]
