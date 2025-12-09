import pytest
import tkinter as tk
from unittest.mock import MagicMock

# Importamos las clases necesarias de tu aplicación
from app_licitaciones import AppLicitacionesGUI, Licitacion, Lote
from logic_licitaciones import DatabaseManager

# --- Entorno de Prueba (Fixture de Pytest) ---
# Esta función especial se ejecuta antes de cada prueba.
# Crea una base de datos en memoria para no tocar tu archivo real.
# --- Entorno de Prueba (Fixture de Pytest) ---
@pytest.fixture
def app():
    """Crea una instancia de la app con una base de datos en memoria para las pruebas."""
    db_test = DatabaseManager(":memory:")
    app_instance = AppLicitacionesGUI(db_path=":memory:")
    app_instance.db = db_test
    
    # Ocultamos la ventana principal para que no bloquee la ejecución de pytest.
    app_instance.withdraw()
    
    # --- LÍNEA CLAVE AÑADIDA ---
    # Forzamos a Tkinter a procesar la orden de ocultar la ventana inmediatamente.
    # Esto evita que la ventana se dibuje y bloquee el test runner.
    app_instance.update()
    # --- FIN DE LA LÍNEA AÑADIDA ---
    
    # Creamos una licitación de prueba para trabajar con ella
    test_lic = Licitacion(
        id=1,
        numero_proceso="TEST-001",
        nombre_proceso="Licitacion de Prueba para GUI",
        institucion="PRUEBA",
        empresas_nuestras=[{'nombre': 'Nuestra Empresa Test'}]
    )
    app_instance.gestor_licitaciones.append(test_lic)
    app_instance.actualizar_tabla_gui()

    yield app_instance # La prueba se ejecuta aquí

    app_instance.destroy() # Se destruye la ventana al finalizar

# --- Nuestra Primera Prueba de GUI ---

def test_agregar_y_eliminar_lote_en_detalles(app, mocker):
    """
    Prueba el flujo completo de agregar y luego eliminar un lote en VentanaDetalles.
    """
    print("\n--- INICIO: Test de Agregar/Eliminar Lote ---")
    
    # 1. PREPARAR (Arrange)
    # ---------------------
    # Seleccionamos la primera (y única) licitación en la tabla principal
    app.tree.selection_set(app.tree.get_children()[0])
    
    # Abrimos la ventana de detalles para esa licitación
    app.abrir_ventana_detalles()
    
    # Pytest no muestra las ventanas, así que accedemos a la ventana de detalles
    # que acaba de ser creada. tk.Toplevel() la hace hija de la ventana principal.
    ventana_detalles = app.winfo_children()[-1]
    
    # Verificamos que inicialmente no hay lotes
    assert len(ventana_detalles.licitacion.lotes) == 0, "La licitación no debería tener lotes al empezar la prueba."
    print("-> Verificado: La licitación inicia con 0 lotes.")

    # 2. ACTUAR (Act) - Simular la adición de un lote
    # ---------------------------------------------
    # Simulamos que el usuario llena el diálogo "DialogoGestionarLote".
    # `mocker.patch` reemplaza la ventana de diálogo con un objeto que devuelve
    # un resultado predecible, sin necesidad de interacción manual.
    datos_lote_nuevo = Lote(numero="101", nombre="Lote de Prueba", monto_base=5000)
    mocker.patch('app_gui.DialogoGestionarLote', return_value=MagicMock(result=datos_lote_nuevo))
    
    # Llamamos a la función que el botón "Agregar Lote" ejecutaría
    ventana_detalles.agregar_lote()
    print("-> Acción: Se simuló agregar el lote '101'.")

    # 3. VERIFICAR (Assert) - Comprobar que el lote se añadió
    # --------------------------------------------------------
    assert len(ventana_detalles.licitacion.lotes) == 1, "Debería haber 1 lote en la licitación después de agregar."
    assert ventana_detalles.licitacion.lotes[0].nombre == "Lote de Prueba", "El nombre del lote agregado no es correcto."
    print("-> Verificado: El lote se agregó correctamente a la licitación en memoria.")
    
    # 4. ACTUAR (Act) - Simular la eliminación del lote
    # ------------------------------------------------
    # Seleccionamos el lote que acabamos de agregar en la tabla de lotes
    ventana_detalles.tree_lotes.selection_set(ventana_detalles.tree_lotes.get_children()[0])
    
    # Simulamos que el usuario confirma la eliminación en el messagebox
    mocker.patch('tkinter.messagebox.askyesno', return_value=True)
    
    # Llamamos a la función del botón "Eliminar Lote"
    ventana_detalles.eliminar_lote()
    print("-> Acción: Se simuló eliminar el lote '101'.")
    
    # 5. VERIFICAR (Assert) - Comprobar que el lote se eliminó
    # ------------------------------------------------------
    assert len(ventana_detalles.licitacion.lotes) == 0, "El lote debería haber sido eliminado."
    print("-> Verificado: El lote se eliminó correctamente.")
    print("--- FIN: Test de Agregar/Eliminar Lote (ÉXITO) ---")

