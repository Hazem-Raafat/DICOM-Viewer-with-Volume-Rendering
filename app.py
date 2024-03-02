import sys
import vtk
from PyQt5.QtWidgets import  QFileDialog
from PyQt5.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5 import  uic
from PyQt5 import QtWidgets
import qdarkstyle
from PyQt5.QtGui import QIcon

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.init_ui()

###############################################################################################
#                                   UI Initialization                                         #
###############################################################################################

    def init_ui(self):
        """
        Initializes the user interface.

        This function loads the UI from the 'mainwindow2.ui' file and sets up the necessary variables and connections.
        It sets the window title to "DICOM Viewer with Volume Rendering".
        It creates a VTK render window and sets it as the widget for rendering.
        It connects the 'loadButton' and 'renderButton' signals to their respective slots.
        It sets the minimum and maximum values for the 'iso_slider' and connects its valueChanged signal to the 'update_iso_value' slot.
        It sets up the VTK renderer and adds it to the render window.
        It sets the default rendering method to surface rendering and enables real-time rendering.
        It shows the UI in full screen mode.
        It overrides the keyPressEvent to handle keyboard events.
        It shows the surface rendering widgets by default.
        """

        self.ui = uic.loadUi('mainwindow.ui', self)
        self.setWindowTitle("DICOM Viewer")
        self.setWindowIcon(QIcon("icons\\skull.png"))
        # Initialize variables
        self.reader = None
        self.mapper = None
        self.actor = None
        self.iso_value = 50 
        
        
        # Create VTK render window
        self.vtk_widget = QVTKRenderWindowInteractor(self.ui.viewWidget)

        self.ui.loadButton.clicked.connect(self.load_dicom_folder)
        self.ui.renderButton.clicked.connect(self.render_volume)

        self.ui.iso_slider.setMinimum(1)
        self.ui.iso_slider.setMaximum(255)
        self.ui.iso_slider.setValue(50)
        self.ui.iso_slider.valueChanged.connect(self.update_iso_value)

        # Assuming ambientSlider, diffuseSlider, specularSlider are your sliders
        self.set_slider_properties(self.ui.ambientSlider, self.ui.diffuseSlider, self.ui.specularSlider)


        # Set up VTK rendering
        self.renderer = vtk.vtkRenderer()
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)
        
        self.render_window_interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
        self.render_window = self.vtk_widget.GetRenderWindow()

        # Set the default rendering method to raycast rendering
        self.ui.rayCastRadio.setChecked(True)
        self.ui.realTimeCheck.setChecked(True)

        self.ui.ambientSlider.valueChanged.connect(self.update_ambient)
        self.ui.diffuseSlider.valueChanged.connect(self.update_diffuse)
        self.ui.specularSlider.valueChanged.connect(self.update_specular)
        
        # Show surface rendering widgets by default
        self.hide_surface_widgets()


    def show_surface_widgets(self):
        """
        Show the surface widgets.

        This function shows the ISO slider and the ISO value widgets on the UI.
        """
        self.ui.iso_slider.show()
        self.ui.isoValue.show()
        self.ui.frameRayCast.hide()
        

    def hide_surface_widgets(self):
        """
        Hides the surface widgets in the UI.

        This function hides the `iso_slider` and `isoValue` widgets in the UI.
        """
        self.ui.iso_slider.hide()
        self.ui.isoValue.hide()
        self.ui.frameRayCast.show()


    def set_slider_properties(self, ambient_slider, diffuse_slider, specular_slider):
        """
        Set limits and initial values for ambient, diffuse, and specular sliders.

        Parameters:
        - ambient_slider: Slider for ambient property.
        - diffuse_slider: Slider for diffuse property.
        - specular_slider: Slider for specular property.
        """
        # Set limits for sliders (adjust these limits based on your requirements)
        ambient_slider.setMinimum(0)
        ambient_slider.setMaximum(10)
        diffuse_slider.setMinimum(0)
        diffuse_slider.setMaximum(10)
        specular_slider.setMinimum(0)
        specular_slider.setMaximum(10)

        # Set initial values for sliders (convert float to int)
        ambient_slider.setValue(int(4))
        diffuse_slider.setValue(int(6))
        specular_slider.setValue(int(2))


    def resizeEvent(self, event):
        """
        Resize event handler for the MainWindow class.

        Args:
            event (QResizeEvent): The resize event object.

        """
        super(MainWindow, self).resizeEvent(event)
        self.vtk_widget.resize(self.ui.viewWidget.size())

