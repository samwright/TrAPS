all: traps calib

traps:
	pyuic4 src/traps/view/ui/main.ui > src/traps/view/main_ui.py
	pyuic4 src/traps/view/ui/variableForm.ui > src/traps/view/variableForm_ui.py
	pyuic4 src/traps/view/ui/variableWidget.ui > src/traps/view/variableWidget_ui.py
	pyuic4 src/traps/view/ui/graph.ui > src/traps/view/graph_ui.py
	pyuic4 src/traps/view/ui/hardware.ui > src/traps/view/hardware_ui.py

calib:
	pyuic4 src/calib/view/ui/calib.ui > src/calib/view/calib_ui.py