def test_agregar_competidor_al_catalogo(app, mocker):
    """
    Prueba que se pueda agregar un nuevo competidor a la lista temporal
    de la ventana de gestión de catálogos.
    """
    print("\n--- INICIO: Test de Agregar Competidor al Catálogo ---")

    # 1. PREPARAR (Arrange)
    # ---------------------
    # Abrimos la ventana de gestión de competidores
    app.abrir_ventana_maestro_competidores()
    ventana_maestros = app.winfo_children()[-1]
    
    # Verificamos el estado inicial: la lista de competidores en la ventana debe estar vacía
    assert len(ventana_maestros.competidores_copia) == 0, "La lista de competidores debería estar vacía al inicio."
    print("-> Verificado: El catálogo de competidores inicia vacío.")

    # 2. ACTUAR (Act)
    # ----------------
    # Simulamos que el usuario introduce los datos de un nuevo competidor en el diálogo.
    datos_nuevo_competidor = {'nombre': 'Competidor Sigma', 'rnc': '131-00000-1', 'rpe': 'RPE-TEST', 'representante': 'Juan Tester'}
    mocker.patch('app_gui.DialogoGestionarEntidad', return_value=MagicMock(result=datos_nuevo_competidor))
    
    # Llamamos a la función del botón "Agregar"
    ventana_maestros.agregar()
    print("-> Acción: Se simuló agregar al 'Competidor Sigma'.")

    # 3. VERIFICAR (Assert)
    # ---------------------
    # Comprobamos que la lista *temporal* de la ventana ahora contiene al nuevo competidor.
    assert len(ventana_maestros.competidores_copia) == 1, "La lista temporal debería tener 1 competidor."
    assert ventana_maestros.competidores_copia[0]['nombre'] == 'Competidor Sigma', "El nombre del competidor no coincide."
    # La lista principal de la app aún no debe haberse modificado.
    assert len(app.competidores_maestros) == 0, "La lista maestra de la app no debe cambiar hasta guardar."
    print("-> Verificado: El competidor se añadió a la lista temporal de la ventana correctamente.")
    print("--- FIN: Test de Agregar Competidor al Catálogo (ÉXITO) ---")


def test_guardar_catalogo_competidores(app, mocker):
    """
    Prueba que los cambios hechos en el catálogo se guarden en la aplicación
    principal al presionar "Guardar y Cerrar".
    """
    print("\n--- INICIO: Test de Guardado de Catálogo ---")

    # 1. PREPARAR (Arrange)
    # ---------------------
    app.abrir_ventana_maestro_competidores()
    ventana_maestros = app.winfo_children()[-1]
    
    # Añadimos un competidor a la lista temporal (reutilizando la lógica anterior)
    datos_nuevo_competidor = {'nombre': 'Competidor Omega', 'rnc': '132-00000-2'}
    mocker.patch('app_gui.DialogoGestionarEntidad', return_value=MagicMock(result=datos_nuevo_competidor))
    ventana_maestros.agregar()
    
    # Verificación intermedia: la lista principal de la app sigue vacía.
    assert len(app.competidores_maestros) == 0, "La lista maestra no debe cambiar antes de guardar."
    print("-> Verificado: La lista maestra de la app aún está vacía.")

    # 2. ACTUAR (Act)
    # ----------------
    # Llamamos a la función del botón "Guardar y Cerrar".
    # Esta función es la que debe transferir los datos a la app principal.
    ventana_maestros.cerrar_y_guardar()
    print("-> Acción: Se simuló 'Guardar y Cerrar'.")

    # 3. VERIFICAR (Assert)
    # ---------------------
    # Ahora sí, la lista maestra de la aplicación principal debe contener al nuevo competidor.
    assert len(app.competidores_maestros) == 1, "La lista maestra debería tener 1 competidor después de guardar."
    assert app.competidores_maestros[0]['nombre'] == 'Competidor Omega', "El nombre del competidor guardado no coincide."
    print("-> Verificado: La lista maestra de la app se actualizó correctamente.")
    print("--- FIN: Test de Guardado de Catálogo (ÉXITO) ---")