###############################################################################################
#                                   Property Update Functions                                 #
###############################################################################################
        
    def update_color_property(self, slider, label, render_method):
        """
        Updates a rendering property based on the current value of the given slider.
        If the surface radio button is checked and the real-time checkbox is checked, calls the specified render_method.
        """
        property_value = slider.value() / 10.0  # Convert back to a float in the range [0.0, 1.0]
        label.setText(f"{label.text().split(':')[0]}: {property_value}")

        if self.ui.realTimeCheck.isChecked():
            if self.ui.rayCastRadio.isChecked():
                render_method()


    def update_ambient(self):
        self.update_color_property(self.ui.ambientSlider, self.ui.AmbientLabel, self.render_ray_casting)

    def update_diffuse(self):
        self.update_color_property(self.ui.diffuseSlider, self.ui.DiffuseLabel, self.render_ray_casting)

    def update_specular(self):
        self.update_color_property(self.ui.specularSlider, self.ui.SpecularLabel, self.render_ray_casting)


    def update_iso_value(self):
        """
        Updates the value of `iso_value` based on the current value of the `iso_slider` in the UI.
        Updates the text of the `isoValue` label in the UI to reflect the new `iso_value`.
        
        """
        self.iso_value = self.ui.iso_slider.value()
        self.ui.isoValue.setText(f"ISO Value: {self.iso_value}")

        if self.ui.surfaceRadio.isChecked() and self.ui.realTimeCheck.isChecked():
            self.render_iso_surface()

