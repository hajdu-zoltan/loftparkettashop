from django.urls import path
from draw import views as draw_views

app_name = 'draw'

urlpatterns = [
    # wheel_page URL, amely nem tartalmaz UUID-t
    path('<str:link>/', draw_views.wheel_page, name='wheel_page'),  # link a családnévhez
    # spin_wheel URL, amely UUID-t tartalmaz
    path('spin/<uuid:link>/', draw_views.spin_wheel, name='spin_wheel'),  # sorsolás
    path('result/<uuid:link>/<str:drawn_family_name>/', draw_views.result_page, name='result_page'),
]