"""3D Slicer scripted module entrypoint for TumorLens AI."""

from __future__ import annotations

try:
    import qt  # type: ignore
    import slicer  # type: ignore
    from slicer.ScriptedLoadableModule import (  # type: ignore
        ScriptedLoadableModule,
        ScriptedLoadableModuleLogic,
        ScriptedLoadableModuleTest,
        ScriptedLoadableModuleWidget,
    )
except ImportError:  # pragma: no cover - lets pure-Python tests import this file outside Slicer.
    qt = None
    slicer = None

    class ScriptedLoadableModule:  # type: ignore[no-redef]
        def __init__(self, parent=None):
            self.parent = parent

    class ScriptedLoadableModuleWidget:  # type: ignore[no-redef]
        def setup(self):
            pass

    class ScriptedLoadableModuleLogic:  # type: ignore[no-redef]
        pass

    class ScriptedLoadableModuleTest:  # type: ignore[no-redef]
        pass

try:
    from .TumorLensAILogic import TumorLensAILogic
except ImportError:  # pragma: no cover - supports Slicer loading as a loose scripted module.
    from TumorLensAILogic import TumorLensAILogic


class TumorLensAI(ScriptedLoadableModule):
    def __init__(self, parent=None):
        super().__init__(parent)
        if parent is not None:
            parent.title = "TumorLens AI"
            parent.categories = ["Segmentation"]
            parent.dependencies = []
            parent.contributors = ["Tarun"]
            parent.helpText = (
                "AI-assisted brain tumor MRI segmentation, 3D surface generation, "
                "and quantitative measurement for research and education workflows."
            )
            parent.acknowledgementText = "Built with 3D Slicer and MONAI Label."


