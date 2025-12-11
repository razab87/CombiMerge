#!/usr/bin/env python3
# -*- coding: utf-8 -*-


#python code for the gimp 3.0 plugin CombiMerge; plugin version 1.0; see the readme or the github page for more information
#
#
#by razab



import os
import sys
import re

import gi
gi.require_version('Gimp', '3.0')
gi.require_version("Gtk", "3.0")
gi.require_version('GimpUi', '3.0')
from gi.repository import Gimp, GimpUi, GLib, Gio, GObject, Gtk


# --------------------- PART I: UI definitions --------------------- 

#define a dialog UI
class UserDialog(Gtk.Dialog):
    def __init__(self, plugin_instance):
        super().__init__(title="CombiMerge Options")

        self.plugin = plugin_instance
        self.progress_info_displayed = False
        self.connect("delete-event", self.on_close_dialog_clicked)

        self.set_default_size(300, 100)
        box = self.get_content_area()
 
        #OK- and CANCEL-buttons
        self.add_buttons("_OK", Gtk.ResponseType.OK, "_Cancel", Gtk.ResponseType.CANCEL)
        self.ok_button = self.get_widget_for_response(Gtk.ResponseType.OK)
        self.ok_button.set_sensitive(False) #grey out until a folder has been choosen       

        #the file chooser
        self.label_folder = Gtk.Label(label="Choose output directory:")
        self.label_folder.set_margin_top(10)
        self.label_folder.set_margin_start(5)
        self.label_folder.set_halign(Gtk.Align.START)
        box.add(self.label_folder)
        self.file_chooser = Gtk.FileChooserButton(title="Select Folder", action=Gtk.FileChooserAction.SELECT_FOLDER)
        self.file_chooser.set_margin_start(5)
        self.file_chooser.set_margin_end(5)
        self.file_chooser.connect("file-set", self.on_file_clicked)
        box.add(self.file_chooser)

        #combo box for image format
        self.label_format = Gtk.Label(label="Choose image format:")
        self.label_format.set_margin_top(10)
        self.label_format.set_margin_start(5)
        self.label_format.set_halign(Gtk.Align.START)
        box.add(self.label_format)
        self.img_formats = Gtk.ComboBoxText()
        self.img_formats.set_margin_start(5)
        self.img_formats.set_margin_end(5)
        format_list = ["bmp", "heic", "jpeg", "jpg", "jxl", "png", "tga", "webp"] #supported image formats
        for f in format_list:
            self.img_formats.append_text(f)
        self.img_formats.set_active(5)  #default is png
        box.add(self.img_formats)  
      
        # info showing the total number of images to be created
        self.label_info = Gtk.Label(label="Total number of resulting images: " + str(self.plugin.number_of_results))
        self.label_info.set_halign(Gtk.Align.START)
        self.label_info.set_margin_top(20)
        self.label_info.set_margin_start(5)

        box.add(self.label_info)

        #box.add(self.label_info)        

        self.show_all()

    def on_file_clicked(self, file_chooser):
        self.ok_button.set_sensitive(True) #OK-button only available after directory is chosen

    #convert the dialog so that it shows progress of the task (hack, because GIMP does not easily allow python/GTK-multithreading)
    def change_to_progress_dialog(self):
        self.set_title("CombiMerge Progress")

        ok_button = self.get_widget_for_response(Gtk.ResponseType.OK)
        cancel_button = self.get_widget_for_response(Gtk.ResponseType.CANCEL)
        self.action_area.remove(ok_button)
        self.action_area.remove(cancel_button)

        content_area = self.get_content_area()
        content_area.remove(self.file_chooser)
        content_area.remove(self.label_folder)
        content_area.remove(self.label_format)
        content_area.remove(self.img_formats)
        content_area.remove(self.label_info)

        self.label_progress = Gtk.Label(label="Finished: 0%")
        self.label_progress.set_margin_top(10)
        self.label_progress.set_margin_start(5)
        self.label_progress.set_halign(Gtk.Align.START)
        content_area.add(self.label_progress)     

        self.label_work = Gtk.Label(label="Working")
        self.label_work.set_margin_top(10)
        self.label_work.set_margin_start(5)
        self.label_work.set_halign(Gtk.Align.START)
        content_area.add(self.label_work)
        self.dots = 0
 
        self.label_info = Gtk.Label(label="Total number of resulting images: " + str(self.plugin.number_of_results))
        self.label_info.set_margin_top(20)
        self.label_info.set_margin_start(5)
        self.label_info.set_halign(Gtk.Align.START)
        content_area.add(self.label_info)

        self.cancel_button = Gtk.Button(label="Cancel Process")
        self.action_area.add(self.cancel_button)
        self.cancel_button.connect("clicked", self.on_cancel_button_clicked)   

        self.progress_info_displayed = True
 
        self.show_all()
        self.plugin.refresh_ui()

    #update the progress dialog
    def update_progress(self, percentage):
        self.label_progress.set_text("Finished: " + str(round(percentage)) + "%")

        self.dots = (self.dots + 1) % 4 
        work_dots = ""
        i = 0
        while i < self.dots:
            work_dots = work_dots + "." 
            i = i+1
        self.label_work.set_text("Working " + work_dots)  
               
        self.show_all()
        self.plugin.refresh_ui()

    def on_close_dialog_clicked(self, widget, event):
        if self.progress_info_displayed:
            confirm = ConfirmDialog() #warn that closing progress window cancels the process
            response = confirm.run()
            if response == Gtk.ResponseType.OK:
                self.plugin.process_cancelled = True 
                confirm.destroy()            
                return False
            else: 
                confirm.destroy()
                return True
        else:
            return False

    def on_cancel_button_clicked(self, button):
        self.plugin.process_cancelled = True 