###############################################################################################
#                                  Loading & Rendering Functions                              #
###############################################################################################
            
    def load_dicom_folder(self):
        """
        Load DICOM series data from a selected folder and render it using VTK.

        Parameters:
            None

        Returns:
            None
        """
        # Clear previous rendering
        if self.actor:
            self.renderer.RemoveActor(self.actor)
        
        self.renderer.RemoveAllViewProps()
        # Open a folder dialog to select a DICOM series folder
        folder_dialog = QFileDialog.getExistingDirectory(self, "Select DICOM Series Folder")
        if folder_dialog:
            print("Selected DICOM folder:", folder_dialog)

            # Load DICOM series data using VTK
            self.reader = vtk.vtkDICOMImageReader()
            self.reader.SetDirectoryName(folder_dialog)
            self.reader.Update()
            
            self.mapper = vtk.vtkImageMapper()
            self.mapper.SetInputConnection(self.reader.GetOutputPort())

            self.actor = vtk.vtkActor2D()
            self.actor.SetMapper(self.mapper)

            self.renderer.AddActor(self.actor)
            self.render_volume()
            self.vtk_widget.resize(self.ui.viewWidget.size())


            # Reset camera and render
            self.renderer.ResetCamera()
            self.render_window.Render()
            
            
    def render_volume(self):
        """
        Renders the volume based on the selected rendering mode.
        """
        if self.reader:
            # Check if the surface rendering mode is selected
            if self.ui.surfaceRadio.isChecked():

                self.show_surface_widgets()
                # Render the volume using the iso-surface rendering method
                self.render_iso_surface()

            # Check if the ray casting rendering mode is selected
            elif self.ui.rayCastRadio.isChecked():

                self.hide_surface_widgets()
                # Render the volume using the ray casting rendering method
                self.render_ray_casting()



    def render_iso_surface(self):
        """
        Render the iso surface using the vtkMarchingCubes algorithm.

        This method creates a vtkMarchingCubes object and sets its input data to the output of the reader from the 
        `load_dicom_folder` method. It then sets the iso value to the current value of the iso slider.

        A vtkPolyDataMapper is created and its input connection is set to the output port of the marching cubes 
        object. An actor is created and its mapper is set to the surface mapper. The surface actor is added to the 
        renderer.

        The renderer is cleared of all view props, the surface actor is added, and the camera is reset. Finally, the 
        render window is updated.

        """
        if self.reader:
            # Get current camera settings
            camera = self.renderer.GetActiveCamera()
            position = camera.GetPosition()
            focal_point = camera.GetFocalPoint()

            # Perform marching cubes surface rendering
            marching_cubes = vtk.vtkMarchingCubes()
            marching_cubes.SetInputConnection(self.reader.GetOutputPort())
            marching_cubes.SetValue(0, self.iso_slider.value())

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(marching_cubes.GetOutputPort())

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)

            # Clear previous view props and add the surface actor to the renderer
            self.renderer.RemoveAllViewProps()
            self.renderer.AddActor(actor)

            # Reset the camera and render
            camera = self.renderer.GetActiveCamera()
            camera.SetPosition(position)
            camera.SetFocalPoint(focal_point)
            self.render_window.Render()

            
            
    def render_ray_casting(self):
        """
        Renders the scene using ray casting.
        
        It sets up the necessary volume properties such as color transfer function, 
        The function also sets the interpolation type to linear and enables shading with the specified ambient, diffuse, and specular values. 
        It creates a vtkVolume object with the ray casting mapper and volume property, 
        clears the previous view props, adds the volume actor to the renderer, resets the camera, and renders the scene.
        

        """
        if self.reader:
            # Get current camera settings
            camera = self.renderer.GetActiveCamera()
            position = camera.GetPosition()
            focal_point = camera.GetFocalPoint()

            # Perform ray casting rendering
            ray_casting_mapper = vtk.vtkGPUVolumeRayCastMapper()
            ray_casting_mapper.SetInputConnection(self.reader.GetOutputPort())
            
            volume_property = vtk.vtkVolumeProperty()
            
            # Set up color transfer function
            volume_property.SetColor(self.volume_color_transfer_function())
            
            # Set up scalar opacity transfer function
            volume_property.SetScalarOpacity(self.scalar_opacity_transfer_function())
            
            # Set up gradient opacity transfer function
            volume_property.SetGradientOpacity(self.gradient_opacity_transfer_function())
            
            volume_property.SetInterpolationTypeToLinear()
            volume_property.ShadeOn()

            ambient_val , diffuse_val , spec_val = self.ui.ambientSlider.value() , self.ui.diffuseSlider.value() , self.ui.specularSlider.value()
            volume_property.SetAmbient(ambient_val/10.0)
            volume_property.SetDiffuse(diffuse_val/10.0)
            volume_property.SetSpecular(spec_val/10.0)
            
            volume = vtk.vtkVolume()
            volume.SetMapper(ray_casting_mapper)
            volume.SetProperty(volume_property)

            # Clear previous view props and add the volume actor to the renderer
            self.renderer.RemoveAllViewProps()
            self.renderer.AddVolume(volume)
            
            # Reset the camera and render
            camera = self.renderer.GetActiveCamera()
            camera.SetPosition(position)
            camera.SetFocalPoint(focal_point)
            self.render_window.Render()


    def volume_color_transfer_function(self):
        """
        Set up color transfer function for the volume.
        """
        volume_color = vtk.vtkColorTransferFunction()
        
        # Setting a new overall color
        overall_color_scalar_value = 0  
        overall_color_rgb = [0.0, 0.0, 0.0]  # RGB values for the new color
        
        # adding the new overall color point
        volume_color.AddRGBPoint(overall_color_scalar_value, *overall_color_rgb)
        
        # color points 
        volume_color.AddRGBPoint(500, 1.0, 0.5, 0.3)
        volume_color.AddRGBPoint(1000, 1.0, 0.5, 0.3)
        volume_color.AddRGBPoint(1150, 1.0, 1.0, 0.9)
        
        return volume_color

    def scalar_opacity_transfer_function(self):
        """
        Set up scalar opacity transfer function for the volume.
        """
        volume_scalar_opacity = vtk.vtkPiecewiseFunction()
        volume_scalar_opacity.AddPoint(0, 0.00)
        volume_scalar_opacity.AddPoint(500, 1.0)
        volume_scalar_opacity.AddPoint(1000, 0.7)
        volume_scalar_opacity.AddPoint(1150, 0.03)
        return volume_scalar_opacity

    def gradient_opacity_transfer_function(self):
        """
        Set up gradient opacity transfer function for the volume.
        """
        volume_gradient_opacity = vtk.vtkPiecewiseFunction()
        volume_gradient_opacity.AddPoint(0, 0.0)
        volume_gradient_opacity.AddPoint(90, 0.5)
        volume_gradient_opacity.AddPoint(100, 1.0)
        return volume_gradient_opacity



def main():
    app = QtWidgets.QApplication([])
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