class TumorLensAIWidget(ScriptedLoadableModuleWidget):
    """Clinical workflow panel for the TumorLens AI Slicer module."""

    def setup(self):
        super().setup()
        if qt is None:
            return

        self.logic = TumorLensAIWorkflowLogic()
        self.latestReport = None
        layout = self.layout

        self._applyStyle()
        layout.setSpacing(12)

        header = self._section("TumorLens AI", "AI segmentation, 3D surface generation, and quantitative review.")
        layout.addWidget(header)

        workflow = qt.QFrame()
        workflow.setObjectName("TumorLensPanel")
        workflowLayout = qt.QVBoxLayout(workflow)
        workflowLayout.setSpacing(10)

        self.workflowStatus = qt.QLabel("Ready to load a research MRI volume.")
        self.workflowStatus.setObjectName("TumorLensStatus")
        self.workflowStatus.setWordWrap(True)
        workflowLayout.addWidget(self.workflowStatus)

        self.volumeSelector = slicer.qMRMLNodeComboBox()
        self.volumeSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
        self.volumeSelector.selectNodeUponCreation = True
        self.volumeSelector.addEnabled = False
        self.volumeSelector.removeEnabled = False
        self.volumeSelector.noneEnabled = True
        self.volumeSelector.setMRMLScene(slicer.mrmlScene)
        self.volumeSelector.setToolTip("Input CT or MRI volume for MONAI Label segmentation.")
        workflowLayout.addLayout(self._formRow("Volume", self.volumeSelector))

        loadButton = self._button("Load scan", "secondary")
        loadButton.connect("clicked()", self._onLoadScan)
        workflowLayout.addWidget(loadButton)

        self.serverUrl = qt.QLineEdit("http://127.0.0.1:8000")
        self.serverUrl.setToolTip("MONAI Label server endpoint.")
        connectButton = self._button("Connect MONAI Label", "secondary")
        connectButton.connect("clicked()", self._onConnectServer)

        serverRow = qt.QHBoxLayout()
        serverRow.addWidget(self.serverUrl, 1)
        serverRow.addWidget(connectButton)
        workflowLayout.addLayout(self._formRow("Server", serverRow))

        self.modelSelector = qt.QComboBox()
        self.modelSelector.addItems(["deepedit", "segresnet", "brats_mri_segmentation"])
        workflowLayout.addLayout(self._formRow("Model", self.modelSelector))

        self.simulateCheckBox = qt.QCheckBox("Use simulated segmentation when MONAI is unavailable")
        self.simulateCheckBox.checked = True
        workflowLayout.addWidget(self.simulateCheckBox)

        runButton = self._button("Run AI segmentation", "primary")
        runButton.connect("clicked()", self._onRunSegmentation)
        workflowLayout.addWidget(runButton)

        layout.addWidget(workflow)

        review = qt.QFrame()
        review.setObjectName("TumorLensPanel")
        reviewLayout = qt.QVBoxLayout(review)
        reviewLayout.setSpacing(10)
        reviewLayout.addWidget(self._panelTitle("Review 2D/3D Segmentation"))

        self.segmentationSelector = slicer.qMRMLNodeComboBox()
        self.segmentationSelector.nodeTypes = ["vtkMRMLSegmentationNode"]
        self.segmentationSelector.selectNodeUponCreation = True
        self.segmentationSelector.addEnabled = False
        self.segmentationSelector.removeEnabled = False
        self.segmentationSelector.noneEnabled = True
        self.segmentationSelector.setMRMLScene(slicer.mrmlScene)
        reviewLayout.addLayout(self._formRow("Segmentation", self.segmentationSelector))

        self.opacitySlider = qt.QSlider(qt.Qt.Horizontal)
        self.opacitySlider.minimum = 0
        self.opacitySlider.maximum = 100
        self.opacitySlider.value = 68
        self.opacitySlider.connect("valueChanged(int)", self._onOpacityChanged)
        reviewLayout.addLayout(self._formRow("Overlay opacity", self.opacitySlider))

        surfaceButton = self._button("Create closed-surface 3D model", "secondary")
        surfaceButton.connect("clicked()", self._onCreateSurface)
        reviewLayout.addWidget(surfaceButton)

        layout.addWidget(review)

        measurements = qt.QFrame()
        measurements.setObjectName("TumorLensPanel")
        measurementsLayout = qt.QVBoxLayout(measurements)
        measurementsLayout.setSpacing(10)
        measurementsLayout.addWidget(self._panelTitle("Measurements"))

        self.metricLabels = {
            "tumorVolumeCm3": qt.QLabel("-- cm^3"),
            "voxelCount": qt.QLabel("-- voxels"),
            "surfaceAreaMm2": qt.QLabel("-- mm^2"),
            "boundingBoxMm": qt.QLabel("-- mm"),
            "centerOfMassMm": qt.QLabel("-- mm"),
        }
        for name, label in self.metricLabels.items():
            label.setObjectName("TumorLensMetric")
            measurementsLayout.addLayout(self._metricRow(name, label))

        metricsButton = self._button("Compute tumor metrics", "secondary")
        metricsButton.connect("clicked()", self._onComputeMetrics)
        measurementsLayout.addWidget(metricsButton)

        exportRow = qt.QHBoxLayout()
        exportJson = self._button("Export JSON", "ghost")
        exportCsv = self._button("Export CSV", "ghost")
        exportJson.connect("clicked()", lambda: self._onExportReport("json"))
        exportCsv.connect("clicked()", lambda: self._onExportReport("csv"))
        exportRow.addWidget(exportJson)
        exportRow.addWidget(exportCsv)
        measurementsLayout.addLayout(exportRow)

        layout.addWidget(measurements)

        disclaimer = qt.QLabel("Research and education demo only. Not for clinical diagnosis or treatment decisions.")
        disclaimer.setObjectName("TumorLensDisclaimer")
        disclaimer.setWordWrap(True)
        layout.addWidget(disclaimer)
        layout.addStretch(1)

    def _applyStyle(self):
        style = """
            #TumorLensPanel {
              background-color: #14181e;
              border: 1px solid rgba(255, 255, 255, 0.12);
              border-radius: 14px;
            }
            #TumorLensHeader {
              color: #f5f5f7;
              font-size: 18px;
              font-weight: 700;
            }
            #TumorLensSubheader, #TumorLensStatus, #TumorLensDisclaimer {
              color: #a8b0ba;
              font-size: 12px;
            }
            #TumorLensPanelTitle {
              color: #f5f5f7;
              font-size: 14px;
              font-weight: 700;
            }
            #TumorLensMetric {
              color: #f5f5f7;
              font-weight: 700;
            }
            QPushButton {
              border-radius: 10px;
              min-height: 30px;
              padding-left: 12px;
              padding-right: 12px;
            }
            QPushButton[variant="primary"] {
              background-color: #64d2ff;
              color: #050608;
              font-weight: 700;
            }
            QPushButton[variant="secondary"] {
              background-color: rgba(48, 209, 88, 0.14);
              border: 1px solid rgba(48, 209, 88, 0.34);
              color: #d8ffe2;
            }
            QPushButton[variant="ghost"] {
              background-color: rgba(255, 255, 255, 0.06);
              border: 1px solid rgba(255, 255, 255, 0.12);
              color: #f5f5f7;
            }
            """
        parent = self.parent() if callable(getattr(self, "parent", None)) else getattr(self, "parent", None)
        if parent is not None and hasattr(parent, "setStyleSheet"):
            parent.setStyleSheet(style)

    def _section(self, title: str, subtitle: str):
        section = qt.QFrame()
        sectionLayout = qt.QVBoxLayout(section)
        sectionLayout.setContentsMargins(0, 0, 0, 0)
        sectionLayout.setSpacing(4)
        titleLabel = qt.QLabel(title)
        titleLabel.setObjectName("TumorLensHeader")
        subtitleLabel = qt.QLabel(subtitle)
        subtitleLabel.setObjectName("TumorLensSubheader")
        subtitleLabel.setWordWrap(True)
        sectionLayout.addWidget(titleLabel)
        sectionLayout.addWidget(subtitleLabel)
        return section

    def _panelTitle(self, text: str):
        label = qt.QLabel(text)
        label.setObjectName("TumorLensPanelTitle")
        return label

    def _formRow(self, label: str, control):
        row = qt.QVBoxLayout()
        labelWidget = qt.QLabel(label)
        labelWidget.setObjectName("TumorLensSubheader")
        row.addWidget(labelWidget)
        if isinstance(control, qt.QLayout):
            row.addLayout(control)
        else:
            row.addWidget(control)
        return row

    def _metricRow(self, label: str, value):
        row = qt.QHBoxLayout()
        name = qt.QLabel(self._metricLabel(label))
        name.setObjectName("TumorLensSubheader")
        row.addWidget(name)
        row.addStretch(1)
        row.addWidget(value)
        return row

    def _button(self, label: str, variant: str):
        button = qt.QPushButton(label)
        button.setProperty("variant", variant)
        return button

    def _metricLabel(self, key: str) -> str:
        labels = {
            "tumorVolumeCm3": "Tumor volume",
            "voxelCount": "Voxel count",
            "surfaceAreaMm2": "Surface area",
            "boundingBoxMm": "Bounding box",
            "centerOfMassMm": "Center of mass",
        }
        return labels.get(key, key)

    def _setStatus(self, message: str):
        self.workflowStatus.setText(message)

    def _currentVolume(self):
        return self.volumeSelector.currentNode()

    def _currentSegmentation(self):
        return self.segmentationSelector.currentNode()

    def _onLoadScan(self):
        slicer.util.openAddDataDialog()
        self._setStatus("Choose a CT or MRI volume, then select it in the Volume field.")

    def _onConnectServer(self):
        status = self.logic.connectMonaiServer(self.serverUrl.text)
        if status.reachable:
            models = ", ".join(status.models) if status.models else "no models listed"
            self._setStatus(f"Connected to MONAI Label. Available models: {models}.")
        else:
            self._setStatus(f"MONAI Label is not reachable: {status.message}")

    def _onRunSegmentation(self):
        volume = self._currentVolume()
        if volume is None:
            self._setStatus("Select a volume before running segmentation.")
            return

        try:
            if self.simulateCheckBox.checked:
                segmentation = self.logic.simulateSegmentation(volume)
            else:
                segmentation = self.logic.runSegmentation(volume, self.modelSelector.currentText)
            self.segmentationSelector.setCurrentNode(segmentation)
            self._setStatus("Segmentation imported. Review 2D overlays and create the 3D closed surface.")
        except Exception as exc:  # noqa: BLE001 - surfaced in the Slicer panel for interactive workflows.
            self._setStatus(f"Segmentation failed: {exc}")

    def _onOpacityChanged(self, value: int):
        segmentation = self._currentSegmentation()
        if segmentation is None:
            return
        displayNode = segmentation.GetDisplayNode()
        if displayNode is not None:
            displayNode.SetOpacity(value / 100.0)

    def _onCreateSurface(self):
        segmentation = self._currentSegmentation()
        if segmentation is None:
            self._setStatus("Select a segmentation before creating a closed surface.")
            return
        try:
            self.logic.createClosedSurface(segmentation)
            self._setStatus("Closed-surface model exported to the TumorLensAI Models folder.")
        except Exception as exc:  # noqa: BLE001
            self._setStatus(f"Closed-surface export failed: {exc}")

    def _onComputeMetrics(self):
        volume = self._currentVolume()
        segmentation = self._currentSegmentation()
        if volume is None or segmentation is None:
            self._setStatus("Select both a volume and a segmentation before computing metrics.")
            return
        try:
            self.latestReport = self.logic.computeTumorMetrics(volume, segmentation)
            payload = self.latestReport.to_dict()
            self.metricLabels["tumorVolumeCm3"].setText(f"{payload['tumorVolumeCm3']} cm^3")
            self.metricLabels["voxelCount"].setText(f"{payload['voxelCount']} voxels")
            self.metricLabels["surfaceAreaMm2"].setText(f"{payload['surfaceAreaMm2']} mm^2")
            self.metricLabels["boundingBoxMm"].setText(f"{payload['boundingBoxMm']} mm")
            self.metricLabels["centerOfMassMm"].setText(f"{payload['centerOfMassMm']} mm")
            self._setStatus("Tumor metrics computed and ready to export.")
        except Exception as exc:  # noqa: BLE001
            self._setStatus(f"Metric computation failed: {exc}")

    def _onExportReport(self, extension: str):
        if self.latestReport is None:
            self._onComputeMetrics()
        if self.latestReport is None:
            return

        path = qt.QFileDialog.getSaveFileName(
            None,
            "Export TumorLens AI report",
            f"TumorLensAI-report.{extension}",
            f"{extension.upper()} (*.{extension})",
        )
        if isinstance(path, tuple):
            path = path[0]
        if not path:
            return
        try:
            self.logic.exportReport(self.latestReport, path)
            self._setStatus(f"Report exported to {path}.")
        except Exception as exc:  # noqa: BLE001
            self._setStatus(f"Report export failed: {exc}")


class TumorLensAIWorkflowLogic(ScriptedLoadableModuleLogic, TumorLensAILogic):
    def __init__(self):
        TumorLensAILogic.__init__(self)


class TumorLensAITest(ScriptedLoadableModuleTest):
    def runTest(self):
        self.test_import_logic()

    def test_import_logic(self):
        logic = TumorLensAIWorkflowLogic()
        assert logic is not None