#error notification, shows up if there is something wrong with the layer-group structure or the output directory
class ErrorDialog(Gtk.Dialog):
    def __init__(self, error_message):
        super().__init__(title="CombiMerge ERROR")

        self.set_default_size(300, 100)
        box = self.get_content_area()
 
        #OK-button
        self.add_buttons("_OK", Gtk.ResponseType.OK)
        self.ok_button = self.get_widget_for_response(Gtk.ResponseType.OK)      

        label_err = Gtk.Label(label=error_message)
        label_err.set_halign(Gtk.Align.START)

        label_err.set_margin_top(10)
        label_err.set_margin_start(5)
        label_err.set_margin_end(5)
        box.add(label_err)

        self.show_all()


#confirm dialog, shows up if user closes the progress dialog
class ConfirmDialog(Gtk.Dialog):
    def __init__(self):
        super().__init__(title="CombiMerge Warning")

        self.set_default_size(300, 100)
        box = self.get_content_area()
 
        #YES- and NO-buttons
        self.add_buttons("_Yes", Gtk.ResponseType.OK, "_No", Gtk.ResponseType.CANCEL)
        self.ok_button = self.get_widget_for_response(Gtk.ResponseType.OK)

        label_warn = Gtk.Label(label="Warning: This will cancel the process. Are you sure?")
        label_warn.set_margin_top(10)
        label_warn.set_margin_start(5)
        label_warn.set_margin_end(5)
        box.add(label_warn)

        self.show_all()   



# --------------------- PART II: main code --------------------- 


#main class defining the plugin
class CombiMerge(Gimp.PlugIn):
    def __init__(self):
        super().__init__()
        self.step = 0
        self.number_of_results = 0
        self.image = None
        self.groups = None
        self.output_path = None
        self.output_folder_name = "CombiMergeImgs"
        self.img_format = None
        self.process_cancelled = False
        self.layer_name_map = {}

    def do_query_procedures(self):
        return [ "jb-plug-in-combi-merge" ]

    def do_set_i18n (self, name):
        return False

    def do_create_procedure(self, name):
        procedure = Gimp.ImageProcedure.new(self, name, Gimp.PDBProcType.PLUGIN, self.run, None)

        procedure.set_image_types("*")
        procedure.set_menu_label("CombiMerge")
        procedure.add_menu_path('<Image>/Filters/')

        return procedure

    #show error
    def throw_error(self, error_message):
        Gimp.message("CombiMerge_ERROR: " + error_message)
        print("CombiMerge_ERROR: " + error_message)
        error_dialog = ErrorDialog(error_message)
        error_dialog.run()
        error_dialog.destroy()        

    #force ui to update and show new ui elements (hack, because GIMP does not easily allow python/GTK-multithreading)
    def refresh_ui(self):
        while Gtk.events_pending(): 
            Gtk.main_iteration_do(False)

    #in case layer names conatain unusual symbols ("<",">", ...), delete them to avoid os-specific problems with file naming
    def repair_layer_name(self, old_name):
        forbidden_symbols = r'[<>:"/\\|?*\n\r\t]'
        if re.search(forbidden_symbols, old_name) != None:
            tmp_name = re.sub(forbidden_symbols, '', old_name)
            new_name = tmp_name
            n = 1
            my_set = set()
            for key in self.layer_name_map:
                my_set.add(self.layer_name_map[key])
            while new_name in my_set:
                new_name = tmp_name + "_" + str(n)
                n = n+1
            return new_name
        return old_name

    #hide all image layers, unhide all group layers, check for correct layer-group-structure, repair layer names, compute number of resulting images
    #return value "True" if layer-group-structure is wrong, "False" otherwise
    def preprocess_session(self):
        num_of_images = 1
        image_found = False
        for group in self.groups:
            if group.is_group_layer():
                num_of_images = num_of_images * len(group.get_children())
                group.set_visible(True)
                layers = group.get_children()
                for layer in layers:
                    if not layer.is_group_layer():
                        image_found = True
                        layer.set_visible(False)
                        old_name = layer.get_name()
                        new_name = self.repair_layer_name(old_name) #remove unusual symbols ("<",">",...) from layer name if necessary
                        if old_name != new_name:
                            self.layer_name_map[old_name] = new_name #do not rename the layer (not mess up the user's gimp session), store them to use them later when exporting the image
                    else: 
                        error_message = "Some groups contain groups as elements! Avoid nested groups and try again."
                        self.throw_error(error_message)
                        return True
            else:
                error_message = "Some image layers are not part of a group! Make sure all layers are part of a group and try again."
                self.throw_error(error_message)
                return True
         
        if image_found: 
            self.number_of_results = num_of_images #number of resulting images
        else:
            self.number_of_results = 0

        return False


    #main function: choose a layer from each group, set it to visible and export the image; is done recursively for every
    #possible combination
    def generate_images(self, dialog, visible_layers, k):
        group = self.groups[k]

        if k == len(self.groups)-1: #recursion base: export the image
            layers = group.get_children()
            for layer in layers:
                layer.set_visible(True)    
                layer_name = layer.get_name()
                if layer_name in self.layer_name_map:
                    layer_name = self.layer_name_map[layer_name]              
                visible_layers.append(layer_name)
                
                self.refresh_ui()
                if self.process_cancelled: #when user cancels process
                    return 

                output_name = "_".join(visible_layers)
                file = Gio.File.new_for_path(os.path.join(self.output_path, output_name + "." + self.img_format))
                Gimp.file_save(Gimp.RunMode.NONINTERACTIVE, self.image, file, None) #export image from visible
                Gimp.progress_pulse()
                self.step = self.step + 1
 
                dialog.update_progress((self.step/self.number_of_results)*100) #update progress dialog

                layer.set_visible(False) 
                visible_layers.pop() #remove last list element
        else:
            layers = group.get_children()
            for layer in layers:

                if self.process_cancelled: #if "cancel process" pressed
                    return 

                layer.set_visible(True)
                layer_name = layer.get_name()
                if layer_name in self.layer_name_map:
                    layer_name = self.layer_name_map[layer_name]
                visible_layers.append(layer_name)

                self.generate_images(dialog, visible_layers, k+1) #recursive call

                layer.set_visible(False)
                visible_layers.pop() #remove last list element

    #run() function: is called when user starts CombiMerge
    def run(self, procedure, run_mode, image, drawables, config, run_data):
        print("\n\n ----- CombiMerge started ----- \n\n")
        Gimp.progress_init("CombiMerge started")
             
        #init some data
        self.process_cancelled = False
        self.step = 0      
        self.image = image
        self.groups = image.get_layers() 

        GimpUi.init("CombiMerge") #use GIMP ui style

        error_found = self.preprocess_session() #make session ready for the task, check for group-folder-structure errors
        if error_found:
           print("\n\n ----- CombiMerge end ----- \n\n")
           return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
       
        selected_path = None
        dialog = UserDialog(self) #create dialog UI (the user can enter some parameter)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.output_path = dialog.file_chooser.get_filename() 
            self.img_format = dialog.img_formats.get_active_text()
        else:
            dialog.destroy()
            print("\n\n ----- CombiMerge end ----- \n\n")
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())  

        if not os.access(self.output_path, os.W_OK): #if no write permission for chosen directory, throw error
            dialog.destroy()
            self.refresh_ui()  
            error_message = "No write permission for chosen directory. Choose one with write permission or change permission. Then try again."
            self.throw_error(error_message)
            print("\n\n ----- CombiMerge end ----- \n\n")
            return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())
       
        dialog.change_to_progress_dialog() #change dialog so that it shows progress of the task (hack, because GIMP does not easily allow python/GTK-multithreading)
                           
        path = os.path.join(self.output_path, self.output_folder_name) #path to the image outputs
        n = 1
        while os.path.isdir(path):
            path = os.path.join(self.output_path, self.output_folder_name + "(" + str(n) + ")")  #use a folder name which doesn't exist already
            n = n+1
        self.output_path = path
        os.mkdir(self.output_path) #create folder for image outputs        

        visible_layers = [] #will contain all layers which are temporarily visible
        self.generate_images(dialog, visible_layers, 0) #start the main process  

        dialog.destroy()
        print("\n\n ----- CombiMerge end ----- \n\n")
        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())




Gimp.main(CombiMerge.__gtype__, sys.argv)


